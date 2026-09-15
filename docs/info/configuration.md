# Configuration

## Purpose

Runtime settings are kept in YAML so retrieval, OCR, review, logging, and data paths can be changed without editing Python code. The application loads `config/settings.yml` from the project root during startup. Prompt text and prompt-selection descriptions are kept separately in `config/prompts.yml`.

## Configuration Files

### `config/settings.yml`

Controls the complete pipeline:

- cleanup behavior and rotating logs
- project data directories
- WebFIRE retrieval dates, states, timeouts, retries, and workers
- OCR resource settings
- LLM models, endpoint, timeout, and retries
- chunk sizing and audit sampling

### `config/prompts.yml`

Contains the reviewer prompt bank. The active review prompts are `review.generic` and `review.stack_test`. `review_desc` provides the descriptions used when selecting a prompt for a chunk. The `audit` and `json` entries are present for future audit/revision workflows.

### `config/environment.yml`

Defines the Conda environment `webfire_review`, pinned to Python 3.12.13, and installs the Python dependencies used by the project. It is an environment specification, not runtime application configuration.

## Environment Setup

Create the environment from the project root:

```bash
conda env create -f config/environment.yml
conda activate webfire_review
```

The environment includes `ocrmypdf`, `pdfplumber`, `pandas`, `openpyxl`, `PyYAML`, `python-magic`, `spacy`, `en-core-web-trf`, `openai`, and the other pipeline dependencies. `ocrmypdf` also requires the external Tesseract executable. Install Tesseract through the operating system package manager and confirm it is available on `PATH` before running OCR. File-type detection through `python-magic` may also require the platform's `libmagic` installation.

The current LLM configuration expects an OpenAI-compatible service at `http://localhost:11436/v1`. Set `llm_api_key` to the credential accepted by that service. The checked-in value is a placeholder-style local value; do not place a real credential in a committed settings file. There are no email or notification credentials configured by this project.

The full pipeline is started with:

```bash
python src/main.py
```

Run from the repository root so project-root discovery and the relative paths in `settings.yml` resolve correctly.

## Folder and Path Settings

All entries under `directories` are paths relative to the project root. The current defaults are:

| Setting | Default | Use |
| --- | --- | --- |
| `config_dir` | `config` | YAML configuration files |
| `log_dir` | `data/logs` | `webfire_review.log` and rotated logs |
| `audit_dir` | `data/audits` | Reserved for audit artifacts |
| `eval_dir` | `data/evals` | Evaluation data |
| `http_dir` | `data/http` | Search HTML and report CSV files |
| `other_dir` | `data/other` | Files that are not PDF or spreadsheet MIME types |
| `pdf_dir` | `data/pdfs` | Routed PDF files before OCR/chunking |
| `raw_data_dir` | `data/raw` | Downloaded files before extraction/routing |
| `review_dir` | `data/reviews` | Per-chunk review JSON files |
| `spreadsheet_dir` | `data/spreadsheets` | Routed `.xls` and `.xlsx` files |
| `summary_dir` | `data/summary_report` | Compiled summary CSV |
| `chunk_dir` | `data/chunks` | Text chunks sent for review |

Directories are created automatically. `log_dir` must be inside `data`; all configured paths must be relative and remain inside the project root.

## Pipeline Settings

### Cleanup and logging

```yaml
remove_data: 'True'
logging:
	level: 'INFO'
	max_bytes: 5000000
	backup_count: 3
```

`remove_data` is a destructive run setting. When true, startup removes files and subdirectories under `data/` except the configured log directory, then recreates the configured directories. Use `false` to preserve prior pipeline outputs. The accepted values are YAML booleans or the strings `true`/`false` (case-insensitive). Logging supports `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`; the log file rotates at approximately 5 MB and retains three backups by default.

### Retrieval

```yaml
last_run_timestamp: null
default_interval_days: 45
http_endpoints:
	webfire: 'https://cfpub.epa.gov/webfire'
http_timeout_seconds: 30
download_retry_attempts: 5
download_retry_delay_seconds: 2
download_workers: 4
states:
	- name: 'KS'
	- name: 'MO'
	- name: 'NE'
	- name: 'IA'
```

The retrieval window ends at the current UTC date. With `last_run_timestamp: null`, it starts `default_interval_days` before the current date. Otherwise the stored timestamp is used as the start date and is converted to `MM/DD/YYYY` for WebFIRE requests. The current code does not automatically persist a new timestamp after a run, so update `last_run_timestamp` deliberately if incremental retrieval is required. Each state is searched and its results are written under `http_dir`; downloaded files are written under `raw_data_dir`.

`http_timeout_seconds`, `download_retry_attempts`, `download_retry_delay_seconds`, and `download_workers` control request timing and concurrency. The WebFIRE endpoint is public, but retrieval requires network access.

### OCR and review

```yaml
ocr_jobs_per_file: 4
ocr_pdf_renderer: 'sandwich'
chunk_size: 4000
chunk_overlap: 300
chunk_cap: 10
audit_chance: 10
```

OCR processes every PDF in `pdf_dir` in place using OCRmyPDF. `ocr_jobs_per_file` controls OCRmyPDF parallelism per file. The `sandwich` renderer preserves an image layer with searchable text and is the current project default.

PDF text is split into overlapping word-based chunks. `chunk_size` and `chunk_overlap` are measured in words; `chunk_overlap` must be smaller than `chunk_size`. `chunk_cap` limits the number of chunks per document; set it to `null` for no cap. The current settings process at most ten chunks per document. Spreadsheet files are converted into reviewable text by the spreadsheet chunking code.

`audit_chance` is an integer percentage. Every review with `issue_flag: 1` receives `audit_flag: true`; other reviews are sampled at this percentage. The audit pipeline is currently a placeholder, so this flag is recorded in review JSON but does not currently cause a second-model audit to run.

### LLM service

```yaml
llm:
	review: 'gemma-4-26b-a4b-it-qat-6bit'
	audit: 'gemma-4-31B-it-qat-6bit'
llm_url: 'http://localhost:11436/v1'
llm_api_key: 'secret_api_key'
llm_timeout: 600
llm_retries: 3
```

The review stage uses `llm.review` through the OpenAI-compatible `llm_url`. `llm_timeout` is in seconds and `llm_retries` controls client retries for requests. `llm.audit` is reserved for the planned audit stage and is not currently used by `src/audit/pipeline.py`.

## Feature Toggles and Workflow Stages

There is no single `enabled`/`disabled` feature-toggle section. `src/main.py` always runs the stages in this order:

1. initialize configuration, logging, and directories
2. retrieve WebFIRE reports
3. extract archives and route files by MIME type
4. OCR PDFs
5. chunk PDFs and spreadsheets
6. select prompts and run LLM reviews
7. run the audit stage placeholder
8. compile review JSON into a summary CSV

To run an individual stage for troubleshooting, invoke its module or function with an initialized configuration and paths. The settings file controls stage behavior; it does not currently turn stages on or off.

## File Naming and Routing Rules

Downloaded filenames come from the HTTP `Content-Disposition` header when available. Unsafe filename characters are replaced with underscores. Existing names are preserved and collisions receive suffixes such as `_1`, `_copy`, or `_copy2`, depending on the operation.

ZIP files in `raw_data_dir` are extracted repeatedly, including nested ZIP files. Extracted files are flattened into the raw directory, and `report_table.csv` receives a pipe-separated `Document List` for ZIP contents. MIME detection routes files as follows:

- `application/pdf` -> `pdf_dir`
- Microsoft Excel MIME types -> `spreadsheet_dir`
- everything else -> `other_dir`

PDF chunks use names such as `report_name_chunk_000.txt`. Review results use the matching `.json` name in `review_dir`, and the source document is resolved from `data/http/report_table.csv` where possible.

## Output Settings

- Search pages: `data/http/results_<STATE>.html`
- State report tables: `data/http/<STATE>_report_table.csv`
- Consolidated document metadata: `data/http/report_table.csv`
- Raw downloads: `data/raw/`
- Routed PDFs: `data/pdfs/`
- Routed spreadsheets: `data/spreadsheets/`
- Review chunks: `data/chunks/*.txt`
- Review results: `data/reviews/*.json`
- Compiled report: `data/summary_report/summary_report.csv`
- Logs: `data/logs/webfire_review.log` and rotated backups

The summary compiler skips invalid review JSON files, writes the fields collected from valid files, and logs the number skipped. Email delivery and automatic archive/backup destinations are not configured.

## Validation and Safety Checks

Startup validates that the YAML root is a mapping, every configured directory is a non-empty relative path inside the project root, and `log_dir` is inside `data`. Invalid logging levels and invalid `remove_data` values raise errors before the pipeline proceeds. Chunk settings are validated so sizes are positive, overlap is non-negative and smaller than the chunk size, and a cap is either positive or `null`.

The review response is parsed as JSON and must contain `issue_flag`, `issue_descr`, `conf_score`, and `importance`. `issue_flag` must be `0` or `1`; the two scores must be numbers from `0` through `10`. Malformed responses raise a review error rather than being silently written as valid results.

Before changing directory settings, confirm that `remove_data` is false or that the configured `data` tree can safely be rebuilt. Do not use absolute paths or paths outside the repository; startup rejects them.

## Example Configuration

This is a small, safer local override pattern for development:

```yaml
remove_data: false
logging:
	level: DEBUG
directories:
	log_dir: data/logs
	raw_data_dir: data/raw
	review_dir: data/reviews
	summary_dir: data/summary_report
last_run_timestamp: null
default_interval_days: 7
chunk_cap: 2
llm_url: http://localhost:11436/v1
llm_api_key: replace-with-a-local-secret
```

If the full pipeline is used, retain all directory keys required by the stages or add them to this example. In particular, `log_dir` is mandatory and must remain under `data`.

## Maintenance Notes

- When adding or moving a data directory, update `directories` and any code that accesses its key. Startup creates configured directories automatically.
- When adding a setting, document its type, units, default, and consuming stage in this file, then add validation and tests where the value affects safety or data integrity.
- Keep `environment.yml` aligned with imports and external executables. Tesseract and `libmagic` are system prerequisites and are not fully installed by the YAML file.
- Keep prompt names in `prompts.yml`, prompt-selection descriptions, and any report metadata values synchronized. An unknown review prompt falls back to `generic`.
- Update `last_run_timestamp` only after confirming the retrieval results were successful; the current code does not manage that value automatically.
- Review the audit settings and this document when `src/audit/pipeline.py` is implemented so the documented audit model and outputs match the actual workflow.
