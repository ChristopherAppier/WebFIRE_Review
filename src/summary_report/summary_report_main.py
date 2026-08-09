from summary_report.review_compiler import compile_reviews


def main(config, paths):
    
    # Compile the review JSONs into a single csv for easy review
    compile_reviews(config, paths)

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    main(config, paths)
