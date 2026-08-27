import csv
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from document_retrieval.timer_manager import check_timer


def fetch_reports(config, paths):
	"""Fetches reports from the WebFIRE HTTP for each state specified in the configuration.
	
	Args:
		config (dict): A dictionary containing configuration settings.
		paths (dict): A dictionary containing paths to various data directories.
	"""

	# Get the base url and start/end dates for the WebFIRE HTTP request from settings
	webfire_base = config['http_endpoints']['webfire']
	start_date, end_date = check_timer(config).values()

	# Start a session to maintain cookies and headers across requests
	print(f"\n{'*' * 50}\n\nStarting session for WebFIRE HTTP requests")
	session = requests.Session()
	session.headers["User-Agent"] = "Mozilla/5.0"

	# Read the state names from the configuration file
	state_names = [state['name'] for state in config['states']]
	dl_retries = int(config.get('download_retry_attempts'))
	dl_retry_delay = float(config.get('download_retry_delay_seconds'))

	# Loop through each state and perform the search and download process
	for state_name in state_names:
		# POST to the search results page with the specified parameters
		post_search(webfire_base, session, start_date, end_date, state_name, paths)

		# Parse the search results page to extract the URLs of the reports and save as CSV
		parse_search_results(paths['http_dir'], state_name)

		# Request 4: GET the report pages for each URL in the parsed CSV and save to file
		get_results(session,paths['raw_data_dir'],paths['http_dir'],state_name,dl_retries,dl_retry_delay)

	# After all states have been processed, build a master report table combining all state CSVs
	build_master_report_table(paths['http_dir'])

def post_search(webfire_base, session, start_date, end_date, state_name, paths):
	"""Posts a search request to the WebFIRE HTTP for a specific state and date range.

	Args:
		webfire_base (str): The base URL for the WebFIRE HTTP.
		session (requests.Session): The session object for making HTTP requests.
		start_date (str): The start date for the search range.
		end_date (str): The end date for the search range.
		state_name (str): The name of the state for which reports are being searched.
		paths (dict): A dictionary containing paths to various data directories.
	"""

	print(f"\n{'*' * 50}\n\nSearching for reports for state: {state_name} from {start_date} to {end_date}")

	# Request 1: GET the initial search page to establish session cookies
	response1 = session.get(f"{webfire_base}/reports/esearch.cfm")  # noqa: F841

	#print("Request 1 status:", response1.status_code)

	# Request 2: POST to the search page to submit the search form
	session.headers["Referer"] = f"{webfire_base}/reports/esearch.cfm"
	response2 = session.post(  # noqa: F841
		f"{webfire_base}/reports/esearch2.cfm",
		headers={"Content-Type": "application/x-www-form-urlencoded"},
		data={"reporttype": "All", "Submit": "Submit Search"},
	)
	#print("Request 2 status:", response2.status_code)

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
	)

	#print("Request 3 status:", response3.status_code)
	#print(response3.text)

	# Save the response content to a file for further processing
	output_file_path = Path(paths['http_dir']) / f"results_{state_name}.html"
	with open(output_file_path, "w", encoding="utf-8") as output_file:
		output_file.write(response3.text)

def parse_search_results(file_path, state_name):
	"""Parses the search results page for a specific state and extracts the report URLs.
	
	Args:
		file_path (Path): The path to the directory where the search results HTML file is stored.
		state_name (str): The name of the state for which reports are being parsed.
	"""

	print(f"\n\nParsing search results for state: {state_name}")

	# Create the path to the search results HTML file and read its content using BeautifulSoup
	state_file = file_path / f"results_{state_name}.html"

	with open(state_file, "r", encoding="utf-8") as html_file:
		soup = BeautifulSoup(html_file.read(), "html.parser")

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
    ]

	# Extract the relevant data from the search results table and store it in a list of dictionaries
	rows = []
	for tr in soup.select("#myDocTable tbody tr"):
		tds = tr.find_all("td")
		if len(tds) < 12:
			continue

		link = tds[10].find("a")
		document_name = (link.get("title", "").strip() if link else "") or tds[10].get_text(" ", strip=True)
		report_url = link.get("href", "").strip() if link else ""

		rows.append({
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
        })

	output_csv = file_path / f"{state_name}_report_table.csv"
	with open(output_csv, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(rows)

	# Calculating the number of reports found and printing the result
	num_reports = len(rows)
	print(f"\n\nFound {num_reports} reports for state: {state_name}")

def get_results(session, raw_data_dir, http_dir, state_name, max_attempts=3, retry_delay_seconds=2):
	"""
	GETs the report pages for each URL in the parsed CSV and saves them to files in the raw data directory.

	Args:
		session (requests.Session): The session object for making HTTP requests.
		raw_data_dir (Path): The directory where raw data files will be saved.
		http_dir (Path): The directory where HTTP-related files are stored.
		state_name (str): The name of the state for which reports are being downloaded.
		max_attempts (int): The maximum number of retry attempts for failed requests.
		retry_delay_seconds (int): The delay in seconds between retry attempts.
	"""
	
	print(f"\n\nDownloading reports for state: {state_name}\n")
	
	# Read the CSV file containing report URLs for the state
	csv_path = http_dir / f"{state_name}_report_table.csv"
	raw_data_dir.mkdir(parents=True, exist_ok=True)

	# If the CSV file does not exist, return early
	if not csv_path.exists():
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

	# Finding the number of reports to download for progress tracking
	num_reports = len(rows)
	num_dl = 0

	for idx, row in enumerate(rows, start=1):
		row.setdefault("Downloaded Filename", "")
		row.setdefault("Document List", "")
		# Read the URL of the report from the CSV row
		report_url = row.get("report_url", "").strip()
		if not report_url:
			continue

		# GET the report with a simple retry loop
		response = None
		for attempt in range(1, max_attempts + 1):
			try:
				response = session.get(report_url, timeout=30, stream=True)
				response.raise_for_status()
				break
			except requests.exceptions.RequestException as e:
				if attempt == max_attempts:
					print(f"Failed after {max_attempts} attempts for {report_url}: {e}")
				else:
					print(f"Attempt {attempt}/{max_attempts} failed for {report_url}: {e}. Retrying...")
					time.sleep(retry_delay_seconds)

		if response is None:
			continue

		# Extract the filename from the Content-Disposition header or fallback to the last part of the URL
		content_disposition = response.headers.get("Content-Disposition", "")
		filename = None

		if "filename=" in content_disposition:
			filename = content_disposition.split("filename=", 1)[1].strip().strip('"')

		if not filename:
			filename = f"{state_name}_report_{idx}.bin"

		# Safety cleanup for filesystem-invalid characters
		filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", filename)

		output_file_path = raw_data_dir / filename
		if output_file_path.exists():
			stem, suffix = output_file_path.stem, output_file_path.suffix
			n = 1
			while output_file_path.exists():
				output_file_path = raw_data_dir / f"{stem}_{n}{suffix}"
				n += 1

		total_bytes = int(response.headers.get("Content-Length", 0))
		chunk_size = 64 * 1024

		# Save the report content to a file in the raw data directory
		with open(output_file_path, "wb") as output_file, tqdm(
			total=total_bytes if total_bytes > 0 else None,
			unit="B",
			unit_scale=True,
			unit_divisor=1024,
			desc=f"{state_name} report {idx}",
			leave=False,
		) as bar:
			for chunk in response.iter_content(chunk_size=chunk_size):
				if not chunk:
					continue
				output_file.write(chunk)
				bar.update(len(chunk))

		# Tracking the number of reports downloaded and printing progress
		num_dl += 1
		row["Downloaded Filename"] = output_file_path.name

		# For non-zip files, keep Document List populated with the downloaded filename.
		# Zip rows are left blank for the extract stage to replace with extracted names.
		if not output_file_path.name.lower().endswith(".zip"):
			row["Document List"] = output_file_path.name
		else:
			row["Document List"] = ""

		print(f"Downloaded report {idx} of {num_reports}")

	# Rewrite the CSV so downstream steps can map extracted docs back to the correct row
	with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(rows)

	if num_dl == num_reports:
		print("\nAll reports successfully downloaded")
	else:
		print(f"\nTotal reports downloaded: {num_dl} of {num_reports}. Some reports may have failed to download.")

	# Printing a separator line to indicate the end of the download process for the state
	print(f"\n{'*' * 50}")

def build_master_report_table(http_dir):
    """
    Combines all per-state *_report_table.csv files into one master report_table.csv.

    Args:
        http_dir (Path): The directory where HTTP-related CSV files are stored.
    """
    state_tables = sorted(
        p for p in http_dir.glob("*_report_table.csv")
        if p.name != "report_table.csv"
    )

    if not state_tables:
        print("\nNo state report tables found to combine.")
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

    print("\nBuilding combined report table")

if __name__ == "__main__":
	from common import utilities

    # Setting up logging and loading configuration options and paths from settings.yml
	config, paths = utilities.initialize_project()

	# Downloading reports from WebFIRE HTTP for each state
	fetch_reports(config, paths)