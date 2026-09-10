def main(config, paths):

    return


if __name__ == "__main__":
    from common import startup

    # Load configuration
    config = startup.load_config()

    # Builds the paths for the data directories
    paths = startup.build_paths(config)

    main(config, paths)
