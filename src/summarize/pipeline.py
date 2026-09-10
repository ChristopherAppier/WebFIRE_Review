from summarize.compile import compile_reviews


def main(config, paths):

    # Compile the review JSONs into a single csv for easy review
    compile_reviews(config, paths)


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    main(config, paths)
