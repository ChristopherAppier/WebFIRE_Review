# Multithread Plan

## Goal
Speed up document retrieval by adding report-level multithreading during download, while keeping pipeline behavior stable and easy to debug.

## Scope Decisions
- Include report-level threading inside each state download flow.
- Use existing `dl_threads` from config/settings.yaml as worker count.
- Keep state iteration serial in phase 1.
- Keep extraction and OCR as downstream phases after download completion.

## Implementation Steps

### 1. Define Threading Boundary
- Keep state loop in src/document_retrieval/doc_retrieval_main.py serial for now.
- Apply threading only to per-report downloads inside fetch_all_reports in src/document_retrieval/download_handler.py.
- Ensure fetch_all_reports receives worker count (from config).

### 2. Add ThreadPoolExecutor to Downloads
- In fetch_all_reports, keep report discovery serial:
  - Search once for reports for a state.
  - Build the report list.
- Replace serial download loop with ThreadPoolExecutor submission per report.
- Consume futures with as_completed for robust per-task handling.

### 3. Preserve Reliable Error Attribution
- Keep errors keyed by report/doc id.
- Separate two error classes:
  - State-level fatal errors (search/session setup failures).
  - Report-level errors (individual download failures).
- Return a structured summary per state:
  - attempted_count
  - downloaded_count
  - errors
  - success

### 4. Keep Threading Safe
- Avoid sharing one mutable requests Session across worker threads.
- Use either:
  - one session per task, or
  - thread-local session per worker.
- Avoid file write race conditions for duplicate doc ids:
  - use temp file + atomic replace, or
  - enforce safe uniqueness before write.

### 5. Main Flow Integration
- In src/document_retrieval/doc_retrieval_main.py:
  - read dl_threads from config.
  - pass worker count into fetch_all_reports.
  - collect per-state summaries for run-level reporting.
- Keep strict phase order:
  1. Download for all states
  2. Extract and route files
  3. OCR

### 6. Optional OCR Threading (Second Phase)
- After download threading is stable, add a separate OCR pool in src/document_retrieval/ocr_handler.py.
- Keep OCR threading independent from download threading.
- Use a lower worker count for OCR (CPU/disk heavier than HTTP requests).

## Verification Plan
1. Baseline run with dl_threads = 1 and record time and file counts.
2. Threaded run with dl_threads > 1 on same date range.
3. Compare runtime and downloaded counts.
4. Confirm no corrupted/partial files in raw output.
5. Confirm extraction and OCR outputs match expected behavior.
6. Force one failing report and verify error appears in per-doc errors without aborting whole state.

## Recommended Starting Values
- Download workers: 6 to 10 (tune by API responsiveness).
- OCR workers (if enabled later): 2 to 4.

## Out of Scope (Phase 1)
- State-level parallelism.
- Major retry/circuit-breaker redesign.
- OCR redesign beyond optional separate pool.

## Future Enhancements
- Add bounded retry with exponential backoff for transient HTTP failures.
- Add optional state-level concurrency behind a separate config key.
- Revisit TLS verification settings for production hardening.
