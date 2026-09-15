import csv
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import requests

from retrieve.download import get_results


class FakeCookies:
    def update(self, cookies):
        pass


class FakeResponse:
    headers = {"Content-Disposition": 'attachment; filename="report.pdf"'}

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield b"report content"

    def close(self):
        pass


class FakeSession:
    def __init__(self, barrier, activity):
        self.barrier = barrier
        self.activity = activity
        self.headers = {}
        self.cookies = FakeCookies()

    def get(self, url, timeout, stream):
        if url.endswith("failed"):
            raise requests.exceptions.RequestException("failed request")

        with self.activity["lock"]:
            self.activity["active"] += 1
            self.activity["maximum"] = max(
                self.activity["maximum"], self.activity["active"]
            )
        try:
            self.barrier.wait(timeout=2)
            return FakeResponse()
        finally:
            with self.activity["lock"]:
                self.activity["active"] -= 1

    def close(self):
        pass


class DownloadConcurrencyTest(unittest.TestCase):
    def test_downloads_concurrently_and_preserves_csv_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            http_dir = temp_path / "http"
            raw_dir = temp_path / "raw"
            http_dir.mkdir()
            csv_path = http_dir / "KS_report_table.csv"
            fieldnames = [
                "Marker",
                "report_url",
                "Downloaded Filename",
                "Document List",
                "Prompt Name",
            ]
            rows = [
                {"Marker": "first", "report_url": "https://example.test/one"},
                {"Marker": "second", "report_url": "https://example.test/two"},
                {"Marker": "third", "report_url": "https://example.test/failed"},
            ]
            with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            source_session = requests.Session()
            barrier = threading.Barrier(2)
            activity = {"active": 0, "maximum": 0, "lock": threading.Lock()}

            with (
                patch(
                    "retrieve.download.requests.Session",
                    side_effect=lambda: FakeSession(barrier, activity),
                ),
                patch(
                    "retrieve.download.tqdm",
                    side_effect=lambda iterable, **kwargs: iterable,
                ),
            ):
                get_results(
                    source_session,
                    raw_dir,
                    http_dir,
                    "KS",
                    max_attempts=1,
                    retry_delay_seconds=0,
                    max_workers=3,
                )
            source_session.close()

            with open(csv_path, "r", encoding="utf-8") as csv_file:
                saved_rows = list(csv.DictReader(csv_file))

            self.assertGreaterEqual(activity["maximum"], 2)
            self.assertEqual(
                [row["Marker"] for row in saved_rows], ["first", "second", "third"]
            )
            filenames = [row["Downloaded Filename"] for row in saved_rows[:2]]
            self.assertEqual(set(filenames), {"report.pdf", "report_1.pdf"})
            self.assertTrue(
                all((raw_dir / filename).exists() for filename in filenames)
            )
            self.assertEqual(saved_rows[2]["Downloaded Filename"], "")
            self.assertEqual(saved_rows[2]["Document List"], "")


if __name__ == "__main__":
    unittest.main()
