from summary_report.review_compiler import compile_reviews


def main(config, paths):
    
    # Compile the review JSONs into a single csv for easy review
    compile_reviews(config, paths)

if __name__ == "__main__":
    from common import utilities

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = utilities.initialize_project()

    main(config, paths)
