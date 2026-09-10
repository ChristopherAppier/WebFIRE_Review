# Computer Setup

- [x] oMLX
  - [x] Models + settings
- [x] VS Code
  - [x] Extensions
  - [x] Settings
  - [x] Formatter and Linter
- [x] Python
  - [x] Create env
  - [x] Download libraries
- [x] GitHub

# Outside Documentation

- [x] One-pager
- [x] Slide deck
- [ ] Business Plan
- [ ] Golden Dataset
- [ ] Evaluation Metrics

# MVP Version

- [ ] Create MVP Version
  - [x] Add print statements at major steps

## /config/settings.yml
  - [x] Settings
    - [x] Add logging dir

## /src/common/utilities.py
  - [x] Utilities
    - [x] find_project_root
    - [x] load_settings
    - [x] build_paths
    - [x] setup_logging
    - [x] Replace print() with logging()

## /src/retrieve/download_handler.py
  - [x] WebFIRE report pull
    - [x] Refactor / review
    - [x] Fix HTTPS TLS certificate verification
    - [x] Use settings.yml info for URLs, etc.
    - [x] Replace print() with logging()

## /src/retrieve/ocr_handler.py
  - [x] OCR
    - [x] Refactor / review
    - [x] Replace print() with logging()

## /src/retrieve/extract_and_route.py
  - [x] Routing
    - [x] Refactor / review
    - [x] Rewrite using magic library (accurately determines file type)
    - [x] Fix zip_extract.py so that it properly routes zips that contained a folder of mixed file types
    - [x] Make zip_extract.py write document names in the zip to the http report table (needed for embedding facility name in review JSON) - non zips are already correct
    - [x] Compress all state_report_table.csv files into one and use that for the zip_extract.py and everything else.
    - [x] Replace print() with logging()

## /src/ai_review/chunk_handler.py
  - [x] Text Chunking
    - [x] Refactor / review
    - [x] Generalize chunking function for use in renaming (future proof)?
    - [x] Add # chunks created text
    - [x] Add optional chunk cap for large files
    - [x] Replace print() with logging()

## /src/ai_review/overall_context_creator.py
  - [ ] Overall Context Carry-Forward Mechanism
    - [ ] Create overall context creation prompt
    - [ ] Overall context creation function
    - [ ] Integrate overall context into subsequent chunk processing

## /src/ai_review/analysis_handler.py
  - [x] AI Reviewer
    - [x] Ingest chunk + prompt
    - [x] Process + output JSON (issue flag, issue description)
    - [x] Add additional info to JSON via scripting
    - [x] JSON validation
    - [x] Reviewer prompt
    - [x] Add retry looping
    - [x] Refactor
    - [x] Shift to omlx and openai
    - [x] Add facility/document info to JSON
    - [x] Replace print() with logging()

## /src/common/prompt_selection.py
  - [ ] Prompt Selection
    - [ ] Input first report chunk
    - [ ] Determine report type
    - [ ] Use report type to pull prompt from prompt bank
    - [ ] Return prompt text and prompt code (for tracking in JSONs)

## /src/summarize/report_compiler.py
  - [ ] Summary Report Building
    - [x] Pull JSONs
    - [x] Create report
    - [ ] Compress chunk reviews for same document
    - [x] Replace print() with logging()

## /src/evaluate
- [ ] Create MVP Version Evaluation Harness
  - [ ] Plan implementation strategy
  - [ ] Define inputs (edge cases included)
  - [ ] Load inputs
  - [ ] Analyze performance metrics
  - [ ] Output performance metrics

## /docs/evaluation/evaluation.md
- [ ] Add MVP Version Evaluation Metrics
  - [ ] Plan implementation strategy
  - [ ] Define metrics
  - [ ] Define success
  - [ ] Embed performance metrics into code

- [ ] Harden MVP Version
  - [ ] Test, modify, repeat until success

## /docs/info
- [ ] Documentation
  - [ ] Update README.md
  - [ ] Update architecture.md
  - [ ] Update setup.md
  - [ ] Update configuration.md
  - [ ] Update output_formats.md

# Full Version

- [ ] Create Full Version

  - [ ] Progress Tracking and Resume
    - [ ] Implement progress tracking mechanism
    - [ ] Implement resume functionality

  - [ ] Report Downloading
    - [x] Scrape html file for facility info
    - [x] Add download retries
    - [ ] Multithreaded downloading (optional)

  - [ ] File Routing
  - [ ] Check spreadsheets for EPA template layout - route to Other folder if not using the template

  - [ ] OCR
    - [ ] Add LLM w vision + text capabilities or structured table parser for table OCR (layout aware parsing)
    - [ ] Add setting to OCR all reports (do not rely on other sources for OCR quality)

  - [ ] Text Chunking
    - [ ] Add summarization to chunks
    - [ ] Add context based stitching after summarization to balance context buildup vs coherency of report

  - [ ] Prompt Selection
    - [ ] Flush out prompt bank
    - [ ] Add function for LLM Audit prompt selection
    - [ ] Refactor

  - [ ] AI Reviewer
    - [ ] Reviewer prompt selection
    - [ ] Reviewer prompt bank
    - [ ] More robust JSON checking
    - [ ] RAG and/or other tool calls
    - [ ] Test review task separation based on doc type / size
    - [ ] Refactor

  - [ ] AI Auditor
    - [ ] Auditor prompt bank
    - [ ] Auditor prompt selection
    - [ ] Seed randomizer and tracking
    - [ ] Refactor

  - [ ] Python Scraping
    - [ ] Read in spreadsheets
    - [ ] Identify flags
    - [ ] Build output JSON
    - [ ] Refactor

  - [ ] Summary Report Building
    - [ ] Add python scraping to report building
    - [ ] Refactor

  - [ ] eCFR RAG
    - [ ] Pull eCFR sections
    - [ ] Figure out RAG vs (tool call + subagent summary) - then create to do list

  - [ ] Automated Trigger

  - [ ] Create Full Version Evaluation Harness
    - [ ] Plan implementation strategy
    - [ ] Define inputs (edge cases included)
    - [ ] Load inputs
    - [ ] Analyze performance metrics
    - [ ] Output performance metrics

  - [ ] Add Full Version Evaluation Metrics
    - [ ] Plan implementation strategy
    - [ ] Define metrics
    - [ ] Define success
    - [ ] Embed performance metrics into code

  - [ ] Harden Full Version
    - [ ] Test, modify, repeat until pass

  - [ ] Documentation
    - [ ] Update README.md
    - [ ] Update architecture.md
    - [ ] Update setup.md
    - [ ] Update configuration.md
    - [ ] Update output_formats.md

# Future Additions

- [ ] Config validation (check that settings are appropriate)
- [ ] Data dashboard (live or post run?)


# Notes
