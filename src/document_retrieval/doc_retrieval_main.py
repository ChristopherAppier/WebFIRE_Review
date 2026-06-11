import yaml
from pathlib import Path
from timer_manager import check_timer
from download_handler import fetch_all_reports
from zip_extract import extract_and_route_files
from ocr_handler import apply_ocr
from file_renamer import rename_files

def load_config():
    """Load configuration from settings.yml."""
    project_root = Path(__file__).parent.parent.parent # Finds the root folder of the project based on this main.py file location
    config_path = project_root / "config" / "settings.yml" # Sets the path for the settings.yml file
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_system_status(config):
    """Print system status and configuration info."""
    print("=" * 50)
    print("WebFIRE Deviation Scanner")
    print("=" * 50)
    print(f"API Base URL: {config['api_endpoints']['webfire']['base_url']}")
    print(f"API Detail URL: {config['api_endpoints']['webfire']['detail_url']}")
    print(f"Last Run: {config['last_run_timestamp'] or 'Never (first run)'}")
    print(f"Scan Interval: {config['scan_interval_days']} days")
    print(f"PDF Directory: {config['directories']['pdf_dir']}")
    print(f"Spreadsheet Directory: {config['directories']['spreadsheet_dir']}")
    print("=" * 50)
    
def main():
    # Load configuration
    config = load_config()
    
    project_root = Path(__file__).parent.parent.parent
    
    # Debug printing
    #print_system_status(config)
    
    # Getting the date range for the WebFIRE API request based on last run date
    timer_info = check_timer(config)
    start_date = timer_info['start_date']
    end_date = timer_info['end_date']
    
    # Downloading reports from WebFIRE API for each state
    #state_names = [state['name'] for state in config['states']]
    #for state_name in state_names:
        #fetch_all_reports(start_date, end_date, state_name, project_root)

    # Unzipping files and routing them into either spreadsheet or pdf folders for processing
    #extract_and_route_files(project_root)

    # OCR PDFs
    #apply_ocr(project_root)

    # Rename files based on content using AI
    rename_files(project_root)

if __name__ == "__main__":
    main()