# WebFIRE Review Automation Pipeline

## Overview

This automation pipeline pulls multiple Clean Air Act reports from EPA's public WebFIRE database, reviews the reports for potential deviations, and compiles the findings into a summary for enforcement staff review.

This pipeline is intended to be used to explore the viability of using a combination of scripting, deterministic natural language processing, and large language models to review environmental reports in bulk. Capabilities will be evaluated using human reviewed data sets, success metrics, and a testing harness.

## Main Workflow

- Automated trigger
- Reports pull via WebFIRE
- Documents are sorted based on file type and content
- PDFs are OCR'd
- Standardized reporting spreadsheets are scraped via python for reported deviations/violations/excess emissions
- Unstructured reports are separated into chunks via scripting to manage LLM context buildup
- A report review prompt is selected based on the report type
- The report chunk and prompt are sent to a reviewer LLM for report review
- The reviewer LLM can call sub-agents to retreive relevant regulatory information from the eCFR
- Sub-agents use the eCFR API to pull data, summarize the relevant portions, and feed it back into the reviewer LLM
- The reviewer LLM outputs a structured JSON with review results for each chunk
- An auditor LLM reviews each chunk with a deviation flag and as well as an adjustable percentage of reports without deviation flags
- Review JSONs are aggregated in a report so that users can easily find the source document and investigate

## Requirements

- Python 3.12 (environment is pinned to `python=3.12.13`)
- Conda (recommended) to create and manage the `webfire_review` environment from `config/environment.yml`
- Core Python packages are installed through the environment file, including:
  - Document parsing and OCR pipeline: `ocrmypdf`, `pdfplumber`, `pdfminer-six`, `pikepdf`, `pypdfium2`, `img2pdf`, `pillow`
  - Web and content parsing: `requests`, `beautifulsoup4`, `lxml`
  - Data/config and validation: `pyyaml`, `pydantic`
  - Reporting/output support: `fpdf2`, `rich`
- External tools/services:
  - No paid external service is required by the environment definition
  - `ocrmypdf` requires Tesseract
- Access and permissions:
  - Read/write access to project data folders (for example, `data/raw`)
  - Network access is needed for document retrieval steps
