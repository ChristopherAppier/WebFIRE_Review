import os
import random
import time

import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


CONNECT_TIMEOUT = 10
SEARCH_READ_TIMEOUT = 60
DOWNLOAD_READ_TIMEOUT = 120
SEARCH_TIMEOUT = (CONNECT_TIMEOUT, SEARCH_READ_TIMEOUT)
DOWNLOAD_TIMEOUT = (CONNECT_TIMEOUT, DOWNLOAD_READ_TIMEOUT)
BOOTSTRAP_TIMEOUT = SEARCH_TIMEOUT

MAX_RETRIES = 5
RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_BACKOFF_BASE = 0.5
RETRY_BACKOFF_CAP = 8.0


class SearchError(Exception):
    """Raised when the report search fails after retries."""

    def __init__(self, reason_code, message):
        super().__init__(message)
        self.reason_code = reason_code


def _configure_adapter_retries(session):
    """Set shallow transport-level retries for transient HTTP failures."""
    retry_cfg = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.4,
        status_forcelist=sorted(RETRIABLE_STATUS_CODES),
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_cfg)
    session.mount("https://", adapter)
    session.mount("http://", adapter)


def _classify_exception(exc):
    """Map request exceptions to reason codes for retry decisions."""
    if isinstance(exc, requests.Timeout):
        return "timeout", str(exc)
    if isinstance(exc, requests.HTTPError):
        code = exc.response.status_code if exc.response is not None else None
        if code == 429:
            return "http_429", f"HTTP {code}: {exc}"
        if code is not None and 500 <= code < 600:
            return "http_5xx", f"HTTP {code}: {exc}"
        return "http_error", f"HTTP {code}: {exc}"
    if isinstance(exc, requests.RequestException):
        return "request_error", str(exc)
    return "unexpected_error", str(exc)


def _is_retriable_reason(reason):
    return reason in {"timeout", "http_429", "http_5xx", "request_error"}


def _backoff_seconds(attempt):
    raw = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
    jitter = random.uniform(0, RETRY_BACKOFF_BASE)
    return min(RETRY_BACKOFF_CAP, raw + jitter)


def _write_atomic_bytes(path, data):
    """Write bytes atomically to avoid partial cached files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".part")
    try:
        with open(tmp_path, "wb") as handle:
            handle.write(data)
        os.replace(tmp_path, path)
    except Exception:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
        raise


def _run_bootstrap_request(session, method, url, timeout, **kwargs):
    """Run a session bootstrap request with transient retry handling."""
    last_reason = "bootstrap_failed"
    last_error = "Unknown bootstrap error"
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            response = session.request(method, url, timeout=timeout, verify=False, **kwargs)
            response.raise_for_status()
            return response
        except Exception as exc:
            last_reason, last_error = _classify_exception(exc)
            if attempt <= MAX_RETRIES and _is_retriable_reason(last_reason):
                wait_for = _backoff_seconds(attempt)
                print(
                    f"build_session: retrying {method} {url} in {wait_for:.2f}s "
                    f"after {last_reason} (attempt {attempt}/{MAX_RETRIES + 1})."
                )
                time.sleep(wait_for)
                continue
            break
    raise SearchError(last_reason, f"Session bootstrap failed: {last_error}")

def build_session():
    """
    Establish a session with WebFIRE API.
    
    Returns:
        requests.Session: Ready-to-use session with headers initialized
    """
    s = requests.Session()
    _configure_adapter_retries(s)
    s.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Safari/605.1.15"
    )
    
    # Initialize session by visiting homepage
    _run_bootstrap_request(
        s,
        "GET",
        "https://cfpub.epa.gov/webfire/reports/esearch.cfm",
        timeout=BOOTSTRAP_TIMEOUT,
    )
    s.headers["Referer"] = "https://cfpub.epa.gov/webfire/reports/esearch.cfm"
    
    # Submit dummy search to initialize cookies
    _run_bootstrap_request(
        s,
        "POST",
        "https://cfpub.epa.gov/webfire/reports/esearch2.cfm",
        timeout=BOOTSTRAP_TIMEOUT,
        data={"reporttype": "All", "Submit": "Submit Search"},
    )
    s.headers["Referer"] = "https://cfpub.epa.gov/webfire/reports/esearch2.cfm"
    
    return s


def search_reports(session, start_date, end_date, state):
    """
    Search for reports in the date range.
    
    Args:
        session: requests.Session from build_session()
        start_date: MM/DD/YYYY start date string
        end_date: MM/DD/YYYY end date string
        state: State to search for
    
    Returns:
        List of dicts with report metadata including download link
    """
    payload = {
        "organization": "",
        "facility": "",
        "startdate": start_date,
        "enddate": end_date,
        "state": state,
        "county": "",
        "city": "",
        "zip": "",
        "CFRpart": "All",
        "CFRSubpart": "",
        "FRS": "",
        "Submit": "Submit Search",
    }

    last_reason = "search_failed"
    last_error = "Unknown search error"
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            response = session.post(
                "https://cfpub.epa.gov/webfire/reports/eSearchResults.cfm",
                data=payload,
                timeout=SEARCH_TIMEOUT,
                verify=False,
            )
            response.raise_for_status()
            return parse_search_results(response.text)
        except Exception as exc:
            last_reason, last_error = _classify_exception(exc)
            if attempt <= MAX_RETRIES and _is_retriable_reason(last_reason):
                wait_for = _backoff_seconds(attempt)
                print(
                    f"search_reports: state={state} retrying in {wait_for:.2f}s "
                    f"after {last_reason} (attempt {attempt}/{MAX_RETRIES + 1})."
                )
                time.sleep(wait_for)
                continue
            break

    raise SearchError(last_reason, f"Search failed for state {state}: {last_error}")


def parse_search_results(html):
    """
    Parse HTML search results into list of report dicts.
    
    Args:
        html: HTML response text from eSearchResults.cfm
    
    Returns:
        List of report metadata dicts
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="cell-border")
    except ImportError:
        return []
    
    if not table:
        print(f"parse_search_results: No table found in response. First 500 chars: {html[:500]}")
        return []
    
    reports = []
    for row in table.find_all("tr")[2:]:  # Skip header rows
        cells = row.find_all("td")
        if len(cells) < 11:
            continue
        
        link = cells[10].find("a", href=True)
        if not link or "ID=" not in link["href"]:
            continue
        
        doc_id = link["href"].split("ID=")[-1].strip()
        reports.append({
            "id": doc_id,
            "facility": cells[1].get_text(strip=True),
            "city": cells[2].get_text(strip=True),
            "state": cells[3].get_text(strip=True),
            "date": cells[5].get_text(strip=True),
            "report_type": cells[6].get_text(strip=True),
            "report_subtype": cells[7].get_text(strip=True),
            "pollutants": cells[8].get_text(strip=True),
            "filename": link.get("title", ""),
            "download_url": "https://cfpub.epa.gov/webfire/FIRE/view/dspERTDocumentDetails.cfm",
        })
    
    return reports


def download_report(session, doc_id, output_dir):
    """
    Download a single report from WebFIRE API.
    
    Args:
        session: requests.Session from build_session()
        doc_id: Report ID (e.g., "12345")
        output_dir: Path to save downloaded file
    
    Returns:
        tuple: (success: bool, filepath: Path|None, file_type: str|None, error: str|None)
    """
    result = download_report_with_details(session, doc_id, output_dir)
    return result["success"], result["filepath"], result["file_type"], result["error"]


def download_report_with_details(session, doc_id, output_dir):
    """Download one report with retries and return diagnostic metadata."""
    filepath = output_dir / f"{doc_id}.zip"

    if filepath.exists():
        return {
            "success": True,
            "filepath": filepath,
            "file_type": "already_cached",
            "error": None,
            "reason_code": "cached",
            "attempts": 1,
        }

    last_reason = "download_failed"
    last_error = "Unknown download error"
    last_attempt = 0
    for attempt in range(1, MAX_RETRIES + 2):
        last_attempt = attempt
        try:
            response = session.get(
                "https://cfpub.epa.gov/webfire/FIRE/view/dspERTDocumentDetails.cfm",
                params={"ID": doc_id},
                timeout=DOWNLOAD_TIMEOUT,
                verify=False,
            )
            response.raise_for_status()

            content = response.content
            if content[:2] == b"PK":
                _write_atomic_bytes(filepath, content)
                return {
                    "success": True,
                    "filepath": filepath,
                    "file_type": "zip",
                    "error": None,
                    "reason_code": "success",
                    "attempts": attempt,
                }

            if content[:5] == b"%PDF-":
                _write_atomic_bytes(filepath, content)
                return {
                    "success": True,
                    "filepath": filepath,
                    "file_type": "pdf",
                    "error": None,
                    "reason_code": "success",
                    "attempts": attempt,
                }

            last_reason = "unexpected_content"
            last_error = (
                "Unexpected response content. "
                f"Content-Type={response.headers.get('Content-Type', 'unknown')}"
            )
        except Exception as exc:
            last_reason, last_error = _classify_exception(exc)

        if attempt <= MAX_RETRIES and _is_retriable_reason(last_reason):
            wait_for = _backoff_seconds(attempt)
            print(
                f"download_report: doc_id={doc_id} retrying in {wait_for:.2f}s "
                f"after {last_reason} (attempt {attempt}/{MAX_RETRIES + 1})."
            )
            time.sleep(wait_for)
            continue
        break

    return {
        "success": False,
        "filepath": None,
        "file_type": None,
        "error": last_error,
        "reason_code": last_reason,
        "attempts": last_attempt,
    }
def fetch_all_reports(start_date, end_date, state, project_root):
    """
    Main entry point: fetch all reports for date range.
    Args:
            start_date: MM/DD/YYYY start date string
            end_date: MM/DD/YYYY end date string
            state: State name to search for
            project_root: Project root path used to locate data/raw
    """
    session = None

    try:
        session = build_session()
        download_path = project_root / "data" / "raw"
        output_dir = Path(download_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Search for reports in date range
        try:
            reports = search_reports(session, start_date, end_date, state)
        except SearchError as search_exc:
            print(
                f"Search failed for state={state} after retries: {search_exc.reason_code} - {search_exc}"
            )
            return {
                'success': False,
                'downloaded_count': 0,
                'errors': {'_search': str(search_exc)},
                'reports': []
            }

        if not reports:
            return {
                'success': True,
                'downloaded_count': 0,
                'errors': {},
                'reports': []
            }

        # Step 2: Download each report
        results = []
        errors = {}

        for i, report in enumerate(reports, 1):
            download_result = download_report_with_details(session, report['id'], output_dir)
            success = download_result['success']
            filepath = download_result['filepath']
            file_type = download_result['file_type']
            error_message = download_result['error']
            reason_code = download_result['reason_code']
            attempts = download_result['attempts']
            
            result = {
                'id': report['id'],
                'facility': report['facility'],
                'city': report['city'],
                'state': report['state'],
                'date': report['date'],
                'success': success,
                'file_path': str(filepath) if filepath else None,
                'pad_file_type': file_type,
                'reason_code': reason_code,
                'attempts': attempts,
                'error': error_message,
            }
            results.append(result)

            if success:
                print(
                    f"[{i}/{len(reports)}] Downloaded {report['id']} in {attempts} attempt(s): {filepath}"
                )
            else:
                errors[report['id']] = error_message
                print(
                    f"[{i}/{len(reports)}] Failed to download {report['id']} "
                    f"after {attempts} attempt(s) [{reason_code}]: {error_message}"
                )

        return {
            'success': len(errors) == 0,
            'downloaded_count': sum(1 for r in results if r['success']),
            'errors': errors,
            'reports': results,
        }
    
    finally:
        if session is not None:
            session.close()
