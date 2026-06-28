import magic
import zipfile

def extract_and_route_files(paths):
    """
    Extracts files from the raw data directory and routes them into either the spreadsheet, pdf, or other (catch-all) folders for later processing.

    Args:
        paths : A dictionary of path objects for the various directories used in the process.
    """

    print(f"\n\nExtracting zip files from raw data directory")

    # Ensure the target directories exist
    paths['spreadsheet_dir'].mkdir(parents=True, exist_ok=True)
    paths['pdf_dir'].mkdir(parents=True, exist_ok=True)
    paths['other_dir'].mkdir(parents=True, exist_ok=True)

    # Check for zip files
    zips_present = check_for_zips(paths)

    # Extracts all zip files in the raw directory while there are still zip files present (handles nested zips)
    while zips_present:
        # Extract all zip files in the raw directory
        extract_zips(paths)

        # Flattens the directory structure in the raw directory (moves all files from subdirectories to the root of the raw directory)
        flatten_directory(paths)

        # Check again if there are any zip files left in the raw directory
        zips_present = check_for_zips(paths)

    # Route files into the appropriate directories based on their MIME type after unzips
    print(f"\n\n{'*' * 50}\n\nRouting files into appropriate directories based on file type\n")
    route_files(paths)

def check_for_zips(paths):
    """
    Checks if there are any zip files present in the specified folder.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
    """
    # Check if there are any zip files in the raw directory using magic library
    for file_name in paths['raw_data_dir'].iterdir():
        mime_type = magic.from_file(file_name, mime=True)
        if mime_type == 'application/zip':
            return True
        
    return False

def extract_zips(paths):
    """
    Extracts all zip files in the raw directory.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
    """
    for file_name in paths['raw_data_dir'].iterdir():
        mime_type = magic.from_file(file_name, mime=True)
        if mime_type == 'application/zip':
            # Extract the zip file
            with zipfile.ZipFile(file_name, 'r') as zip_ref:
                zip_ref.extractall(paths['raw_data_dir'])
            # Delete the zip file after extraction
            file_name.unlink()

def flatten_directory(paths):
    """
    Flattens the directory structure in the raw directory by moving all files from subdirectories to the root of the raw directory.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
    """
    for subdir in paths['raw_data_dir'].iterdir():
        if subdir.is_dir():
            for file_name in subdir.iterdir():
                # Move the file to the raw directory (adding a suffix if a file with the same name already exists)
                target_path = paths['raw_data_dir'] / file_name.name
                if target_path.exists():
                    target_path = paths['raw_data_dir'] / f"{file_name.stem}_copy{file_name.suffix}"
                file_name.rename(target_path)
            # Delete the now-empty subdirectory
            subdir.rmdir()

def route_files(paths):
    """
    Routes files in the raw directory into either the spreadsheet, pdf, or other (catch-all) folders based on their MIME type.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
    """
    for file_name in paths['raw_data_dir'].iterdir():
        mime_type = magic.from_file(file_name, mime=True)

        # Targets .pdf files to the pdf directory
        if mime_type == 'application/pdf':
            target_dir = paths['pdf_dir']

        # Targets .xls and .xlsx files to the spreadsheet directory
        elif mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            target_dir = paths['spreadsheet_dir']
        
        # Targets all other files to the catch-all directory
        else:
            target_dir = paths['other_dir']

        # Move the file to the appropriate directory
        target_path = target_dir / file_name.name
        file_name.rename(target_path)

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    extract_and_route_files(paths)