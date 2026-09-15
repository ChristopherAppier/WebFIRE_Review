# Evaluation Plan

## Purpose

This plan provides a small, practical set of checks for WebFIRE Review. Its
purpose is to verify that the implemented workflow functions correctly and to
provide a lightweight way to inspect the quality of the LLM's reviews.

WebFIRE Review is a personal-use project, so this plan favors useful tests over
a large evaluation framework. It covers the implemented `common`, `retrieve`,
`review`, and `summarize` stages. Python review, audit, and the generic
evaluation harness are deferred until those stages contain working behavior.

## Evaluation Approach

The MVP has four parts:

1. Focused functional tests for each implemented stage.
2. Tests of the important handoffs between stages.
3. One isolated end-to-end test with mocked external services.
4. A small manual check of LLM review quality.

Automated tests determine whether the software works as intended. The manual
LLM check determines whether the model's judgments are useful. These are kept
separate because model quality can vary even when the software is functioning
correctly.

## Functional Tests

### Startup and shared behavior

Verify that:

- valid configuration and paths load correctly;
- invalid configuration produces a clear error;
- cleanup cannot affect the repository's production data during testing;
- prompt files load correctly;
- unknown prompt selections use the `generic` fallback; and
- prompt selections are saved to the correct report-table row.

### Retrieval

Verify that:

- WebFIRE search results are parsed into the expected CSV fields;
- failed downloads do not leave partial files;
- retry and individual-file failures are handled safely;
- duplicate filenames preserve both files;
- valid ZIP files are extracted and corrupt ZIP files are reported;
- files are routed to the expected PDF, spreadsheet, or other directory; and
- failed OCR does not destroy or replace the source PDF.

HTTP responses, MIME detection, and OCR should be mocked where appropriate.
Tests should use real temporary files and ZIP archives for filesystem behavior.

### Review

Verify that:

- PDFs, supported spreadsheets, and XML files produce expected chunks;
- chunk size, overlap, and cap settings are honored;
- continuation chunks include the first chunk as context;
- prompt selection and fallback are passed into review processing;
- valid plain and fenced JSON responses are accepted;
- malformed, incomplete, non-text, and wrongly typed responses are rejected;
- provider failures do not prevent later chunks from being attempted;
- attempted, succeeded, skipped, and failed counts are correct; and
- successful reviews are saved as JSON with source and chunk metadata.

For this MVP, `conf_score` and `importance` are numeric values from 0 through
10 and may include decimals, matching the current implementation.

### Summarization

Verify that:

- valid review objects produce one CSV row each;
- headers are unique and deterministic when review objects have different
  fields;
- missing fields become empty cells;
- commas, quotes, newlines, Unicode, and empty strings survive CSV round trips;
- lists and dictionaries use deterministic JSON encoding;
- malformed JSON and non-object JSON are skipped and reported;
- a previous summary cannot be mistaken for the current result when no valid
  reviews exist; and
- output write failures are reported and re-raised.

## Handoff Tests

Add two small integration tests:

1. **Retrieval to AI review:** Confirm that routed files and the `Document List`
   in `report_table.csv` allow chunking and metadata lookup to find the correct
   source document.
2. **AI review to summary:** Confirm that saved review JSON can be compiled into
   a parseable CSV without losing the source filename, chunk name, issue flag,
   description, confidence, importance, or prompt name.

These tests should exercise the real on-disk formats but mock network and model
calls.

## Mocked End-to-End Test

Create one small fixture flow:

```text
isolated temporary project
  -> fixture WebFIRE response and downloaded file
  -> extraction and file routing
  -> mocked OCR
  -> document chunks and prompt selection
  -> mocked LLM review response
  -> review JSON
  -> summary_report.csv
```

The test passes when:

- stages run in the expected order;
- expected files are created under the temporary project;
- no repository production data is changed;
- the review JSON contains the expected values and metadata;
- the summary is valid CSV with unique headers;
- every successful review produces one summary row; and
- intentionally injected failures are handled in the expected way.

Python review and audit are not part of this flow until their pipelines are
implemented.

## Manual LLM Quality Check

Maintain a small sample of approximately 10 to 20 representative documents or
chunks. Include different report types and both examples with issues and
examples without issues.

For each sample, record:

- sample identifier and source document;
- expected issue flag;
- expected importance, when applicable;
- expected prompt category;
- model issue flag, importance, and prompt category; and
- brief notes explaining meaningful disagreements.

Review this sample after changing the model, prompts, chunking behavior, or
review schema. Pay particular attention to missed issues and repeated false
alarms. Do not require formal precision, recall, F1, calibration, or statistical
confidence thresholds for the MVP. Establish those only if the sample becomes
large and stable enough to support them.

## Test Isolation and Live Checks

- Automated tests use temporary directories and synthetic or sanitized input.
- Automated tests never run cleanup against the repository's real `data/`
  directory.
- WebFIRE, OCR, and LLM calls are mocked by default.
- A live WebFIRE, OCR, or model smoke check is run manually and explicitly.
- A live dependency failure is recorded as an external failure, not confused
  with a deterministic software-test failure.
- API keys and other secrets are not stored in fixtures or test output.

Live checks are useful after configuration or dependency changes, but they are
not required for the normal automated test suite to pass.

## Acceptance Criteria

The MVP evaluation passes when:

- all focused functional and handoff tests pass;
- the mocked end-to-end test produces the expected review JSON and summary CSV;
- expected invalid inputs and injected failures are classified and handled
  safely;
- no automated test contacts an external service or changes production data;
  and
- the latest manual LLM sample has been reviewed and its important
  disagreements documented.

The manual LLM review is an informed quality check, not an automated release
gate.

## Implementation Order

1. Decide the minimum summary fields and what should happen to an old summary
   when no valid reviews exist.
2. Add missing focused regression tests to the existing test modules.
3. Correct summary header, structured-value, and stale-output behavior.
4. Add the retrieval-to-review and review-to-summary handoff tests.
5. Add one isolated mocked end-to-end test for the implemented stages.
6. Create and review the small manual LLM quality sample.

## Deferred Work

The following are outside this personal-use MVP and should be added only when
there is a concrete need:

- audit evaluation;
- a general-purpose evaluation pipeline or adapter framework;
- JSON Lines records for every test;
- run manifests and comprehensive artifact hashing;
- large output trees for copied inputs, outputs, failures, and diffs;
- a formally adjudicated golden dataset with multiple reviewers;
- statistical confidence intervals and fixed semantic thresholds;
- automated performance gates; and
- automated live WebFIRE, OCR, or LLM test tiers.