import json
import csv
from pathlib import Path

def compile_reviews(config, paths):
    """
    Compiles the review JSON files into a single CSV file for easy review.

    Args:
        config (dict): Configuration settings.
        paths (dict): Paths to the data directories.
    """

    print(f"\n{'*' * 50}\n\nCompiling review files")

    review_data = []

    # Path to the directory containing review JSON files and selecting only JSON files
    review_files = paths['rev_json_dir'].glob('*.json')

    # Iterate through the review JSON files in the configured directory
    for review_file in review_files:
        with open(review_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            review_data.append(data)

    # Error message for no review JSON files found
    if not review_data:
        print(f"\nNo review files found")
        return

    # Write the compiled data to a CSV file under the summary directory
    csv_output_path = paths['summary_dir'] / 'summary_report.csv'
    fieldnames = [key for review in review_data for key in review.keys()]
    with open(csv_output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for review in review_data:
            writer.writerow(review)

    print(f"\nCompiled {len(review_data)} review files\n\n{'*' * 50}\n")

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    compile_reviews(config, paths)