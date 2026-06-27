import requests
from timer_manager import check_timer
from pathlib import Path
from bs4 import BeautifulSoup
import csv
import re
import time

def fetch_reports(config, paths):
	"""Fetches reports from the WebFIRE API for each state specified in the configuration.
	
	Args:
		config (dict): A dictionary containing configuration settings.
		paths (dict): A dictionary containing paths to various data directories.
	"""

	# Get the base url and start/end dates for the WebFIRE API request from settings
	webfire_base = config['api_endpoints']['webfire']
	start_date, end_date = check_timer(config).values()

	# Start a session to maintain cookies and headers across requests
	print(f"\n\n{'*' * 50}\n\nStarting session for WebFIRE API requests")
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
		parse_search_results(paths['api_dir'], state_name)

		# Request 4: GET the report pages for each URL in the parsed CSV and save to file
		get_results(session,paths['raw_data_dir'],paths['api_dir'],state_name,dl_retries,dl_retry_delay)

def post_search(webfire_base, session, start_date, end_date, state_name, paths):
	"""Posts a search request to the WebFIRE API for a specific state and date range.

	Args:
		webfire_base (str): The base URL for the WebFIRE API.
		session (requests.Session): The session object for making HTTP requests.
		start_date (str): The start date for the search range.
		end_date (str): The end date for the search range.
		state_name (str): The name of the state for which reports are being searched.
		paths (dict): A dictionary containing paths to various data directories.
	"""

	print(f"\n\n{'*' * 50}\n\nSearching for reports for state: {state_name} from {start_date} to {end_date}")

	# Request 1: GET the initial search page to establish session cookies
	response1 = session.get(f"{webfire_base}/reports/esearch.cfm")

	#print("Request 1 status:", response1.status_code)

	# Request 2: POST to the search page to submit the search form
	session.headers["Referer"] = f"{webfire_base}/reports/esearch.cfm"
	response2 = session.post(
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
	output_file_path = Path(paths['api_dir']) / f"results_{state_name}.html"
	with open(output_file_path, "w", encoding="utf-8") as output_file:
		output_file.write(response3.text)

def parse_search_results(file_path, state_name):
	"""Parses the search results page for a specific state and extracts the report URLs.
	
	Args:
		file_path (Path): The path to the directory where the search results HTML file is stored.
		state_name (str): The name of the state for which reports are being parsed.
	"""

	print(f"\n\nParsing search results for state: {state_name}")

	all_rows = []

	state_file = file_path / f"results_{state_name}.html"
	if not state_file.exists():
		return

	# Read the state-specific HTML file and parse report links.
	with open(state_file, "r", encoding="utf-8") as html_file:
		soup = BeautifulSoup(html_file.read(), "html.parser")

	# Finds anchors whose href contains the report details endpoint
	report_links = soup.select('a[href*="dspERTDocumentDetails.cfm"]')

	for a in report_links:
		href = a.get("href")
		if href:
			all_rows.append({
				"state": state_name,
				"report_url": href
			})

	# Write the extracted report URLs to a CSV file for the state
	output_csv = file_path / f"{state_name}_report_urls.csv"
	with open(output_csv, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=["state", "report_url"])
		writer.writeheader()
		writer.writerows(all_rows)

	# Calculating the number of reports found and printing the result
	num_reports = len(all_rows)
	print(f"\n\nFound {num_reports} reports for state: {state_name}")

def get_results(session, raw_data_dir, api_dir, state_name, max_attempts=3, retry_delay_seconds=2):
	"""
	GETs the report pages for each URL in the parsed CSV and saves them to files in the raw data directory.

	Args:
		session (requests.Session): The session object for making HTTP requests.
		raw_data_dir (Path): The directory where raw data files will be saved.
		api_dir (Path): The directory where API-related files are stored.
		state_name (str): The name of the state for which reports are being downloaded.
		max_attempts (int): The maximum number of retry attempts for failed requests.
		retry_delay_seconds (int): The delay in seconds between retry attempts.
	"""
	
	print(f"\n\nDownloading reports for state: {state_name}")
	
	# Read the CSV file containing report URLs for the state
	csv_path = api_dir / f"{state_name}_report_urls.csv"
	raw_data_dir.mkdir(parents=True, exist_ok=True)

	# If the CSV file does not exist, return early
	if not csv_path.exists():
		return
	
	# Loop through each report URL in the CSV and GET the report page, saving it to a file
	with open(csv_path, "r", encoding="utf-8") as csv_file:
		reader = csv.DictReader(csv_file)

		# Finding the number of reports to download for progress tracking
		num_reports = sum(1 for _ in reader)
		num_dl = 0

		# Rewind and rebuild DictReader so header is handled correctly again
		csv_file.seek(0)
		reader = csv.DictReader(csv_file)

		for idx, row in enumerate(reader, start=1):
			# Read the URL of the report from the CSV row
			report_url = row.get("report_url", "").strip()
			if not report_url:
				continue

			# GET the report with a simple retry loop
			response = None
			for attempt in range(1, max_attempts + 1):
				try:
					response = session.get(report_url, timeout=30)
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

			# Save the report content to a file in the raw data directory
			with open(output_file_path, "wb") as output_file:
				output_file.write(response.content)

			# Tracking the number of reports downloaded and printing progress
			num_dl += 1
			print(f"Downloaded report {num_dl} of {num_reports} for state: {state_name}")
	print("*" * 50)

if __name__ == "__main__":
	from common import utilities

	# Load configuration
	config = utilities.load_config()

	# Builds the paths for the data directories
	paths = utilities.build_paths(config)

	# Downloading reports from WebFIRE API for each state
	fetch_reports(config, paths)
