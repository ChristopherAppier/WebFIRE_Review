from common import utilities
from document_retrieval.download_handler import fetch_all_reports
from document_retrieval.zip_extract import extract_and_route_files
from document_retrieval.ocr_handler import apply_ocr

def main():
    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)
    
    # Downloading reports from WebFIRE API for each state
    state_names = [state['name'] for state in config['states']]
    for state_name in state_names:
        fetch_all_reports(config, state_name, paths)

    # Unzipping files and routing them into either spreadsheet or pdf folders for processing
    extract_and_route_files(paths)

    # OCR PDFs
    apply_ocr(paths, config)

if __name__ == "__main__":
    main()