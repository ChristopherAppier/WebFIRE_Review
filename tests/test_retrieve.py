import csv
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from retrieve.download import get_results, parse_search_results, post_search
from retrieve.extract import extract_zips, route_files


class FakeCookies:
    def get_dict(self):
        return {}

    def update(self, cookies):
        pass


class StreamingResponse:
    def __init__(self, filename, error=None):
        self.headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        self.error = error

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield b"partial"
        if self.error:
            raise self.error

    def close(self):
        pass


class WorkerSession:
    def __init__(self, response):
        self.response = response
        self.headers = {}
        self.cookies = FakeCookies()

    def get(self, url, timeout, stream):
        return self.response

    def close(self):
        pass


class RetrieveDownloadTests(unittest.TestCase):
    def test_post_search_applies_timeout_and_checks_each_response(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            responses = [Mock(), Mock(), Mock(text="<table id='myDocTable'></table>")]
            session = Mock()
            session.headers = {}
            session.get.return_value = responses[0]
            session.post.side_effect = responses[1:]

            post_search(
                "https://example.test",
                session,
                "01/01/2026",
                "01/02/2026",
                "KS",
                {"http_dir": Path(temp_dir)},
                timeout=12,
            )

            self.assertEqual(session.get.call_args.kwargs["timeout"], 12)
            self.assertTrue(
                all(
                    call.kwargs["timeout"] == 12 for call in session.post.call_args_list
                )
            )
            for response in responses:
                response.raise_for_status.assert_called_once_with()

    def test_post_search_reraises_http_failure_with_context(self):
        session = Mock()
        session.headers = {}
        session.get.side_effect = requests.exceptions.Timeout("timed out")

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            self.assertLogs("retrieve.download", level="ERROR") as logs,
            self.assertRaises(requests.exceptions.Timeout),
        ):
            post_search(
                "https://example.test",
                session,
                "01/01/2026",
                "01/02/2026",
                "KS",
                {"http_dir": Path(temp_dir)},
                timeout=12,
            )

        self.assertIn("state KS", "\n".join(logs.output))

    def test_parse_search_results_rejects_missing_results_table(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            http_dir = Path(temp_dir)
            (http_dir / "results_KS.html").write_text(
                "<html><body>Service unavailable</body></html>", encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "expected results table"):
                parse_search_results(http_dir, "KS")

    def test_stream_failure_removes_partial_file_and_persists_other_results(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            http_dir = temp_path / "http"
            raw_dir = temp_path / "raw"
            http_dir.mkdir()
            csv_path = http_dir / "KS_report_table.csv"
            fieldnames = ["report_url", "Downloaded Filename", "Document List"]
            with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(
                    [
                        {"report_url": "https://example.test/good"},
                        {"report_url": "https://example.test/broken"},
                    ]
                )

            source_session = Mock(headers={}, cookies=FakeCookies())
            worker_sessions = [
                WorkerSession(StreamingResponse("good.pdf")),
                WorkerSession(
                    StreamingResponse(
                        "broken.pdf", requests.exceptions.ConnectionError("lost")
                    )
                ),
            ]
            with (
                patch(
                    "retrieve.download.requests.Session", side_effect=worker_sessions
                ),
                patch("retrieve.download.tqdm", side_effect=lambda items, **_: items),
            ):
                get_results(
                    source_session,
                    raw_dir,
                    http_dir,
                    "KS",
                    max_attempts=1,
                    retry_delay_seconds=0,
                    max_workers=1,
                )

            with open(csv_path, "r", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(rows[0]["Downloaded Filename"], "good.pdf")
            self.assertEqual(rows[1]["Downloaded Filename"], "")
            self.assertTrue((raw_dir / "good.pdf").exists())
            self.assertFalse((raw_dir / "broken.pdf").exists())

    def test_unexpected_worker_failure_does_not_prevent_csv_rewrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            http_dir = temp_path / "http"
            http_dir.mkdir()
            csv_path = http_dir / "KS_report_table.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=["report_url"])
                writer.writeheader()
                writer.writerow({"report_url": "https://example.test/report"})

            source_session = Mock(headers={}, cookies=FakeCookies())
            with (
                patch(
                    "retrieve.download._download_report",
                    side_effect=ValueError("unexpected"),
                ),
                patch("retrieve.download.tqdm", side_effect=lambda items, **_: items),
                self.assertLogs("retrieve.download", level="ERROR"),
            ):
                get_results(source_session, temp_path / "raw", http_dir, "KS")

            with open(csv_path, "r", encoding="utf-8") as csv_file:
                row = next(csv.DictReader(csv_file))
            self.assertEqual(row["Downloaded Filename"], "")

    def test_blank_urls_are_not_counted_as_failed_downloads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            http_dir = temp_path / "http"
            http_dir.mkdir()
            csv_path = http_dir / "KS_report_table.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=["report_url"])
                writer.writeheader()
                writer.writerow({"report_url": ""})

            source_session = Mock(headers={}, cookies=FakeCookies())
            with (
                patch("retrieve.download.tqdm", side_effect=lambda items, **_: items),
                self.assertLogs("retrieve.download", level="INFO") as logs,
            ):
                get_results(source_session, temp_path / "raw", http_dir, "KS")

            self.assertIn("All reports successfully downloaded", "\n".join(logs.output))


class RetrieveExtractionTests(unittest.TestCase):
    def make_paths(self, root):
        paths = {
            "raw_data_dir": root / "raw",
            "pdf_dir": root / "pdf",
            "spreadsheet_dir": root / "spreadsheets",
            "other_dir": root / "other",
        }
        for path in paths.values():
            path.mkdir()
        return paths

    def test_route_files_uses_collision_safe_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self.make_paths(Path(temp_dir))
            (paths["raw_data_dir"] / "report.pdf").write_bytes(b"new")
            (paths["pdf_dir"] / "report.pdf").write_bytes(b"existing")

            with patch(
                "retrieve.extract.magic.from_file", return_value="application/pdf"
            ):
                route_files(paths)

            self.assertEqual(
                (paths["pdf_dir"] / "report.pdf").read_bytes(), b"existing"
            )
            self.assertEqual(
                (paths["pdf_dir"] / "report_copy.pdf").read_bytes(), b"new"
            )

    def test_corrupt_zip_is_preserved_and_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self.make_paths(Path(temp_dir))
            archive_path = paths["raw_data_dir"] / "broken.zip"
            archive_path.write_bytes(b"not a zip")

            with (
                patch(
                    "retrieve.extract.magic.from_file", return_value="application/zip"
                ),
                self.assertLogs("retrieve.extract", level="ERROR") as logs,
                self.assertRaisesRegex(RuntimeError, "broken.zip"),
            ):
                extract_zips(paths)

            self.assertTrue(archive_path.exists())
            self.assertIn("Failed to extract archive", "\n".join(logs.output))

    def test_successful_zip_is_deleted_after_extraction(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self.make_paths(Path(temp_dir))
            archive_path = paths["raw_data_dir"] / "reports.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("nested/report.txt", "content")

            with patch(
                "retrieve.extract.magic.from_file", return_value="application/zip"
            ):
                result = extract_zips(paths)

            self.assertFalse(archive_path.exists())
            self.assertEqual(result, {"reports.zip": ["report.txt"]})
            self.assertEqual(
                (paths["raw_data_dir"] / "report.txt").read_text(encoding="utf-8"),
                "content",
            )


if __name__ == "__main__":
    unittest.main()
