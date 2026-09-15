import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ai_review import chunk, review


class ChunkingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.pdf_dir = self.root / "pdfs"
        self.chunk_dir = self.root / "chunks"
        self.pdf_dir.mkdir()
        self.chunk_dir.mkdir()
        self.config = {"chunk_size": 3, "chunk_overlap": 1, "chunk_cap": 2}

    def test_validate_chunk_config_rejects_invalid_values(self):
        invalid_configs = (
            ({"chunk_size": None, "chunk_overlap": 0}, "chunk_size"),
            ({"chunk_size": 3, "chunk_overlap": -1}, "chunk_overlap"),
            ({"chunk_size": 3, "chunk_overlap": 3}, "smaller"),
            (
                {"chunk_size": 3, "chunk_overlap": 1, "chunk_cap": 0},
                "chunk_cap",
            ),
        )

        for config, expected_message in invalid_configs:
            with self.subTest(config=config):
                with self.assertRaisesRegex(ValueError, expected_message):
                    chunk.validate_chunk_config(config)

    def test_process_single_pdf_writes_chunks_and_honors_cap(self):
        pdf_path = self.pdf_dir / "report.pdf"
        page = Mock()
        page.extract_text.return_value = "one two three four five six seven"
        opened_pdf = Mock()
        opened_pdf.__enter__ = Mock(return_value=SimpleNamespace(pages=[page]))
        opened_pdf.__exit__ = Mock(return_value=False)

        with patch("ai_review.chunk.pdfplumber.open", return_value=opened_pdf):
            count = chunk.process_single_pdf(self.config, self.chunk_dir, pdf_path)

        self.assertEqual(count, 2)
        self.assertEqual(
            sorted(path.name for path in self.chunk_dir.glob("*.txt")),
            ["report_chunk_000.txt", "report_chunk_001.txt"],
        )

    def test_process_single_pdf_distinguishes_empty_and_extraction_failure(self):
        pdf_path = self.pdf_dir / "report.pdf"
        empty_pdf = Mock()
        empty_pdf.__enter__ = Mock(
            return_value=SimpleNamespace(
                pages=[SimpleNamespace(extract_text=lambda: None)]
            )
        )
        empty_pdf.__exit__ = Mock(return_value=False)

        with patch("ai_review.chunk.pdfplumber.open", return_value=empty_pdf):
            self.assertEqual(
                chunk.process_single_pdf(self.config, self.chunk_dir, pdf_path), 0
            )

        with (
            patch(
                "ai_review.chunk.pdfplumber.open",
                side_effect=OSError("damaged PDF"),
            ),
            self.assertRaisesRegex(chunk.PdfExtractionError, pdf_path.name),
        ):
            chunk.process_single_pdf(self.config, self.chunk_dir, pdf_path)

    def test_chunk_pdfs_continues_and_reports_exact_outcomes(self):
        first_pdf = self.pdf_dir / "a.pdf"
        second_pdf = self.pdf_dir / "b.pdf"
        first_pdf.touch()
        second_pdf.touch()
        paths = {"pdf_dir": self.pdf_dir, "chunk_dir": self.chunk_dir}

        with (
            patch(
                "ai_review.chunk.process_single_pdf",
                side_effect=[chunk.PdfExtractionError("damaged"), 2],
            ) as process_pdf,
            self.assertLogs("ai_review.chunk", level="ERROR") as logs,
        ):
            counts = chunk.chunk_pdfs(self.config, paths)

        self.assertEqual(counts, {"total": 2, "chunked": 1, "empty": 0, "failed": 1})
        self.assertEqual(process_pdf.call_count, 2)
        self.assertIn(first_pdf.name, "\n".join(logs.output))


class ReviewJsonTests(unittest.TestCase):
    def test_json_check_accepts_plain_and_fenced_review_objects(self):
        payload = {
            "issue_flag": 1,
            "issue_descr": "A potential issue was identified.",
            "conf_score": 8,
            "importance": 6.5,
        }

        self.assertEqual(review.json_check(json.dumps(payload)), payload)
        self.assertEqual(
            review.json_check(f"```json\n{json.dumps(payload)}\n```"), payload
        )

    def test_json_check_rejects_invalid_shapes_without_echoing_raw_output(self):
        invalid_responses = (
            ("not-json-sensitive-text", "invalid JSON"),
            ("[]", "JSON object"),
            ('{"issue_flag": 0}', "missing required fields"),
            (
                json.dumps(
                    {
                        "issue_flag": True,
                        "issue_descr": "none",
                        "conf_score": 8,
                        "importance": 2,
                    }
                ),
                "must be 0 or 1",
            ),
        )

        for raw_output, expected_message in invalid_responses:
            with self.subTest(raw_output=raw_output):
                with self.assertRaisesRegex(ValueError, expected_message) as raised:
                    review.json_check(raw_output)
                self.assertNotIn("sensitive-text", str(raised.exception))


class ReviewProcessingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.chunk_dir = self.root / "chunks"
        self.review_dir = self.root / "reviews"
        self.chunk_dir.mkdir()
        self.review_dir.mkdir()
        self.paths = {
            "chunk_dir": self.chunk_dir,
            "review_dir": self.review_dir,
        }
        self.config = {"llm": {"review": "test-model"}}

    def test_review_chunks_warns_and_returns_zero_counts_when_empty(self):
        with self.assertLogs("ai_review.review", level="WARNING") as logs:
            counts = review.review_chunks(self.config, self.paths)

        self.assertEqual(
            counts, {"attempted": 0, "succeeded": 0, "skipped": 0, "failed": 0}
        )
        self.assertIn("No text chunks found", "\n".join(logs.output))

    def test_review_chunks_continues_after_expected_failure(self):
        first_chunk = self.chunk_dir / "a_chunk_000.txt"
        second_chunk = self.chunk_dir / "b_chunk_000.txt"
        first_chunk.touch()
        second_chunk.touch()

        with (
            patch(
                "ai_review.review.review_single_chunk",
                side_effect=[OSError("unreadable"), None],
            ) as review_one,
            self.assertLogs("ai_review.review", level="ERROR") as logs,
        ):
            counts = review.review_chunks(self.config, self.paths)

        self.assertEqual(
            counts, {"attempted": 2, "succeeded": 1, "skipped": 0, "failed": 1}
        )
        self.assertEqual(review_one.call_count, 2)
        self.assertIn(first_chunk.name, "\n".join(logs.output))

    def test_single_analysis_translates_connection_error_without_response_data(self):
        class FakeConnectionError(Exception):
            pass

        client = Mock()
        client.responses.create.side_effect = FakeConnectionError("secret response")
        config = {
            "llm_api_key": "secret key",
            "llm_url": "http://example.test",
            "llm_timeout": 1,
            "llm_retries": 0,
            "llm": {"review": "test-model"},
        }

        with (
            patch("ai_review.review.OpenAI", return_value=client),
            patch.object(review.openai, "APIConnectionError", FakeConnectionError),
            self.assertRaisesRegex(
                review.ReviewRequestError, "connection failed"
            ) as raised,
        ):
            review.single_analysis(
                config,
                Path("report_chunk_000.txt"),
                "sensitive chunk text",
                "sensitive prompt",
            )

        self.assertNotIn("secret", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
