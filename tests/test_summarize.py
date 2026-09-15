import csv
import json
import tempfile
import unittest
from pathlib import Path

from summarize.compile import compile_reviews


class CompileReviewsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.review_dir = self.root / "reviews"
        self.summary_dir = self.root / "summary"
        self.review_dir.mkdir()
        self.summary_dir.mkdir()
        self.paths = {
            "review_dir": self.review_dir,
            "summary_dir": self.summary_dir,
        }

    def write_review(self, filename, data):
        review_path = self.review_dir / filename
        review_path.write_text(json.dumps(data), encoding="utf-8")

    def test_compiles_review_and_logs_output(self):
        self.write_review("review.json", {"facility": "Example", "status": "pass"})

        with self.assertLogs("summarize.compile", level="INFO") as logs:
            compile_reviews({}, self.paths)

        output_path = self.summary_dir / "summary_report.csv"
        with output_path.open(newline="", encoding="utf-8") as csvfile:
            rows = list(csv.DictReader(csvfile))

        self.assertEqual(rows, [{"facility": "Example", "status": "pass"}])
        self.assertIn("Found 1 review files", "\n".join(logs.output))
        self.assertIn(str(output_path), "\n".join(logs.output))

    def test_skips_malformed_review_and_compiles_valid_review(self):
        (self.review_dir / "bad.json").write_text("{not valid json", encoding="utf-8")
        self.write_review("not-an-object.json", ["unexpected", "list"])
        self.write_review("valid.json", {"facility": "Example"})

        with self.assertLogs("summarize.compile", level="INFO") as logs:
            compile_reviews({}, self.paths)

        log_output = "\n".join(logs.output)
        self.assertIn("Skipping review file bad.json", log_output)
        self.assertIn("Skipping review file not-an-object.json", log_output)
        self.assertIn("JSON root must be an object", log_output)
        self.assertIn("Compiled 1 review files; skipped 2", log_output)
        self.assertTrue((self.summary_dir / "summary_report.csv").exists())

    def test_logs_and_reraises_output_write_failure(self):
        self.write_review("review.json", {"facility": "Example"})
        missing_summary_dir = self.root / "missing-summary"
        self.paths["summary_dir"] = missing_summary_dir

        with (
            self.assertLogs("summarize.compile", level="ERROR") as logs,
            self.assertRaises(OSError),
        ):
            compile_reviews({}, self.paths)

        self.assertIn(
            str(missing_summary_dir / "summary_report.csv"),
            "\n".join(logs.output),
        )


if __name__ == "__main__":
    unittest.main()
