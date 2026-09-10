# Output Formats

## Purpose

- Explain what each stage of the pipeline writes out
- Define how outputs are structured and where they are used

## Output Types

- JSON files
- Spreadsheets
- Email summaries
- Audit folders
- Logs or timing files

## Retrieval Outputs

- Downloaded source files
- Extracted documents
- Renamed files
- Any routing or tracking metadata

## OCR / Parsing Outputs

- OCR text output
- Parsed document text
- Chunked PDF text or document segments
- Normalized content for downstream review

## Review Outputs

- Compliance determination JSON
- Deviation flag JSON
- Excess emission flag JSON
- Scan statistics JSON
- Reviewer notes or summaries

## Audit Outputs

- Live auditor review results
- Random auditor review results
- Sampled audit input packages
- Audit summary statistics

## Reporting Outputs

- Human-readable spreadsheet summaries
- Further review spreadsheet
- Email-ready attachments or links
- Final report files

## File Naming Conventions

- Standard naming pattern for each output type
- How timestamps or run IDs are included
- How stage names are reflected in filenames

## Folder Locations

- Where each output type is saved
- Which folders are temporary vs final
- Which folders are meant for audit or review

## Data Schema Notes

- Expected fields in JSON outputs
- Important columns in spreadsheet outputs
- Any required identifiers or metadata

## Retention and Cleanup

- What outputs are kept
- What outputs are temporary
- When old outputs should be archived or deleted
