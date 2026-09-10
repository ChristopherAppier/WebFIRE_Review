import csv
import logging
import shutil
import zipfile
from pathlib import Path

import magic

logger = logging.getLogger(__name__)


def extract_and_route_files(paths):
    """
    Extracts files from the raw data directory and routes them into either the spreadsheet, pdf, or other (catch-all) folders for later processing.

    Args:
        paths : A dictionary of path objects for the various directories used in the process.
    """

    logger.info("\nExtracting zip files from raw data directory")

    # Tracks zip filename -> extracted base filenames across all unzip rounds.
    zip_to_documents = {}

    # Check for zip files
    zips_present = check_for_zips(paths)

    # Extracts all zip files in the raw directory while there are still zip files present (handles nested zips)
    while zips_present:
        # Extract all zip files in the raw directory
        round_zip_documents = extract_zips(paths)
        merge_zip_documents(zip_to_documents, round_zip_documents)

        # Flattens the directory structure in the raw directory (moves all files from subdirectories to the root of the raw directory)
        flatten_directory(paths)

        # Check again if there are any zip files left in the raw directory
        zips_present = check_for_zips(paths)

    # Rolls nested zip contents up to parent zips before writing Document List.
    zip_to_documents = resolve_nested_zip_documents(zip_to_documents)

    # Updates CSV rows for zip records using the files extracted from each zip.
    update_document_lists(paths, zip_to_documents)

    # Route files into the appropriate directories based on their MIME type after unzips
    logger.info(
        f"\n{'*' * 50}\n\nRouting files into appropriate directories based on file type"
    )

    route_files(paths)


def check_for_zips(paths):
    """
    Checks if there are any zip files present in the specified folder.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
    """
    # Check if there are any zip files in the raw directory using magic library
    for file_name in paths["raw_data_dir"].iterdir():
        mime_type = magic.from_file(file_name, mime=True)
        if mime_type == "application/zip":
            return True

    return False


def extract_zips(paths):
    """
    Extracts all zip files in the raw directory.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
    """
    zip_to_documents = {}

    for file_name in paths["raw_data_dir"].iterdir():
        mime_type = magic.from_file(file_name, mime=True)
        if mime_type == "application/zip":
            # Extract the zip file
            with zipfile.ZipFile(file_name, "r") as zip_ref:
                extracted_files = []
                for member_name in zip_ref.namelist():
                    if member_name.endswith("/"):
                        continue
                    normalized_name = member_name.replace("\\", "/").rstrip("/")
                    base_name = Path(normalized_name).name
                    if not base_name:
                        continue
                    # Skipping metadata.xml files
                    if base_name.lower() == "metadata.xml":
                        continue
                    target_path = build_unique_target_path(
                        paths["raw_data_dir"], base_name
                    )
                    with (
                        zip_ref.open(member_name) as source,
                        open(target_path, "wb") as destination,
                    ):
                        shutil.copyfileobj(source, destination)
                    extracted_files.append(target_path.name)

                zip_to_documents[file_name.name] = dedupe_preserve_order(
                    extracted_files
                )
            # Delete the zip file after extraction
            file_name.unlink()

    return zip_to_documents


def build_unique_target_path(raw_data_dir, file_name):
    """
    Builds a collision-safe target path in the raw directory.

    Args:
        raw_data_dir (Path): Root raw directory for extracted files.
        file_name (str): Desired base filename.
    """
    candidate = raw_data_dir / file_name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    copy_index = 1

    while True:
        copy_suffix = "_copy" if copy_index == 1 else f"_copy{copy_index}"
        candidate = raw_data_dir / f"{stem}{copy_suffix}{suffix}"
        if not candidate.exists():
            return candidate
        copy_index += 1


def dedupe_preserve_order(items):
    """
    Removes duplicates while preserving original order.

    Args:
        items (list[str]): A list of strings that may contain duplicates.
    """
    unique_items = []
    seen = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items


def merge_zip_documents(all_zip_documents, round_zip_documents):
    """
    Merges per-round zip extraction results into one mapping.

    Args:
        all_zip_documents (dict): Aggregate mapping of zip name to extracted base filenames.
        round_zip_documents (dict): Mapping from the current extraction round.
    """
    for zip_name, document_names in round_zip_documents.items():
        if zip_name not in all_zip_documents:
            all_zip_documents[zip_name] = []
        all_zip_documents[zip_name].extend(document_names)
        all_zip_documents[zip_name] = dedupe_preserve_order(all_zip_documents[zip_name])


def resolve_nested_zip_documents(zip_to_documents):
    """
    Resolves nested zip references so parent zip mappings include child zip contents.

    Args:
        zip_to_documents (dict): Mapping of zip filename to extracted base filenames.
    """
    resolved_cache = {}

    def expand(zip_name, visiting):
        if zip_name in resolved_cache:
            return resolved_cache[zip_name]

        resolved_names = []
        for name in zip_to_documents.get(zip_name, []):
            if name.lower().endswith(".zip") and name in zip_to_documents:
                if name in visiting:
                    continue
                resolved_names.extend(expand(name, visiting | {name}))
            else:
                resolved_names.append(name)

        resolved_names = dedupe_preserve_order(resolved_names)
        resolved_cache[zip_name] = resolved_names
        return resolved_names

    return {zip_name: expand(zip_name, {zip_name}) for zip_name in zip_to_documents}


def update_document_lists(paths, zip_to_documents):
    """
    Updates master report_table.csv by filling Document List for zip rows from extraction results.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
        zip_to_documents (dict): Mapping of zip filename to extracted base filenames.
    """
    csv_path = paths["http_dir"] / "report_table.csv"
    if not csv_path.exists():
        logger.warning(
            "\nreport_table.csv not found in http directory. Skipping Document List update."
        )
        return

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if "Document List" not in fieldnames:
        fieldnames.append("Document List")

    for row in rows:
        downloaded_filename = row.get("Downloaded Filename", "").strip()
        if not downloaded_filename:
            downloaded_filename = row.get("Document Name", "").strip()

        if not downloaded_filename:
            continue

        if downloaded_filename.lower().endswith(".zip"):
            document_names = zip_to_documents.get(downloaded_filename, [])
            if document_names:
                row["Document List"] = "|".join(document_names)
        else:
            if not row.get("Document List", "").strip():
                row["Document List"] = downloaded_filename

    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def flatten_directory(paths):
    """
    Flattens the directory structure in the raw directory by moving all files from subdirectories to the root of the raw directory.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
    """
    for subdir in paths["raw_data_dir"].iterdir():
        if subdir.is_dir():
            for file_name in subdir.iterdir():
                # Move the file to the raw directory (adding a suffix if a file with the same name already exists)
                target_path = paths["raw_data_dir"] / file_name.name
                if target_path.exists():
                    target_path = (
                        paths["raw_data_dir"]
                        / f"{file_name.stem}_copy{file_name.suffix}"
                    )
                file_name.rename(target_path)
            # Delete the now-empty subdirectory
            subdir.rmdir()


def route_files(paths):
    """
    Routes files in the raw directory into either the spreadsheet, pdf, or other (catch-all) folders based on their MIME type.

    Args:
        paths (dict): A dictionary of path objects for the various directories used in the process.
    """
    for file_name in paths["raw_data_dir"].iterdir():
        mime_type = magic.from_file(file_name, mime=True)

        # Targets .pdf files to the pdf directory
        if mime_type == "application/pdf":
            target_dir = paths["pdf_dir"]

        # Targets .xls and .xlsx files to the spreadsheet directory
        elif mime_type in [
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]:
            target_dir = paths["spreadsheet_dir"]

        # Targets all other files to the catch-all directory
        else:
            target_dir = paths["other_dir"]

        # Move the file to the appropriate directory
        target_path = target_dir / file_name.name
        file_name.rename(target_path)


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    extract_and_route_files(paths)
