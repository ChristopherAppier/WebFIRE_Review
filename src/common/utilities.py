import yaml
from dataclasses import dataclass
from pathlib import Path

def find_project_root(start: Path | None = None) -> Path:
    ROOT_MARKER = "README.md"

    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ROOT_MARKER).exists():
            return candidate
    raise RuntimeError("Could not locate project root")

def load_config():
    """Load configuration from settings.yml."""
    print(f"\n\n{'*' * 50}\n\nLoading configuration data from settings.yml")

    project_root = find_project_root() # Finds the root folder of the project

    config_path = project_root / "config" / "settings.yml" # Sets the path for the settings.yml file
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

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

def build_paths(config: dict) -> Paths:

    """Returns folder paths as defined in settings.yml. Additions to settings.yml will automatically be added to the Paths object."""

    print(f"\n{'*' * 50}\n\nBuilding paths from settings.yml")

    # Load directory paths from the configuration.
    dirs = config.get("directories", {})
    if not isinstance(dirs, dict):
        raise ValueError("config['directories'] must be a mapping of name -> relative path")

    # Finds the project root
    root = find_project_root()

    resolved_directories = {
        name: root / relative_path
        for name, relative_path in dirs.items()
    }

    return Paths(
        root=root,
        directories=resolved_directories,
    )

def data_dir_clean(config: dict, paths: Paths) -> None:
    """
    Creates the directories as defined in settings.yml if they do not already exist. If remove_data in settings.yml is set to True, it will also clean the data directory by removing all files and subdirectories before rebuilding the directories.
    """
    if config.get("remove_data", "False").lower() == "true":
        # Remove all files and subdirectories in the data directory
        print(f"\n{'*' * 50}\n\nRemoving all files and subdirectories in the data directory")

        data_dir = paths.root / "data"
        for item in data_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                import shutil
                shutil.rmtree(item)

    # Rebuild the directories as defined in settings.yml
    print("\nRebuilding the data directories as defined in settings.yml")

    for dir_path in paths.directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / ".gitkeep").touch(exist_ok=True)