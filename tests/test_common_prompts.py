import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import openai

from common import prompts


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.config_dir = self.root / "config"
        self.chunk_dir = self.root / "chunks"
        self.http_dir = self.root / "http"
        self.config_dir.mkdir()
        self.chunk_dir.mkdir()
        self.http_dir.mkdir()
        self.paths = {
            "config_dir": self.config_dir,
            "chunk_dir": self.chunk_dir,
            "http_dir": self.http_dir,
        }
        self.config = {
            "llm_api_key": "test",
            "llm_url": "http://localhost/v1",
            "llm_timeout": 1,
            "llm_retries": 0,
            "llm": {"review": "test-model"},
        }

    def write_prompt_bank(self, content):
        (self.config_dir / "prompts.yml").write_text(content, encoding="utf-8")

    def test_check_model_response_marks_only_invalid_output_as_fallback(self):
        valid = prompts.check_model_response("generic", {"generic", "stack_test"})
        invalid = prompts.check_model_response("unknown", {"generic", "stack_test"})

        self.assertEqual(valid, prompts.PromptSelection("generic", False))
        self.assertEqual(invalid, prompts.PromptSelection("generic", True))

    def test_choose_prompt_wraps_openai_failures_with_chunk_context(self):
        request = httpx.Request("POST", "http://localhost/v1/responses")
        response_429 = httpx.Response(429, request=request)
        response_500 = httpx.Response(500, request=request)
        failures = (
            openai.APIConnectionError(request=request),
            openai.RateLimitError("limited", response=response_429, body=None),
            openai.APIStatusError("failed", response=response_500, body=None),
        )
        chunk_path = self.chunk_dir / "report_chunk_000.json"

        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                client = Mock()
                client.responses.create.side_effect = failure
                with (
                    patch("common.prompts.OpenAI", return_value=client),
                    self.assertRaisesRegex(
                        prompts.PromptSelectionError, str(chunk_path)
                    ) as raised,
                ):
                    prompts.choose_prompt(
                        self.config, "instructions", "chunk", chunk_path
                    )
                self.assertIs(raised.exception.__cause__, failure)

    def test_choose_system_prompt_does_not_treat_api_failure_as_model_output(self):
        self.write_prompt_bank(
            "selection: Choose one\nreview_desc:\n  generic: Other reports\n"
        )
        chunk_path = self.chunk_dir / "report_chunk_000.json"
        chunk_path.write_text("content", encoding="utf-8")

        with (
            patch(
                "common.prompts.choose_prompt",
                side_effect=prompts.PromptSelectionError("offline"),
            ),
            patch("common.prompts.check_model_response") as check_response,
            self.assertRaises(prompts.PromptSelectionError),
        ):
            prompts.choose_system_prompt(chunk_path, self.config, self.paths)

        check_response.assert_not_called()

    def test_select_prompts_continues_after_recoverable_failure_and_logs_totals(self):
        chunks = [
            self.chunk_dir / "failed_chunk_000.json",
            self.chunk_dir / "valid_chunk_000.json",
            self.chunk_dir / "fallback_chunk_000.json",
            self.chunk_dir / "ignored_chunk_001.json",
        ]
        selections = [
            prompts.PromptSelectionError("offline"),
            prompts.PromptSelection("stack_test"),
            prompts.PromptSelection("generic", used_fallback=True),
        ]

        with (
            patch("common.prompts.list_chunks", return_value=chunks),
            patch("common.prompts.choose_system_prompt", side_effect=selections),
            patch("common.prompts.save_to_table") as save_to_table,
            self.assertLogs("common.prompts", level="INFO") as logs,
        ):
            prompts.select_prompts(self.config, self.paths)

        self.assertEqual(save_to_table.call_count, 2)
        save_to_table.assert_any_call(chunks[1], "stack_test", self.http_dir)
        save_to_table.assert_any_call(chunks[2], "generic", self.http_dir)
        output = "\n".join(logs.output)
        self.assertIn(str(chunks[0]), output)
        self.assertIn("selected=1, defaulted=1, failed=1", output)

    def test_select_prompts_propagates_fatal_loading_errors(self):
        chunk_path = self.chunk_dir / "report_chunk_000.json"
        error = prompts.PromptLoadError("bad prompt bank")

        with (
            patch("common.prompts.list_chunks", return_value=[chunk_path]),
            patch("common.prompts.choose_system_prompt", side_effect=error),
            patch("common.prompts.save_to_table") as save_to_table,
            self.assertRaises(prompts.PromptLoadError),
        ):
            prompts.select_prompts(self.config, self.paths)

        save_to_table.assert_not_called()

    def test_load_system_prompt_reports_file_yaml_and_key_context(self):
        prompt_path = self.config_dir / "prompts.yml"
        with self.assertRaisesRegex(prompts.PromptLoadError, str(prompt_path)):
            prompts.load_system_prompt(self.paths, "selection")

        self.write_prompt_bank("selection: [unterminated")
        with self.assertRaisesRegex(prompts.PromptLoadError, str(prompt_path)):
            prompts.load_system_prompt(self.paths, "selection")

        self.write_prompt_bank("generic: review\n")
        with self.assertRaisesRegex(
            prompts.PromptLoadError, "Prompt 'selection'.*prompts.yml"
        ):
            prompts.load_system_prompt(self.paths, "selection")

    def test_choose_system_prompt_reports_invalid_entry_and_missing_chunk(self):
        chunk_path = self.chunk_dir / "report_chunk_000.json"
        chunk_path.write_text("content", encoding="utf-8")
        self.write_prompt_bank("selection: []\nreview_desc:\n  generic: Other\n")

        with self.assertRaisesRegex(prompts.PromptLoadError, "selection.*must be text"):
            prompts.choose_system_prompt(chunk_path, self.config, self.paths)

        self.write_prompt_bank(
            "selection: Choose one\nreview_desc:\n  generic: Other\n"
        )
        missing_chunk = self.chunk_dir / "missing_chunk_000.json"
        with self.assertRaisesRegex(prompts.PromptLoadError, str(missing_chunk)):
            prompts.choose_system_prompt(missing_chunk, self.config, self.paths)


if __name__ == "__main__":
    unittest.main()
