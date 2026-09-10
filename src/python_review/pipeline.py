def main(config, paths):

    return


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    main(config, paths)
