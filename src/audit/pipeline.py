def main(config, paths):

    # Audit flagged reviews after the lightweight review stage
    return


if __name__ == "__main__":
    from common import startup

    # Load configuration
    config = startup.load_config()

    # Builds the paths for the data directories
    paths = startup.build_paths(config)

    main(config, paths)
