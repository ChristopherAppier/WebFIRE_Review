# Architecture

## Purpose

WebFIRE Review retrieves EPA WebFIRE submissions for configured states, converts the downloaded files into reviewable text, sends each text chunk to a locally hosted OpenAI-compatible model, and compiles validated model responses into a CSV summary.

The executable workflow is orchestrated by `src/main.py`. Each stage receives the same configuration mapping and `common.startup.Paths` object, which keeps filesystem layout in configuration rather than hard-coding it in the pipeline modules.

## Runtime Workflow

The top-level `main()` function runs these stages in order:

1. `common.startup.initialize_project()` loads `config/settings.yml`, resolves configured directories beneath the project root, configures console and rotating-file logging, and creates or cleans the `data` directories. `remove_data: true` removes prior data while preserving the configured log directory.
2. `retrieve.pipeline.main()` queries WebFIRE for each configured state and date range, downloads report files, extracts nested ZIP archives, routes files by MIME type, and applies OCR to PDFs.
3. `review.pipeline.main()` creates text chunks, selects a review prompt for each document, calls the review model, validates the returned JSON, and writes one JSON result per chunk.
4. `audit.pipeline.main()` is called after review, but is currently a placeholder and returns without processing anything.
5. `summarize.pipeline.main()` reads valid review JSON files and writes `data/summary_report/summary_report.csv`.

## Modules

### `src/common`

- `startup.py` defines the `Paths` object, project-root discovery, YAML configuration loading, directory initialization/cleanup, and logging setup.
- `prompts.py` calls the configured review model to select a prompt from `config/prompts.yml` using each document's first chunk. The selected name is written to the `Prompt Name` column in `data/http/report_table.csv`; invalid selections fall back to `generic`.

### `src/retrieve`

- `time.py` derives the WebFIRE search window from `last_run_timestamp` or `default_interval_days`. The current implementation reads the timestamp but does not persist a new one.
- `download.py` performs the WebFIRE search flow, saves per-state HTML and CSV metadata, downloads reports concurrently with retries, and builds the combined `report_table.csv`.
- `extract.py` repeatedly extracts nested ZIP files, flattens extracted directories, records the files associated with each archive in `Document List`, and routes PDFs, Excel workbooks, and other files to their configured directories. Name collisions receive `_copy` suffixes.
- `ocr.py` runs `ocrmypdf` through the active Python interpreter on every PDF in `data/pdfs`, replacing each source PDF only after successful processing.
- `pipeline.py` coordinates download, extraction/routing, and OCR.

### `src/review`

- `chunk.py` extracts PDF text with `pdfplumber` and writes overlapping word-based chunks. PDFs use `chunk_size`, `chunk_overlap`, and optional `chunk_cap`; spreadsheets and XML files become one text chunk per file.
- `review.py` maps chunks back to report metadata, loads the selected prompt, calls the configured OpenAI-compatible endpoint, validates required response fields, adds timing and document metadata, and writes JSON to `data/reviews`.
- `pipeline.py` orders chunking, prompt selection, and model review.

The required model response is a JSON object containing `issue_flag` (`0` or `1`), `issue_descr` (string), `conf_score` (0-10), and `importance` (0-10). Each result also includes `audit_flag`, which is true for flagged issues or for a random percentage controlled by `audit_chance`.

### `src/audit`

`pipeline.py` defines the audit-stage entry point, but `main()` is currently empty. The repository does not yet implement the downstream auditor, escalation rules, or audit output generation described in earlier project plans.

### `src/summarize`

`compile.py` reads JSON objects from `data/reviews`, skips malformed or non-object files, and writes the union of encountered keys as rows in `data/summary_report/summary_report.csv`. It does not currently merge audit results, generate additional spreadsheets, or send email.

## Data Layout

The configured directories under `data/` are:

| Directory | Role |
| --- | --- |
| `audits` | Reserved for audit artifacts; not currently populated by the audit pipeline |
| `chunks` | Extracted PDF, spreadsheet, and XML text chunks |
| `evals` | Reserved evaluation output |
| `http` | WebFIRE HTML responses, per-state tables, and master `report_table.csv` |
| `logs` | Rotating `webfire_review.log` output |
| `other` | Files that are neither PDFs nor supported Excel workbooks, including XML inputs |
| `pdfs` | Routed and OCR-processed PDFs |
| `raw` | Downloaded files and temporary archive contents before routing |
| `reviews` | One validated review JSON file per processed chunk |
| `spreadsheets` | Routed `.xlsx` and `.xlsm` workbooks |
| `summary_report` | Compiled `summary_report.csv` |

The main metadata handoff is `data/http/report_table.csv`. Retrieval populates document and facility metadata; extraction adds archive contents; prompt selection adds `Prompt Name`; review reads these fields when constructing each JSON result.

## External Services and Configuration

- WebFIRE is queried through the configured `http_endpoints.webfire` endpoint. Network access is required for retrieval.
- OCR depends on the `ocrmypdf` Python module and its Tesseract installation.
- Prompt selection and review use the OpenAI Python client against `llm_url`, with the configured review model. The configured endpoint is local (`http://localhost:11436/v1`); an API key, timeout, and retry count are still required by the client setup.
- States, date interval, download concurrency/retries, OCR settings, chunking limits, model names, and audit sampling percentage are all configured in `config/settings.yml`.

## Current Limitations and Integration Notes

- The audit stage is intentionally unimplemented, so `audit_flag` currently records sampling intent but does not cause a second model review or escalation.
- The timer calculates a start date from `last_run_timestamp`, but no code currently updates that setting after a successful run.
- The checked-in review pipeline imports `ai_review.chunk` and `ai_review.review`, while the implementation directories are named `src/review`. This package-name mismatch must be resolved for the top-level review stage and its corresponding tests to run from a clean checkout.
- Spreadsheet review is model-based text review; there is no separate deterministic spreadsheet deviation scanner in the current `src/` tree.
- OCR failures are logged and skipped, so downstream results may be incomplete without causing the entire retrieval stage to fail.