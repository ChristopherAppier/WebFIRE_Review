# WebFIRE Deviation Scanner - Implementation Plan

## Overview

This document outlines a detailed, phased implementation plan for the WebFIRE Deviation Scanner project. The plan is structured sequentially with portions sized to complete in 30-minute to 4-hour timeframes. Each portion includes a clear goal, technical steps, file modifications, testing approach, and explanation of how it fits into the overall project schema.

**Reading Guide:** Follow Phases in order. Each Phase is self-contained and builds on previous work.

---

## Project Structure

```
WebFIRE_Review/
├── planning/
│   └── implementation_plan.md
├── src/
│   ├── document_retrieval/
│   │   └── (Phase 1 implementation)
│   ├── spreadsheet_review/
│   │   └── (Phase 2 implementation)
│   ├── pdf_review/
│   │   └── (Phase 2 implementation)
│   ├── summary_reporting/
│   │   └── (Phase 3 implementation)
│   └── auditors/
│       └── (Phase 4 implementation)
├── tests/
│   └── (All unit/integration tests)
├── config/
│   └── settings.yml
└── data/
```

---

## Phase 1: Core Document Retrieval (MVP)

### Portion 1.1: Project Setup and Configuration (30 min)

**Goal:** Initialize project structure, create config file, and setup basic runner.

**Technical Steps:**

1. Create `config/settings.yml` with:
   - API endpoints for document retrieval
   - Timestamp tracking setting
   - Output directory paths
   - Audit percentage settings
2. Create `src/document_retrieval/__init__.py` with package marker
3. Create basic `src/document_retrieval/main.py` entry point that:
   - Loads config from `config/settings.yml`
   - Prints system status info
   - Has placeholder functions for the 4 workflow stages

**Files to Create/Modify:**

- `config/settings.yml`
- `src/document_retrieval/__init__.py`
- `src/document_retrieval/main.py`

**Testing:**

```python
tests/unit/test_config.py
```

**Why it fits:** Foundation setup - establishes single source of truth for environment settings.

---

### Portion 1.2: Timer System

**Objective:** Implement a time stamp based system that finds the date range to request documents in the WebFIRE API request.

**Scope:**

- Read last_run_timestamp from config on startup
- Calculate the date range for WebFIRE API calls based on:
  - last_run_timestamp (start date)
  - Current datetime (end date)
- Expose the calculated date range to download_documents() function

**Implementation Strategy:**

- Use Python's datetime module for timestamp comparisons and range calculations
- Store timestamps as ISO 8601 format strings in config (e.g., "2024-01-15T00:00:00")
- Initialize with a default timestamp (e.g., 30 days ago or a fixed date)
- Implement a check_timer() function that:
  - Reads config on entry
  - Calculates and returns the date range (last_run_date, today)

**Output:**

- check_timer() returns {"start_date": ..., "end_date": ...}
  Integration Point (Post 1.3):
- download_documents() will use the returned date range (or default range if first run) to filter WebFIRE API calls.

**Deliverable:**

1. src/document_retrieval/timer_manager.py
   - load_timestamps() → reads last_run_timestamp from config
   - get_date_range() → returns date range tuple
   - check_timer() → main entry point returning date range info

---

### Portion 1.3: Document Download Handler (1 hour)

**Goal:** Fetch documents from API/database for the selected timestamp range.

**Technical Steps:**

1. Create `src/document_retrieval/download_handler.py`:
   - API session with authentication
   - Fetch reports since timestamp
   - Download all reports to zip files
   - Handle errors and retries
2. Integrate into main workflow in `main.py`

**Files to Create/Modify:**

- `src/document_retrieval/download_handler.py`
- `src/document_retrieval/main.py` (add download chain)

**Testing:**

```python
tests/unit/test_download_handler.py
```

**Why it fits:** First major step - gets all raw data into system.

---

### Portion 1.4: Document Extraction and Pre-processing (1 hour)

**Goal:** Unzip reports, identify PDF vs spreadsheet, and route them appropriately.

**Technical Steps:**

1. Create `src/document_retrieval/extract_processor.py`:
   - Extract contents from zip files
   - Route PDFs to pdf_dir
   - Route spreadsheets to spreadsheet_dir
   - Track metadata for each file
2. Integrate extraction into main workflow

**Files to Create/Modify:**

- `src/document_retrieval/extract_processor.py`
- `src/document_retrieval/main.py`

**Testing:**

```python
tests/unit/test_extract_processor.py
```

**Why it fits:** Routing logic that separates PDF and spreadsheet workflows.

---

### Portion 1.5: OCR Integration (2 hours)

**Goal:** Add OCR for PDFs that need text extraction from images.

**Technical Steps:**

1. Install dependencies: `pytesseract`, `python-tessdata`
2. Create `src/document_retrieval/ocr_processor.py`:
   - Detect PDFs needing OCR (low text density)
   - Extract text from images
   - Process with or without OCR as needed
3. Integrate OCR into extraction flow

**Files to Create/Modify:**

- `src/document_retrieval/ocr_processor.py`
- `scripts/install_tesseract.sh`

**Testing:**

```python
tests/unit/test_ocr_processor.py
```

**Why it fits:** Handles scanned documents that would otherwise fail downstream.

---

## Phase 2: Spreadsheet and PDF Review Workflows

### Portion 2.1: Spreadsheet Scanner (2 hours)

**Goal:** Scan spreadsheets for deviation/excess emission flags and extract compliance data.

**Technical Steps:**

1. Create `src/spreadsheet_review/scanner.py`:
   - Detect deviation-related columns
   - Scan for non_compliance_flags
   - Extract deviations and compliance info
   - Output stats to JSON
2. Create `src/spreadsheet_review/json_exporter.py`
3. Integrate scanner into main workflow

**Files to Create/Modify:**

- `src/spreadsheet_review/scanner.py`
- `src/spreadsheet_review/json_exporter.py`
- `src/spreadsheet_review/__init__.py`
- `main.py` (add spreadsheet route)

**Testing:**

```python
tests/unit/test_scanner.py
```

**Why it fits:** Handles the simplest file type - feeds compliance info to summary reports.

---

### Portion 2.2: PDF Review Workflow (3 hours)

**Goal:** Chunk PDFs, send to AI for review, classify compliance, and route to audit workflows.

**Technical Steps:**

1. Create `src/pdf_review/chunker.py`:
   - Split PDFs into manageable chunks
   - Preserve page relationships
   - Save chunks as individual PDFs
2. Create `src/pdf_review/ai_processor.py`:
   - Load chunks and format for AI
   - Send to AI API for compliance classification
   - Handle streaming responses
3. Create `src/pdf_review/compliance_classifier.py`:
   - Parse AI responses
   - Classify as COMPLIANT or NON_COMPLIANT
   - Generate JSON output
4. Create `src/pdf_review/main.py` orchestrator
5. Integrate PDF workflow into main system

**Files to Create:**

- `src/pdf_review/chunker.py`
- `src/pdf_review/ai_processor.py`
- `src/pdf_review/compliance_classifier.py`
- `src/pdf_review/main.py`

**Testing:**

```python
tests/unit/test_chunker.py
tests/unit/test_ai_processor.py
tests/unit/test_compliance_classifier.py
```

**Why it fits:** Handles the complex file type - AI classification determines audit routing.

---

### Portion 2.3: Routing to Audit Workflows (1 hour)

**Goal:** Route compliant and non-compliant files to appropriate folders and workflows.

**Technical Steps:**

1. Create `src/routing/auditor_router.py`:
   - Route non-compliant to Live Auditor
   - Route compliant to Random Auditor
   - Save metadata for tracking
2. Create audit folder structure
3. Integrate routing into PDF workflow

**Files to Create:**

- `src/routing/auditor_router.py`
- `src/auditor_queue/` directory

**Testing:**

```python
tests/unit/test_auditor_router.py
```

**Why it fits:** Ensures proper separation of concerns - compliance vs non-compliance get different treatment.

---

## Phase 3: Summary Reporting

### Portion 3.1: Spreadsheet Compiler (2 hours)

**Goal:** Compile all JSON outputs from spreadsheet and PDF reviews into human-readable spreadsheets. Also updates successful run timestamping update.

**Technical Steps:**

1. Create `src/summary_reporting/spreadsheet_compiler.py`:
   - Read all JSON compliance files
   - Parse and merge compliance info
   - Generate pandas DataFrame
   - Export to Excel
2. Create 'src/summary_reporting/timestamp_updater.py':
   - Update the settings.yml last_run_timestamp
3. Integrate into main workflow

**Files to Create:**

- `src/summary_reporting/spreadsheet_compiler.py`
- `src/summary_reporting/timestamp_updater.py`

**Testing:**

```python
tests/unit/test_spreadsheet_compiler.py
```

**Why it fits:** Final output generation - produces deliverable reports for staff and marks end of a successful run.

---

### Portion 3.2: Live AI Auditor (3 hours)

**Goal:** Implement auditor AI agent that reviews all non-compliance flags before human review.

**Technical Steps:**

1. Create `src/auditors/live_ai_auditor.py`:
   - Receive non-compliance determination + context
   - Run secondary AI review
   - Cross-reference original documents
   - Output auditor confidence + findings
2. Create audit response format
3. Integrate into main workflow after non-compliance routing

**Files to Create:**

- `src/auditors/live_ai_auditor.py`
- `src/auditors/__init__.py`

**Testing:**

```python
tests/unit/test_live_ai_auditor.py
```

**Why it fits:** Increases confidence in flagged reports - saves human time by eliminating false positives.

---

### Portion 3.3: Random AI Auditor (2 hours)

**Goal:** Sample X% of compliance determinations to validate AI accuracy.

**Technical Steps:**

1. Create `src/auditors/random_ai_auditor.py`:
   - Load list of compliance determinations
   - Randomly select X% for review
   - Send to auditor AI
   - Compare auditor output with AI original
   - Calculate accuracy stats
2. Store comparison results
3. Integrate as post-workflow job

**Files to Create:**

- `src/auditors/random_ai_auditor.py`
- `src/auditor_results/` directory

**Testing:**

```python
tests/unit/test_random_ai_auditor.py
```

**Why it fits:** Validates AI model accuracy - catches systematic issues before they become problems.

---

### Portion 3.4: Random Python Auditor (2 hours)

**Goal:** Sample X% of spreadsheet reviews to validate Python logic.

**Technical Steps:**

1. Create `src/auditors/random_python_auditor.py`:
   - Load compliance summary JSON
   - Randomly select X% for re-validation
   - Run scanner again
   - Compare results
   - Detect code issues
2. Integrate as parallel audit job

**Files to Create:**

- `src/auditors/random_python_auditor.py`
- `src/auditor_results/python_audits/` directory

**Testing:**

```python
tests/unit/test_random_python_auditor.py
```

**Why it fits:** Validates Python script logic is correct, not just AI decisions.

---

### Portion 3.5: Audit Results Aggregator (1 hour)

**Goal:** Collect and present all audit results in final summary email.

**Technical Steps:**

1. Create `src/summary_reporting/audit_aggregator.py`:
   - Gather live auditor results
   - Gather random auditor results
   - Gather python auditor results
   - Calculate overall accuracy stats
   - Generate audit summary
2. Integrate into summary reporting

**Files to Create:**

- `src/summary_reporting/audit_aggregator.py`

**Testing:**

```python
tests/unit/test_audit_aggregator.py
```

**Why it fits:** Consolidates all audit work into actionable summary for managers.

---

## Phase 4: Poor Accuracy Handling

### Portion 4.1: Threshold Monitoring (1 hour)

**Goal:** Monitor audit accuracy and flag when confidence drops below threshold.

**Technical Steps:**

1. Create `src/auditors/accuracy_monitor.py`:
   - Read all auditor results
   - Calculate overall accuracy rate
   - Trigger alert if below threshold
   - Log to file

**Files to Create:**

- `src/auditors/accuracy_monitor.py`
- `config/accuracy_thresholds.yaml`

**Testing:**

```python
tests/unit/test_accuracy_monitor.py
```

**Why it fits:** Provides fail-safe mechanism for detecting model degradation.

---

### Portion 4.2: Process Overhaul Script (2 hours)

**Goal:** Create script to pause workflow, alert team, and trigger manual review.

**Technical Steps:**

1. Create `src/auditors/overhaul_trigger.py`:
   - Pause document retrieval
   - Send alert email
   - Create manual review queue
   - Log incident

**Files to Create:**

- `src/auditors/overhaul_trigger.py`
- `scripts/pause_workflow.sh`

**Testing:**

```python
tests/unit/test_overhaul_trigger.py
```

**Why it fits:** Ensures data quality is never compromised by continuing with bad model.

---

## Phase 5: Integration & Polish

### Portion 5.1: Main Workflow Orchestrator (2 hours)

**Goal:** Wire all components together and create single entry point.

**Technical Steps:**

1. Create `src/document_retrieval/main.py` final version:
   - Import all modules
   - Wire timer -> download -> extract -> OCR
   - Route to spreadsheet or PDF workflow
   - Route to auditors
   - Compile summary
   - Trigger next iteration
2. Create CLI entry point

**Files to Create/Modify:**

- `src/document_retrieval/main.py` (complete version)
- `src/main.py` CLI

**Testing:**

```python
tests/integration/test_full_workflow.py
```

**Why it fits:** Single entry point that runs the entire system.

---

### Portion 5.2: Logging and Error Handling (1 hour)

**Goal:** Add comprehensive logging and error handling throughout.

**Technical Steps:**

1. Add `logging.config.fileConfig` to main config
2. Add try/except blocks with retries
3. Create error directories
4. Add health check endpoints

**Files to Create/Modify:**

- `config/logging.yaml`
- All main.py files (add exception handling)

**Testing:**

```python
tests/unit/test_logging.py
```

**Why it fits:** Production readiness for debugging and monitoring.

---

### Portion 5.3: Performance Optimization (2 hours)

**Goal:** Optimize for speed and memory efficiency.

**Technical Steps:**

1. Batch process PDF chunks
2. Stream downloads instead of full load
3. Cache AI responses
4. Use async where beneficial

**Files to Create/Modify:**

- All processing modules (add optimization)

**Testing:**

```python
tests/performance/test_optimization.py
```

**Why it fits:** Makes system handle high volume efficiently.

---

## Testing Strategy

### Unit Tests

- One test file per module
- Test happy path and error cases
- Use pytest with mocking

### Integration Tests

- Test across workflow boundaries
- Use sample data files
- Verify end-to-end flow

### Acceptance Criteria Per Portion

- [ ] Tests pass locally
- [ ] No new warnings in output
- [ ] Handles edge cases gracefully
- [ ] Logs appropriate messages

---

## Dependencies

Install requirements before beginning:

```bash
pip install \
    requests \
    pandas \
    pymupdf \
    pytesseract \
    python-tessdata \
    openai \
    pyyaml \
    pillow
```

---

## Quick Start

Start here if new to the project:

1. Run `pip install -r requirements.txt`
2. Edit `config/settings.yml` with your API keys
3. Run `tests/` to verify setup
4. Then follow Phase 1 portions in order

---

**Note:** Always run `pip install -e .` after installing any package that adds a new Python module.
