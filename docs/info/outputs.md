# Pipeline Outputs

## Purpose

This document describes the outputs currently produced by the Python pipeline in
`src/main.py`. The configured output root is `data/`; directory names are defined
in `config/settings.yml`.

## Output Overview

| Stage | Location | Current output |
| --- | --- | --- |
| Retrieval | `data/http/` | Search-result HTML and CSV report tables |
| Download and extraction | `data/raw/` | Downloaded files and ZIP contents while being processed |
| File routing | `data/pdfs/`, `data/spreadsheets/`, `data/other/` | Files routed by detected MIME type |
| OCR | `data/pdfs/` | The original PDF replaced with its OCR-processed version |
| Chunking | `data/chunks/` | Plain-text PDF, spreadsheet, and XML chunks |
| LLM review | `data/reviews/` | One JSON file per reviewed chunk |
| Summary | `data/summary_report/` | `summary_report.csv` |
| Logging | `data/logs/` | Rotating `webfire_review.log` files |

The `data/audits/` and `data/evals/` directories are created during project
initialization but are not currently populated by the implemented pipeline.

## Retrieval Outputs

For each configured state, retrieval writes:

- `data/http/results_<STATE>.html`: saved WebFIRE search response.
- `data/http/<STATE>_report_table.csv`: parsed search results and download
	metadata.
- `data/http/report_table.csv`: master table combining all state tables.
- `data/raw/`: downloaded report files. Filename collisions receive `_copy`,
	`_copy2`, and similar suffixes.

The report-table columns currently include `Organization`, `Facility`, `City`,
`State`, `County`, `Submission Date`, `Report Type`, `Report Sub Type`,
`Pollutants`, `Control Devices`, `Document Name`, `Related Attachment(s)`,
`report_url`, `Downloaded Filename`, `Document List`, and `Prompt Name`.

ZIP files are extracted into `data/raw/`, including nested ZIP contents. The ZIP
archive is removed after successful extraction. `Document List` is updated with
the extracted filenames, separated by `|`, so later stages can map chunks back to
the source report.

## Routing and OCR Outputs

Files are moved from `data/raw/` based on MIME type:

- PDFs go to `data/pdfs/`.
- `.xls` and `.xlsx` MIME types go to `data/spreadsheets/`.
- All other files go to `data/other/`.

OCR runs in place on each PDF in `data/pdfs/`. It writes to a temporary PDF in
the same directory and replaces the source only after OCR succeeds. A failed OCR
attempt leaves the source PDF in place; no separate OCR text file is produced.

## Chunk Outputs

Chunking writes UTF-8 text files to `data/chunks/`:

- PDFs become overlapping files named `<source_stem>_chunk_000.txt`,
	`<source_stem>_chunk_001.txt`, and so on. `chunk_size`, `chunk_overlap`, and
	`chunk_cap` in `settings.yml` control the output.
- `.xlsx` and `.xlsm` workbooks become one `<source_stem>_chunk_000.txt` file
	containing workbook and sheet headings followed by tab-separated cell values.
- XML files found in `data/other/` become one `<source_stem>_chunk_000.txt` file
	containing readable element paths and values.

Empty or failed extractions are logged and do not create a chunk file.

## Review Outputs

The review stage writes one indented JSON object to
`data/reviews/<chunk_stem>.json` for each successful chunk review. The validated
model response must contain:

- `issue_flag`: `0` or `1`.
- `issue_descr`: description text.
- `conf_score`: numeric confidence from `0` through `10`.
- `importance`: numeric importance from `0` through `10`.

The review code adds `audit_flag`, `file_name`, `chunk_name`, facility and report
metadata, `review_start_time`, `review_end_time`, `total_review_time`,
`think_output`, and `prompt_name`. `audit_flag` indicates that a result was
selected for auditing; it is not an auditor result.

Prompt selection updates the matching `Prompt Name` cell in
`data/http/report_table.csv`. Invalid model selections fall back to `generic`.

## Audit Outputs

Audit result generation is not implemented yet. `src/audit/pipeline.py` currently
returns without writing files, and `store_for_audit` in the review module is a
placeholder. Therefore the project currently produces no live-auditor JSON,
random-auditor JSON, sampled input packages, or audit summary statistics.

## Summary Output

The summary stage reads valid JSON objects from `data/reviews/` and writes:

- `data/summary_report/summary_report.csv`

The CSV uses the union of keys found in the review JSON files as its columns.
Because field order follows the loaded review objects, new JSON fields may add
columns without a separate schema migration. There is currently no XLSX export,
further-review workbook, email summary, attachment, or link package.

## Logging and Naming

Logging writes `data/logs/webfire_review.log` with rotation controlled by
`logging.max_bytes` and `logging.backup_count`. Rotated files use the logging
handler's numeric suffixes, such as `webfire_review.log.1`.

Output filenames use source names, state names, or fixed stage names. They do not
include a run ID or timestamp. Retrieval dates are used for the WebFIRE search,
but the current timer code does not persist a new `last_run_timestamp` after a
run.

## Retention and Cleanup

Project initialization creates all configured directories and removes nested
`.gitkeep` files. With the current `remove_data: 'True'` setting, initialization
deletes files and directories under `data/` while preserving the configured
`data/logs/` directory and its existing log files. It then recreates configured
directories and `data/.gitkeep`.

Set `remove_data` to `false` to retain prior pipeline outputs between runs. There
is no separate archive or automated retention policy for reports, reviews,
chunks, summaries, audits, or evaluation artifacts.
