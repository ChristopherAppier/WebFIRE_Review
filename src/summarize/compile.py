import csv
import json
import logging

logger = logging.getLogger(__name__)


def compile_reviews(config, paths):
    """
    Compiles the review JSON files into a single CSV file for easy review.

    Args:
        config (dict): Configuration settings.
        paths (dict): Paths to the data directories.
    """

    logger.info("Compiling review files")
    review_data = []
    skipped_files = 0

    # Path to the directory containing review JSON files and selecting only JSON files
    review_files = sorted(paths["review_dir"].glob("*.json"))
    logger.info("Found %d review files", len(review_files))

    # Iterate through the review JSON files in the configured directory
    for review_file in review_files:
        try:
            with open(review_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise TypeError("JSON root must be an object")
        except (json.JSONDecodeError, UnicodeError, OSError, TypeError) as exc:
            skipped_files += 1
            logger.warning("Skipping review file %s: %s", review_file.name, exc)
            continue

        review_data.append(data)

    # Error message for no review JSON files found
    if not review_data:
        if review_files:
            logger.warning("No valid review files found; skipped %d", skipped_files)
        else:
            logger.warning("No review files found")
        return

    # Write the compiled data to a CSV file under the summary directory
    csv_output_path = paths["summary_dir"] / "summary_report.csv"
    fieldnames = []
    for review in review_data:
        for field in review:
            if field not in fieldnames:
                fieldnames.append(field)
    try:
        with open(csv_output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for review in review_data:
                writer.writerow(review)
    except (OSError, csv.Error):
        logger.exception("Failed to write summary report to %s", csv_output_path)
        raise

    logger.info(
        "Compiled %d review files; skipped %d; wrote %s",
        len(review_data),
        skipped_files,
        csv_output_path,
    )


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    compile_reviews(config, paths)
