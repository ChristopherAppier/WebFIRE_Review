from retrieve.download import fetch_reports
from retrieve.extract import extract_and_route_files
from retrieve.ocr import apply_ocr


def main(config, paths):

    # Downloading reports from WebFIRE API for each state
    fetch_reports(config, paths)

    # Unzipping files and routing them into either spreadsheet or pdf folders for processing
    extract_and_route_files(paths)

    # OCR PDFs
    apply_ocr(config, paths)


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    main(config, paths)
