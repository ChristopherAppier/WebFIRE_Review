import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from common import startup


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        (self.root / "README.md").touch()
        (self.root / "config").mkdir()

    def write_config(self, content):
        (self.root / "config" / "settings.yml").write_text(content, encoding="utf-8")

    def build_paths(self, config, **kwargs):
        with patch("common.startup.find_project_root", return_value=self.root):
            return startup.build_paths(config, **kwargs)

    def test_load_config_rejects_empty_or_non_mapping_yaml(self):
        for content in ("", "- data/logs\n"):
            with self.subTest(content=content):
                self.write_config(content)
                with (
                    patch("common.startup.find_project_root", return_value=self.root),
                    self.assertRaisesRegex(TypeError, "must be a mapping"),
                ):
                    startup.load_config()

    def test_build_paths_requires_valid_relative_log_directory(self):
        invalid_configs = (
            ({"directories": {}}, "must define 'log_dir'"),
            ({"directories": {"log_dir": "/tmp/logs"}}, "must be relative"),
            ({"directories": {"log_dir": "logs"}}, "must be inside 'data'"),
            ({"directories": {"log_dir": 4}}, "non-empty string"),
        )

        for config, message in invalid_configs:
            with self.subTest(config=config):
                with self.assertRaisesRegex((TypeError, ValueError), message):
                    self.build_paths(config)
                self.assertFalse((self.root / "data").exists())

    def test_remove_data_accepts_boolean_and_string_values(self):
        for value, expected in (
            (True, True),
            (False, False),
            ("True", True),
            ("false", False),
        ):
            with self.subTest(value=value):
                self.assertEqual(startup._validate_remove_data(value), expected)

        with self.assertRaisesRegex(ValueError, "must be true or false"):
            startup._validate_remove_data("yes")

    def test_cleanup_preserves_logs_and_recreates_configured_directories(self):
        data_dir = self.root / "data"
        log_dir = data_dir / "logs"
        old_dir = data_dir / "old"
        log_dir.mkdir(parents=True)
        old_dir.mkdir()
        (log_dir / "webfire_review.log").write_text("keep", encoding="utf-8")
        (old_dir / "remove.txt").write_text("remove", encoding="utf-8")

        config = {
            "remove_data": True,
            "directories": {
                "log_dir": "data/logs",
                "review_dir": "data/reviews",
            },
        }
        paths = self.build_paths(config)

        self.assertTrue((log_dir / "webfire_review.log").exists())
        self.assertFalse(old_dir.exists())
        self.assertTrue((self.root / "data" / ".gitkeep").exists())
        self.assertTrue((self.root / "data" / "reviews").exists())
        self.assertFalse((self.root / "data" / "reviews" / ".gitkeep").exists())
        self.assertFalse((log_dir / ".gitkeep").exists())

    def test_cleanup_removes_stale_gitkeep_files_without_removing_data(self):
        data_dir = self.root / "data"
        log_dir = data_dir / "logs"
        review_dir = data_dir / "reviews"
        log_dir.mkdir(parents=True)
        review_dir.mkdir()
        (data_dir / ".gitkeep").touch()
        (log_dir / ".gitkeep").touch()
        (review_dir / ".gitkeep").touch()
        (review_dir / "keep.txt").write_text("keep", encoding="utf-8")

        config = {
            "remove_data": False,
            "directories": {
                "log_dir": "data/logs",
                "review_dir": "data/reviews",
            },
        }
        self.build_paths(config)

        self.assertTrue((data_dir / ".gitkeep").exists())
        self.assertTrue((review_dir / "keep.txt").exists())
        self.assertFalse((log_dir / ".gitkeep").exists())
        self.assertFalse((review_dir / ".gitkeep").exists())

    def test_cleanup_logs_and_reraises_filesystem_errors(self):
        data_dir = self.root / "data"
        data_dir.mkdir()
        doomed_file = data_dir / "doomed.txt"
        doomed_file.touch()
        config = {
            "remove_data": True,
            "directories": {"log_dir": "data/logs"},
        }
        paths = self.build_paths(config, initialize_directories=False)

        with (
            patch.object(Path, "unlink", side_effect=OSError("denied")),
            self.assertLogs("common.startup", level="ERROR") as logs,
            self.assertRaisesRegex(OSError, "denied"),
        ):
            startup.data_dir_clean(config, paths)

        self.assertIn(str(data_dir), "\n".join(logs.output))

    def test_initialize_project_configures_logging_before_cleanup(self):
        config = {
            "remove_data": False,
            "directories": {"log_dir": "data/logs"},
        }
        paths = startup.Paths(
            root=self.root,
            directories={"log_dir": self.root / "data" / "logs"},
        )
        calls = []

        with (
            patch("common.startup.load_config", return_value=config),
            patch("common.startup.build_paths", return_value=paths) as build_paths,
            patch(
                "common.startup.setup_logging",
                side_effect=lambda *_: calls.append("logging"),
            ),
            patch(
                "common.startup.data_dir_clean",
                side_effect=lambda *_: calls.append("cleanup"),
            ),
        ):
            result = startup.initialize_project()

        self.assertEqual(result, (config, paths))
        build_paths.assert_called_once_with(config, initialize_directories=False)
        self.assertEqual(calls, ["logging", "cleanup"])

    def test_setup_logging_configures_level_format_and_rotation(self):
        root_logger = Mock(handlers=[])
        file_handler = Mock()
        stream_handler = Mock()

        with (
            patch("common.startup.logging.getLogger", return_value=root_logger),
            patch(
                "common.startup.RotatingFileHandler", return_value=file_handler
            ) as rotating_handler,
            patch("common.startup.logging.StreamHandler", return_value=stream_handler),
        ):
            startup.setup_logging(
                self.root, {"level": "DEBUG", "max_bytes": 1000, "backup_count": 2}
            )

        rotating_handler.assert_called_once_with(
            self.root / "webfire_review.log",
            maxBytes=1000,
            backupCount=2,
            encoding="utf-8",
        )
        root_logger.setLevel.assert_called_once_with(startup.logging.DEBUG)
        root_logger.addHandler.assert_any_call(file_handler)
        root_logger.addHandler.assert_any_call(stream_handler)
        formatter = file_handler.setFormatter.call_args.args[0]
        self.assertIn("%(name)s", formatter._fmt)
        self.assertIn("%(threadName)s", formatter._fmt)

    def test_setup_logging_rejects_invalid_level(self):
        with self.assertRaisesRegex(ValueError, "Invalid logging level"):
            startup.setup_logging(self.root, {"level": "VERBOSE"})


if __name__ == "__main__":
    unittest.main()
