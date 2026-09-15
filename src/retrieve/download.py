import csv
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from retrieve.time import check_timer

logger = logging.getLogger(__name__)


def fetch_reports(config, paths):
    """Fetches reports from the WebFIRE HTTP for each state specified in the configuration.

    Args:
            config (dict): A dictionary containing configuration settings.
            paths (dict): A dictionary containing paths to various data directories.
    """

    # Get the base url and start/end dates for the WebFIRE HTTP request from settings
    webfire_base = config["http_endpoints"]["webfire"]
    start_date, end_date = check_timer(config).values()

    # Start a session to maintain cookies and headers across requests
    logger.info(f"\n{'*' * 50}\n\nStarting session for WebFIRE HTTP requests")
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0"

    # Read the state names from the configuration file
    state_names = [state["name"] for state in config["states"]]
    dl_retries = int(config.get("download_retry_attempts"))
    dl_retry_delay = float(config.get("download_retry_delay_seconds"))
    dl_workers = max(1, int(config.get("download_workers", 4)))
    http_timeout = float(config.get("http_timeout_seconds", 30))

    try:
        # Loop through each state and perform the search and download process
        for state_name in state_names:
            # POST to the search results page with the specified parameters
            post_search(
                webfire_base,
                session,
                start_date,
                end_date,
                state_name,
                paths,
                timeout=http_timeout,
            )

            # Parse the search results page to extract the URLs of the reports and save as CSV
            parse_search_results(paths["http_dir"], state_name)

            # Request 4: GET the report pages for each URL in the parsed CSV and save to file
            get_results(
                session,
                paths["raw_data_dir"],
                paths["http_dir"],
                state_name,
                dl_retries,
                dl_retry_delay,
                dl_workers,
                http_timeout,
            )
    finally:
        session.close()

    # After all states have been processed, build a master report table combining all state CSVs
    build_master_report_table(paths["http_dir"])


def post_search(
    webfire_base, session, start_date, end_date, state_name, paths, timeout=30
):
    """Posts a search request to the WebFIRE HTTP for a specific state and date range.

    Args:
            webfire_base (str): The base URL for the WebFIRE HTTP.
            session (requests.Session): The session object for making HTTP requests.
            start_date (str): The start date for the search range.
            end_date (str): The end date for the search range.
            state_name (str): The name of the state for which reports are being searched.
            paths (dict): A dictionary containing paths to various data directories.
    """

    logger.info(
        f"\n{'*' * 50}\n\nSearching for reports for state: {state_name} from {start_date} to {end_date}"
    )

    try:
        # Request 1: GET the initial search page to establish session cookies
        response1 = session.get(f"{webfire_base}/reports/esearch.cfm", timeout=timeout)
        response1.raise_for_status()

        # Request 2: POST to the search page to submit the search form
        session.headers["Referer"] = f"{webfire_base}/reports/esearch.cfm"
        response2 = session.post(
            f"{webfire_base}/reports/esearch2.cfm",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"reporttype": "All", "Submit": "Submit Search"},
            timeout=timeout,
        )
        response2.raise_for_status()

        # Request 3: POST to the search results page with the specified parameters
        session.headers["Referer"] = f"{webfire_base}/reports/esearch2.cfm"
        response3 = session.post(
            f"{webfire_base}/reports/eSearchResults.cfm",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "organization": "",
                "facility": "",
                "startdate": start_date,
                "enddate": end_date,
                "state": state_name,
                "county": "",
                "city": "",
                "zip": "",
                "CFRpart": "All",
                "CFRSubpart": "",
                "FRS": "",
                "Submit": "Submit Search",
            },
            timeout=timeout,
        )
        response3.raise_for_status()
    except requests.exceptions.RequestException:
        logger.exception(
            "WebFIRE search request failed for state %s (%s to %s)",
            state_name,
            start_date,
            end_date,
        )
        raise

    # Save the response content to a file for further processing
    output_file_path = Path(paths["http_dir"]) / f"results_{state_name}.html"
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(response3.text)


def parse_search_results(file_path, state_name):
    """Parses the search results page for a specific state and extracts the report URLs.

    Args:
            file_path (Path): The path to the directory where the search results HTML file is stored.
            state_name (str): The name of the state for which reports are being parsed.
    """

    logger.info(f"\n\nParsing search results for state: {state_name}")

    # Create the path to the search results HTML file and read its content using BeautifulSoup
    state_file = file_path / f"results_{state_name}.html"

    with open(state_file, "r", encoding="utf-8") as html_file:
        soup = BeautifulSoup(html_file.read(), "html.parser")

    results_table = soup.select_one("#myDocTable")
    if results_table is None:
        raise ValueError(
            f"WebFIRE response for state {state_name} did not contain the expected results table"
        )

    # Define the fieldnames for the CSV file that will store the extracted report URLs
    fieldnames = [
        "Organization",
        "Facility",
        "City",
        "State",
        "County",
        "Submission Date",
        "Report Type",
        "Report Sub Type",
        "Pollutants",
        "Control Devices",
        "Document Name",
        "Related Attachment(s)",
        "report_url",
        "Downloaded Filename",
        "Document List",
        "Prompt Name",
    ]

    # Extract the relevant data from the search results table and store it in a list of dictionaries
    rows = []
    for tr in results_table.select("tbody tr"):
        tds = tr.find_all("td")
        if len(tds) < 12:
            continue

        link = tds[10].find("a")
        document_name = (link.get("title", "").strip() if link else "") or tds[
            10
        ].get_text(" ", strip=True)
        report_url = link.get("href", "").strip() if link else ""

        rows.append(
            {
                "Organization": tds[0].get_text(" ", strip=True),
                "Facility": tds[1].get_text(" ", strip=True),
                "City": tds[2].get_text(" ", strip=True),
                "State": tds[3].get_text(" ", strip=True),
                "County": tds[4].get_text(" ", strip=True),
                "Submission Date": tds[5].get_text(" ", strip=True),
                "Report Type": tds[6].get_text(" ", strip=True),
                "Report Sub Type": tds[7].get_text(" ", strip=True),
                "Pollutants": tds[8].get_text(" ", strip=True),
                "Control Devices": tds[9].get_text(" ", strip=True),
                "Document Name": document_name,
                "Related Attachment(s)": tds[11].get_text(" ", strip=True),
                "report_url": report_url,
                "Downloaded Filename": "",
                "Document List": "",
                "Prompt Name": "",
            }
        )

    output_csv = file_path / f"{state_name}_report_table.csv"
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Calculating the number of reports found and logging the result
    num_reports = len(rows)
    logger.info(f"\n\nFound {num_reports} reports for state: {state_name}")


def _download_report(
    row,
    idx,
    state_name,
    raw_data_dir,
    max_attempts,
    retry_delay_seconds,
    headers,
    cookies,
    reserved_names,
    filename_lock,
    request_timeout,
):
    report_url = row.get("report_url", "").strip()
    worker_session = requests.Session()
    worker_session.headers.update(headers)
    worker_session.cookies.update(cookies)

    response = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = worker_session.get(
                report_url, timeout=request_timeout, stream=True
            )
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as error:
            if response is not None:
                response.close()
                response = None
            if attempt == max_attempts:
                logger.error(
                    f"Failed after {max_attempts} attempts for {report_url}: {error}"
                )
            else:
                time.sleep(retry_delay_seconds)

    if response is None:
        worker_session.close()
        return False

    content_disposition = response.headers.get("Content-Disposition", "")
    filename = None
    if "filename=" in content_disposition:
        filename = content_disposition.split("filename=", 1)[1].strip().strip('"')
    if not filename:
        filename = f"{state_name}_report_{idx}.bin"
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", filename)

    with filename_lock:
        output_file_path = raw_data_dir / filename
        stem, suffix = output_file_path.stem, output_file_path.suffix
        number = 1
        while output_file_path.exists() or output_file_path.name in reserved_names:
            output_file_path = raw_data_dir / f"{stem}_{number}{suffix}"
            number += 1
        reserved_names.add(output_file_path.name)

    try:
        with open(output_file_path, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if chunk:
                    output_file.write(chunk)
    except Exception:
        output_file_path.unlink(missing_ok=True)
        logger.exception("Failed to save report %s", report_url)
        return False
    finally:
        response.close()
        worker_session.close()

    row["Downloaded Filename"] = output_file_path.name
    row["Document List"] = (
        "" if output_file_path.name.lower().endswith(".zip") else output_file_path.name
    )
    return True


def get_results(
    session,
    raw_data_dir,
    http_dir,
    state_name,
    max_attempts=3,
    retry_delay_seconds=2,
    max_workers=4,
    request_timeout=30,
):
    """
    GETs the report pages for each URL in the parsed CSV and saves them to files in the raw data directory.

    Args:
            session (requests.Session): The session object for making HTTP requests.
            raw_data_dir (Path): The directory where raw data files will be saved.
            http_dir (Path): The directory where HTTP-related files are stored.
            state_name (str): The name of the state for which reports are being downloaded.
            max_attempts (int): The maximum number of retry attempts for failed requests.
            retry_delay_seconds (int): The delay in seconds between retry attempts.
            max_workers (int): The maximum number of concurrent downloads.
            request_timeout (float): Timeout in seconds for each report request.
    """

    logger.info(f"\n\nDownloading reports for state: {state_name}\n")

    # Read the CSV file containing report URLs for the state
    csv_path = http_dir / f"{state_name}_report_table.csv"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    # If the CSV file does not exist, return early
    if not csv_path.exists():
        logger.warning("Report table not found for state %s: %s", state_name, csv_path)
        return

    # Loop through each report URL in the CSV and GET the report page, saving it to a file
    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    # Keep the original column order and append new columns if missing
    fieldnames = list(reader.fieldnames or [])
    if "Downloaded Filename" not in fieldnames:
        fieldnames.append("Downloaded Filename")
    if "Document List" not in fieldnames:
        fieldnames.append("Document List")
    if "Prompt Name" not in fieldnames:
        fieldnames.append("Prompt Name")

    # Finding the number of reports to download for progress tracking
    num_dl = 0
    jobs = []
    for idx, row in enumerate(rows, start=1):
        row.setdefault("Downloaded Filename", "")
        row.setdefault("Document List", "")
        row.setdefault("Prompt Name", "")
        if row.get("report_url", "").strip():
            jobs.append((idx, row))

    headers = dict(session.headers)
    cookies = session.cookies.get_dict()
    reserved_names = set()
    filename_lock = Lock()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _download_report,
                row,
                idx,
                state_name,
                raw_data_dir,
                max_attempts,
                retry_delay_seconds,
                headers,
                cookies,
                reserved_names,
                filename_lock,
                request_timeout,
            ): (idx, row)
            for idx, row in jobs
        }
        for future in tqdm(
            as_completed(futures), total=len(futures), desc=f"{state_name} reports"
        ):
            idx, row = futures[future]
            try:
                num_dl += int(future.result())
            except Exception:
                logger.exception(
                    "Unexpected download failure for state %s report %s (%s)",
                    state_name,
                    idx,
                    row.get("report_url", ""),
                )

    # Rewrite the CSV so downstream steps can map extracted docs back to the correct row
    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    num_reports = len(jobs)
    if num_dl == num_reports:
        logger.info("\nAll reports successfully downloaded")
    else:
        logger.warning(
            f"\nTotal reports downloaded: {num_dl} of {num_reports}. Some reports may have failed to download."
        )

    # Logging a separator line to indicate the end of the download process for the state
    logger.info(f"\n{'*' * 50}")


def build_master_report_table(http_dir):
    """
    Combines all per-state *_report_table.csv files into one master report_table.csv.

    Args:
        http_dir (Path): The directory where HTTP-related CSV files are stored.
    """
    state_tables = sorted(
        p for p in http_dir.glob("*_report_table.csv") if p.name != "report_table.csv"
    )

    if not state_tables:
        logger.warning("\nNo state report tables found to combine.")
        return

    master_rows = []
    master_fieldnames = []

    for table_path in state_tables:
        with open(table_path, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
            fieldnames = list(reader.fieldnames or [])

        for field in fieldnames:
            if field not in master_fieldnames:
                master_fieldnames.append(field)

        master_rows.extend(rows)

    master_path = http_dir / "report_table.csv"
    with open(master_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=master_fieldnames)
        writer.writeheader()
        writer.writerows(master_rows)

    logger.info("\nBuilding combined report table")


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    # Downloading reports from WebFIRE HTTP for each state
    fetch_reports(config, paths)
