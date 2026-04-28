import requests
from pathlib import Path

def build_session():
    """
    Establish a session with WebFIRE API.
    
    Returns:
        requests.Session: Ready-to-use session with headers initialized
    """
    s = requests.Session()
    s.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Safari/605.1.15"
    )
    
    # Initialize session by visiting homepage
    s.get("https://cfpub.epa.gov/webfire/reports/esearch.cfm", timeout=30, verify=False)
    s.headers["Referer"] = "https://cfpub.epa.gov/webfire/reports/esearch.cfm"
    
    # Submit dummy search to initialize cookies
    s.post(
        "https://cfpub.epa.gov/webfire/reports/esearch2.cfm",
        data={"reporttype": "All", "Submit": "Submit Search"},
        timeout=60,
        verify=False
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
        "facility": "jayhawk",
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
    
    r = session.post(
        "https://cfpub.epa.gov/webfire/reports/eSearchResults.cfm",
        data=payload,
        timeout=60,
        verify=False
    )
    r.raise_for_status()
    
    return parse_search_results(r.text)


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
        tuple: (success: bool, filepath: Path|None, file_type: str)
    """
    filepath = output_dir / f"{doc_id}.zip"
    
    if filepath.exists():
        return True, filepath, "already_cached"
    
    try:
        r = session.get(
            "https://cfpub.epa.gov/webfire/FIRE/view/dspERTDocumentDetails.cfm",
            params={"ID": doc_id},
            timeout=120,
            verify=False
        )
        r.raise_for_status()
        
        # Check if response is valid ZIP
        if not r.content[:2] == b"PK":
            # Check if it's a PDF instead
            if r.content[:4] == b"%PDF":
                filepath.write_bytes(r.content)
                file_type = "pdf"
                return True, filepath, file_type
            
            # Unknown format
            return False, None, f"Unexpected content type: {r.headers.get('Content-Type', 'unknown')}"
        
        filepath.write_bytes(r.content)
        return True, filepath, "zip"
        
    except Exception as e:
        return False, None, str(e)
    
    
def fetch_all_reports(start_date, end_date, state):
    """
    Main entry point: fetch all reports for date range.
    Args:
        session: requests.Session from build_session()
        end_date: MM/DD/YYYY end date string
        end_date: MM/DD/YYYY end date string
        output_dir: Path to save downloaded reports
    """
    session = build_session()
    
    
    project_root = Path(__file__).parent.parent.parent # Finds the root folder of the project
    download_path = project_root / "data" / "raw"
    
    output_dir = Path(download_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Search for reports in date range
    reports = search_reports(session, start_date, end_date, state)
    
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
        success, filepath, file_type = download_report(session, report['id'], output_dir)
        
        result = {
            'id': report['id'],
            'facility': report['facility'],
            'city': report['city'],
            'state': report['state'],
            'date': report['date'],
            'success': success,
            'file_path': str(filepath),
            'pad_file_type': file_type, # Wait, I'm seeing a phantom "pad_file_type" ... no, let me check m0002 again.
            'error': file_type if not success else None,
        }
        results.append(result)
        
        if success:
            print(f"[{i}/{len(reports)}] Downloaded {report['id']}: {filepath}")
        else:
            errors[report['id']] = file_type
            print(f"[{i}/{len(reports)}] Failed to download {report['id']}: {file_type}")
    
    return {
        'success': len(errors) == 0,
        'downloaded_count': sum(1 for r in results if r['success']),
        'errors': errors,
        'reports': results,
    }