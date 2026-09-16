# WebFIRE Review Automation Pipeline

## Overview

WebFIRE Review is a pipeline for retrieving Clean Air Act compliance reports from the EPA public facing WebFIRE database, preparing them for analysis, reviewing chunked reports with locally run open-weight large language models, and compiling the results for US EPA enforcement staff review.

The project is intended to evaluate the capability of scripting and LLMs for use in bulk document processing as a function of setup effort.

## Current Workflow

The main entry point is `src/main.py`. It currently:

1. Retrieves reports for the configured states and date range from WebFIRE.
2. Extracts downloaded archives and routes files into PDF and spreadsheet directories.
3. Applies OCR to PDFs, if needed.
4. Chunks OCR text and spreadsheet content using the configured size, overlap, and per-document cap.
5. Selects a review prompt based on report type and sends each chunk to the configured review model.
6. Validates each model response and writes one JSON result per reviewed chunk.
7. Compiles review JSON files into `data/summary_report/summary_report.csv`.

The current audit pipeline is currently only a placeholder for future implementation. It is wired into `src/main.py`, but does not yet perform a second-model audit. A regulatory text retrieval tool and scheduled triggers are also not part of the current entry-point workflow, but potential future additionss.

## Setup

Requirements:

- Conda
- The dependencies installed by `config/environment.yml`
- Network access to WebFIRE
- An OpenAI-compatible LLM endpoint for review requests

Runtime settings are in `config/settings.yml`; review prompts are in `config/prompts.yml`.

## Project Layout

- `src/retrieve/`: WebFIRE downloads, archive extraction, file routing, and OCR
- `src/review/`: PDF/spreadsheet chunking, prompt selection, and LLM review
- `src/audit/`: audit-stage integration point; currently a placeholder
- `src/summarize/`: review JSON compilation into CSV
- `src/common/`: configuration, path initialization, logging, and prompts
- `config/`: runtime settings and prompt definitions
- `data/`: generated inputs, intermediate files, logs, and outputs
- `tests/`: unit tests for the implemented components
