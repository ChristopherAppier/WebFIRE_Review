# Architecture

## Purpose

- Explain how the WebFIRE Deviation Scanner is organized
- Describe how the major scripts and folders work together
- Show how data moves through the system from input to final report

## Overview

- High-level description of the full workflow
- Main system parts and what each part is responsible for
- Short explanation of why the project is split into retrieval, review, validation, and reporting stages

## Main Pipeline Stages

- Document Retrieval and Routing
  - Timer trigger
  - Last-run timestamp check
  - Pull request creation
  - Downloading reports
  - Extraction from zip/database structure
  - OCR processing
  - File routing by document type
  - Renaming of non-spreadsheets

- Spreadsheet Review
  - Scan for deviation or excess-emission flags
  - Write compliance results to JSON
  - Write scan statistics to JSON

- PDF Review
  - PDF chunking
  - AI-based chunk review
  - JSON output creation
  - Random audit sampling for compliant cases
  - Live auditor routing for non-compliant cases

- Summary Reporting
  - Compile JSON outputs
  - Generate human-readable spreadsheets
  - Build further review spreadsheet
  - Prepare email summary and links

- Accuracy Oversight Workflows
  - Live AI auditor for non-compliance flags
  - Random AI auditor for compliance determinations
  - Random Python auditor for spreadsheet reviews
  - Accuracy threshold handling and escalation

## Folder / Module Structure

- `document_retrieval`
  - Main retrieval entry point
  - Download, extraction, OCR, timer, and file routing helpers

- `file_rename`
  - File renaming workflow and naming standardization

- `llm_review`
  - AI-based PDF review workflow
  - Chunk handling, analysis, and JSON compilation

- `python_review`
  - Python-based spreadsheet review workflow

- `llm_audit`
  - AI audit review entry points and related logic

- `sub_agents`
  - Supporting agent workflows or shared review automation

- `summary_report`
  - Final report generation and email packaging

- `validate`
  - Validation workflow and checks

## Data Flow

- Source reports are discovered and retrieved
- Files are extracted and routed by type
- PDFs are OCR’d and chunked when needed
- Spreadsheet and PDF reviews generate structured JSON outputs
- Audit workflows consume selected review outputs
- Summary reporting compiles all JSON results into spreadsheets and email-ready outputs
- Final QA and audit information is delivered to staff or workflow managers

## Component Interactions

- Retrieval output feeds file routing and downstream review
- Renaming standardizes files before review
- OCR output feeds PDF chunking and AI review
- Review JSON feeds reporting and audit workflows
- Audit results feed final summary materials
- Validation checks can run alongside or after review stages

## Key Design Decisions

- Use separate workflows for spreadsheets and PDFs because their processing methods differ
- Use JSON as the intermediate format between stages for consistency
- Use AI for text-heavy PDF review and human/auditor oversight for accuracy
- Save some compliant cases for random audit sampling to monitor quality
- Keep summary reporting separate from review logic so reporting can change without rewriting analysis code

## Dependencies

- Retrieval must happen before review
- OCR must happen before chunking and PDF AI review
- Review must happen before audits and summary reporting
- Audit outputs depend on the main review outputs
- Reporting depends on the full set of review and audit JSON files

## Limitations

- OCR quality may affect downstream review accuracy
- AI review may miss edge cases or interpret text inconsistently
- Hard-coded spreadsheet logic may require maintenance when formats change
- Audit sampling only covers a subset of compliant determinations
- Accuracy thresholds and escalation rules still need final tuning
- Workflow reliability depends on source file structure and consistent naming

############### ^^^^ Use these sections to complete this doc ^^^^ ###################

WebFIRE Deviation Scanner Workflow

Main Workflow
Document Retrieval and Routing (Python)

- Automated timer triggers the script to run
- Check last run timestamp
- Create Pull request for all reports since last timestamp
- Download all reports returned
- Extract documents from zip/database structure
- OCR all PDFs (if needed)
- Split route based on PDF vs spreadsheet
- Standardized renaming of all non-spreadsheets based on content (AI)

Spreadsheet Review (Python) - Loop

- Scan for deviation / excess emission flags
- Output all compliance info to JSON
- Output all scan stats to JSON

PDF Review (AI + Python) - Loop

- PDF chunking (python)
- PDF chunk review w document content specific instructions and summary output as JSON (AI)
- Save X% of reviews marked as in compliance to audit folder
- Send all reviews marked as out of compliance to Live Auditor workflow
- Output all compliance info to JSON
- Output all scan stats to JSON

Summary Reporting (Python)

- Compiles all JSONs into human readable spreadsheets
- Packages the Further Review Spreadsheet into an email summary with the spreadsheet linked
- Includes links to further information for QA reviews (auditor information, etc.)

Accuracy Oversight Workflows
Live AI Auditor (Non-compliance Flag Audit)

- When compliance issue is flagged by the standard AI workflow, an auditor AI agent is passed the information that was used to create the flag and the output JSON. The auditor scrutinizes the review to ensure that it is correct
- Increases confidence in reports flagged for further review by humans (save time)
- This live auditor is used to review all non-compliance flags
- The results of the live auditor’s review will be presented alongside the compliance summary spreadsheet in the emails to staff

Random AI Auditor (Compliance Flag Audit)

- X% of the compliance determinations made (only in compliance determinations) by the AI in the standard workflows will save their information reviewed and output JSON to a random auditor folder that will run after the main workflow.
- The random auditor agent will scrutinize the work of the main workflow AI agents and create a report on their accuracy
- This random auditor is used to review X% of all compliance flags
- The results of the random auditor’s review will be presented to workflow manager (human) when the audit is ran and will include stats.

Random Python Auditor

- X% of the spreadsheets that were reviewed via python scripts will be set aside for random AI auditor agent review
- Ensures that the python script isn’t creating unexpected errors due to its hard coded logic
- Report results to workflow manager

Poor Accuracy Handling

- If the live or random audits fall below a certain percentage (decided later), then the entire process will be reviewed and overhauled to maintain accurate checks
