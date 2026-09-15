import logging
import shutil
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Paths:
    root: Path
    directories: dict[str, Path]

    def __getattr__(self, name: str) -> Path:
        """Allow attribute-style access for configured directory keys."""
        try:
            return self.directories[name]
        except KeyError as exc:
            raise AttributeError(f"No configured directory named '{name}'") from exc

    def __getitem__(self, name: str) -> Path:
        """Allow dict-style access for configured directory keys."""
        return self.directories[name]

    def __truediv__(self, other: str) -> Path:
        """Behave like the project root Path when used with the / operator."""
        return self.root / other


def initialize_project() -> tuple[dict, Paths]:
    """Initialize the project by loading configuration and building paths."""
    config = load_config()
    paths = build_paths(config, initialize_directories=False)
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(paths.log_dir, config.get("logging"))
    logger.info("Initializing project directories")
    data_dir_clean(config, paths)

    return config, paths


def find_project_root(start: Path | None = None) -> Path:
    ROOT_MARKER = "README.md"

    # Walk upward until the project marker identifies the repository root
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ROOT_MARKER).exists():
            return candidate
    raise RuntimeError("Could not locate project root")


def load_config() -> dict:
    """Load configuration from settings.yml."""
    project_root = find_project_root()  # Finds the root folder of the project

    config_path = (
        project_root / "config" / "settings.yml"
    )  # Sets the path for the settings.yml file

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise TypeError(f"Configuration in {config_path} must be a mapping")

    _validate_remove_data(config.get("remove_data", False))
    return config


def build_paths(config: dict, *, initialize_directories: bool = True) -> Paths:
    """Returns folder paths as defined in settings.yml. Additions to settings.yml will automatically be added to the Paths object."""
    if not isinstance(config, dict):
        raise TypeError("config must be a mapping")

    dirs = config.get("directories", {})
    if not isinstance(dirs, dict):
        raise TypeError(
            "config['directories'] must be a mapping of name -> relative path"
        )
    if "log_dir" not in dirs:
        raise ValueError("config['directories'] must define 'log_dir'")

    # Resolve configured directories and keep them inside the project root
    root = find_project_root().resolve()
    resolved_directories = {}
    for name, relative_path in dirs.items():
        if not isinstance(name, str) or not name.strip():
            raise TypeError("Directory names must be non-empty strings")
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise TypeError(f"Directory path for '{name}' must be a non-empty string")

        configured_path = Path(relative_path)
        if configured_path.is_absolute():
            raise ValueError(f"Directory path for '{name}' must be relative")

        resolved_path = (root / configured_path).resolve()
        try:
            resolved_path.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                f"Directory path for '{name}' must remain inside the project root"
            ) from exc
        resolved_directories[name] = resolved_path

    paths = Paths(root=root, directories=resolved_directories)
    data_root = (root / "data").resolve()
    try:
        paths.log_dir.relative_to(data_root)
    except ValueError as exc:
        raise ValueError(
            "config['directories']['log_dir'] must be inside 'data'"
        ) from exc

    _validate_remove_data(config.get("remove_data", False))
    if initialize_directories:
        data_dir_clean(config, paths)
    return paths


def _validate_remove_data(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise ValueError("config['remove_data'] must be true or false")


def data_dir_clean(config: dict, paths: Paths) -> None:
    """
    Creates the directories as defined in settings.yml if they do not already exist. If remove_data in settings.yml is set to True, it will also clean the data directory by removing all files and subdirectories before rebuilding the directories.
    """
    data_dir = (paths.root / "data").resolve()
    expected_data_dir = paths.root.resolve() / "data"
    if data_dir != expected_data_dir:
        raise ValueError(f"Refusing to clean unexpected data directory: {data_dir}")

    try:
        # Optionally remove prior data while preserving the log directory
        if _validate_remove_data(config.get("remove_data", False)):
            logger.info("Removing data files from %s", data_dir)
            log_dir = paths.log_dir.resolve()
            data_dir.mkdir(parents=True, exist_ok=True)
            for item in data_dir.iterdir():
                resolved_item = item.resolve()
                if resolved_item == log_dir or resolved_item in log_dir.parents:
                    continue
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info("Finished removing data files from %s", data_dir)

        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / ".gitkeep").touch(exist_ok=True)
        for dir_path in paths.directories.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            try:
                dir_path.relative_to(data_dir)
            except ValueError:
                continue
            (dir_path / ".gitkeep").touch(exist_ok=True)
    except OSError:
        logger.exception("Failed to initialize project directories under %s", data_dir)
        raise


def setup_logging(log_dir: Path, settings: dict | None = None) -> None:
    """Configure console and rotating-file logging for the application."""
    settings = settings or {}
    configured_level = settings.get("level", "INFO")
    if not isinstance(configured_level, str):
        raise TypeError("logging.level must be a string")
    level_name = configured_level.upper()
    if level_name not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(f"Invalid logging level: {level_name}")
    level = getattr(logging, level_name)

    max_bytes = int(settings.get("max_bytes", 5_000_000))
    backup_count = int(settings.get("backup_count", 3))
    if max_bytes < 1:
        raise ValueError("logging.max_bytes must be a positive integer")
    if backup_count < 0:
        raise ValueError("logging.backup_count must be zero or greater")

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s [%(threadName)s]: %(message)s"
    )
    file_handler = RotatingFileHandler(
        log_dir / "webfire_review.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
