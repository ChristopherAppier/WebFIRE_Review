from document_retrieval.download_handler import fetch_reports
from document_retrieval.extract_and_route import extract_and_route_files
from document_retrieval.ocr_handler import apply_ocr

def main(paths, config):
    
    # Downloading reports from WebFIRE API for each state
    fetch_reports(config, paths)

    # Unzipping files and routing them into either spreadsheet or pdf folders for processing
    extract_and_route_files(paths)

    # OCR PDFs
    apply_ocr(paths, config)

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    # Removes previous run data (if enabled in settings.yml) and checks folder structure
    utilities.data_dir_clean(config, paths)

    main(paths, config)