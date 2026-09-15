# Setup

## Purpose

WebFIRE Review is a Python 3.12.13 pipeline that retrieves EPA WebFIRE reports,
extracts and OCRs them, sends text chunks to a local OpenAI-compatible model,
and writes review JSON plus a CSV summary.

## Prerequisites

- macOS, Conda, and network access to the public WebFIRE service.
- Python 3.12.13, supplied by `config/environment.yml`.
- Tesseract installed separately and available on `PATH` for OCRmyPDF.
- A local OpenAI-compatible LLM service listening at the configured URL. The
	current default is `http://localhost:11436/v1`.
- Read/write access to the repository's `data/` directory.

`python-magic` may also require the macOS `libmagic` installation. No paid
external service is required by the checked-in configuration.

## Repository Setup

Clone or copy the repository, open its root folder in VS Code, and run commands
from that root. Project-root discovery looks for `README.md`, and all paths in
`config/settings.yml` are relative to the repository root.

## Virtual Environment

From the repository root:

```bash
conda env create -f config/environment.yml
conda activate webfire_review
python --version
```

The expected Python version is `3.12.13`. To update an existing environment
after the YAML changes, use:

```bash
conda env update -n webfire_review -f config/environment.yml --prune
```

## Dependencies and External Tools

The Conda file installs the Python dependencies, including OCRmyPDF, PDF and
spreadsheet parsers, pandas, PyYAML, Pydantic, OpenAI, spaCy, and Streamlit.
Install and verify Tesseract separately:

```bash
brew install tesseract
which tesseract
tesseract --version
```

The review stage does not start an LLM server. Start the local service expected
by `llm_url` and make sure the configured review model is available before a
full run.

## Configuration

Review [config/settings.yml](../../config/settings.yml) before running:

- `remove_data`: currently `'True'`. Startup deletes files and directories
	under `data/` on each run, while preserving `data/logs/`. Set it to `false`
	when previous outputs must be retained.
- `states`: currently `KS`, `MO`, `NE`, and `IA`.
- `last_run_timestamp` and `default_interval_days`: control the WebFIRE search
	window. With a null timestamp, the default window is 45 days.
- `llm_url`, `llm_api_key`, and `llm.review`: identify the local model service.
	Replace the checked-in placeholder API key locally; do not commit a real
	credential.
- `chunk_size`, `chunk_overlap`, `chunk_cap`, and `audit_chance`: control review
	volume and sampling.

Prompt text is stored in [config/prompts.yml](../../config/prompts.yml).
There is no separate `.env` or `requirements.txt` file.

## Initial Folder Setup

No manual data-folder setup is required. Startup creates the configured
directories under `data/`, including:

`raw/`, `http/`, `pdfs/`, `spreadsheets/`, `other/`, `chunks/`, `reviews/`,
`summary_report/`, `audits/`, `evals/`, and `logs/`.

The pipeline uses `data/http/report_table.csv` as its metadata handoff. Input
reports are downloaded to `data/raw/`; routed and processed files remain in the
other data directories.

## First Run

1. Activate `webfire_review` and verify Tesseract and the local LLM service.
2. Set `remove_data: false` if existing data must survive the run.
3. From the repository root, run:

	 ```bash
	 python src/main.py
	 ```

The orchestrator initializes directories, retrieves and routes reports, OCRs
PDFs, creates chunks, performs model reviews, runs the current audit-stage
placeholder, and compiles the summary. A successful implemented run produces
report metadata under `data/http/`, review JSON under `data/reviews/`, and
`data/summary_report/summary_report.csv`, with logs in
`data/logs/webfire_review.log`.

The audit stage is currently a placeholder and does not produce audit result
files. The retrieval timer also does not automatically persist a new
`last_run_timestamp`.

## Verification

Run the test suite from the repository root:

```bash
python -m unittest discover -s tests
```

For a basic environment check:

```bash
python -c "import yaml, openai, ocrmypdf, pandas; print('Python dependencies import successfully')"
```

Before a full retrieval run, confirm that `config/settings.yml` loads, the
configured endpoint is reachable, and the `data/` directory is writable.

## Common Setup Issues

- **`ModuleNotFoundError`**: activate `webfire_review` or select that Conda
	interpreter in VS Code.
- **Tesseract/OCR errors**: install Tesseract and confirm `which tesseract`
	returns a path.
- **LLM connection errors**: start the local OpenAI-compatible service, check
	`llm_url`, and verify the configured model name and API key.
- **Unexpected data loss**: set `remove_data: false` before running when
	existing outputs are needed.
- **WebFIRE retrieval failures**: confirm network access and inspect the
	per-run log plus `data/http/` response files.
- **Path/configuration errors**: keep configured directory paths relative and
	inside the repository; startup rejects absolute or escaping paths.
