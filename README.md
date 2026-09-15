# WebFIRE Review Automation Pipeline

## Overview

WebFIRE Review is a Python MVP for retrieving Clean Air Act compliance reports from the EPA WebFIRE database, preparing them for analysis, reviewing report chunks with an OpenAI-compatible local open-weight language model, and compiling the results for EPA enforcement staff review.

The project is intended to evaluate the capability of LLMs for use in bulk environmental-report review. Results are exploratory and require human verification.

## Current Workflow

The end-to-end entry point is `src/main.py`. It currently:

1. Retrieves reports for the configured states and date range from WebFIRE.
2. Extracts downloaded archives and routes files into PDF and spreadsheet inputs.
3. Applies OCR to PDFs.
4. Chunks OCR text and spreadsheet content using the configured size, overlap, and per-document cap.
5. Selects a review prompt and sends each chunk to the configured review model.
6. Validates each model response and writes one JSON result per reviewed chunk.
7. Compiles review JSON files into `data/summary_report/summary_report.csv`.

The current audit pipeline is reserved for future implementation. It is wired into `src/main.py`, but does not yet perform a second-model audit. Regulatory retrieval through eCFR sub-agents, scheduled triggers, and a user interface are also not part of the current entry-point workflow, but planned future expansions.

## Setup

Requirements:

- Conda, with Python 3.12.13 as pinned in `config/environment.yml`
- The dependencies installed by `config/environment.yml`, including `ocrmypdf`, PDF and image-processing libraries, `pandas`, `openpyxl`, `numpy`, `torch`, and the `openai` client
- Tesseract, required by `ocrmypdf`
- Network access to WebFIRE
- An OpenAI-compatible LLM endpoint for review requests

Create the environment from the repository root:

```bash
conda env create -f config/environment.yml
conda activate webfire_review
```

The environment includes OCR and document-processing packages (`ocrmypdf`, `pdfplumber`, `pdfminer-six`, `pikepdf`, `pypdfium2`, `img2pdf`, and `pillow`), web and configuration packages, the `openai` client, and data/reporting packages including `pandas`, `openpyxl`, `numpy`, and `fpdf2`.

## Configuration

Runtime settings are in `config/settings.yml`; review prompts are in `config/prompts.yml`. Important settings include:

- `states`, WebFIRE endpoint, download timeout/retry settings, and download worker count
- OCR worker count and renderer
- Chunk size, overlap, chunk cap, and the percentage of non-flagged chunks selected for future auditing
- Review and audit model names, OpenAI-compatible `llm_url`, API key, timeout, and retry count
- `remove_data`, which defaults to `'True'` and cleans generated data before a run while preserving logs

Review models are accessed through the configured OpenAI-compatible endpoint. The default endpoint is `http://localhost:11436/v1`; make sure the endpoint is running and the model names in `settings.yml` are available before starting a full run.

## Run

From the repository root, with the Conda environment active:

```bash
python src/main.py
```

Generated files are organized under `data/`, including raw downloads, PDFs, spreadsheets, chunks, per-chunk reviews, logs, and the compiled summary CSV. Set `remove_data` to `False` when preserving existing generated data is required.

## Project Layout

- `src/retrieve/`: WebFIRE downloads, archive extraction, file routing, and OCR
- `src/review/`: PDF/spreadsheet chunking, prompt selection, and LLM review
- `src/audit/`: audit-stage integration point; currently a placeholder
- `src/summarize/`: review JSON compilation into CSV
- `src/common/`: configuration, path initialization, logging, and prompts
- `config/`: runtime settings and prompt definitions
- `data/`: generated inputs, intermediate files, logs, and outputs
- `tests/`: unit tests for the implemented components
