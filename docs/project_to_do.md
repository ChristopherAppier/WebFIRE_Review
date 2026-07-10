# Computer Setup

- [x] oMLX
  - [x] Models + settings
- [x] VS Code
  - [x] Extensions
  - [x] Settings
  - [ ] Formatter and Linter
- [x] Python
  - [x] Create env
  - [x] Download libraries
- [x] GitHub

# Outside Documentation

- [x] One-pager
- [x] Slide deck
- [ ] Business Plan

# MVP Version

- [ ] Create MVP Version
  - [x] Add print statements at major steps

  - [x] Common
    - [x] find_project_root
    - [x] load_settings
    - [x] build_paths
    - [ ] Replace print() with logging()

  - [x] WebFIRE report pull
    - [x] Refactor / review
    - [x] Fix HTTPS TLS certificate verification
    - [x] Use settings.yml info for URLs, etc.
    - [ ] Replace print() with logging()

  - [x] OCR
    - [x] Refactor / review
    - [ ] Replace print() with logging()

  - [x] Routing
    - [x] Refactor / review
    - [x] Rewrite using magic library (accurately determines file type)
    - [x] Fix zip_extract.py so that it properly routes zips that contained a folder of mixed file types
    - [x] Make zip_extract.py write document names in the zip to the http report table (needed for embedding facility name in review JSON) - non zips are already correct
    - [x] Compress all state_report_table.csv files into one and use that for the zip_extract.py and everything else.
    - [ ] Replace print() with logging()

  - [x] Text Chunking
    - [x] Refactor / review
    - [x] Generalize chunking function for use in renaming (future proof)?
    - [x] Add # chunks created text
    - [ ] Add optional chunk cap for large files
    - [ ] Replace print() with logging()

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
    - [ ] Replace print() with logging()

  - [ ] Prompt Selection
    - [ ] Input first report chunk
    - [ ] Determine report type
    - [ ] Use report type to pull prompt from prompt bank
    - [ ] Return prompt text and prompt code (for tracking in JSONs)

  - [ ] Summary Report Building
    - [x] Pull JSONs
    - [x] Create report
    - [ ] Compress chunk reviews for same document (req doc review name first)
    - [ ] Visual dashboard via Streamlit
    - [ ] Replace print() with logging()

- [ ] Create MVP Version Evaluation Harness
  - [ ] Plan implementation strategy
  - [ ] Define inputs (edge cases included)
  - [ ] Load inputs

- [ ] Add MVP Version Evaluation Metrics
  - [ ] Plan implementation strategy
  - [ ] Define metrics
  - [ ] Define success
  - [ ] Embed performance metrics into code
  - [ ] Analyze performance metrics
  - [ ] Output performance metrics

- [ ] Harden MVP Version
  - [ ] Test, modify, repeat until success

- [ ] Documentation
  - [ ] Update README.md
  - [ ] Update architecture.md
  - [ ] Update setup.md
  - [ ] Update configuration.md
  - [ ] Update output_formats.md

# Full Version

- [ ] Create Full Version

- [ ] Report Downloading
  - [x] Scrape html file for facility info
  - [x] Add download retries
  - [ ] Multithreaded downloading (optional)

- [ ] File Routing
- [ ] Check spreadsheets for EPA template layout - route to Other folder if not using the template

- [ ] OCR
  - [ ] Add LLM w vision + text capabilities or structured table parser for table OCR
  - [ ] Add setting to OCR all reports (do not rely on other sources for OCR quality)

- [ ] Text Chunking
  - [ ] Add summarization to chunks
  - [ ] Add context based stitching after summarization to balance context buildup vs coherency of report

- [ ] Prompt Selection (common utilities for all prompt needs)
  - [ ] Flush out prompt bank
  - [ ] Add function for LLM Audit prompt selection
  - [ ] Refactor

- [ ] AI Reviewer
  - [ ] Reviewer prompt selection
  - [ ] Reviewer prompt bank
  - [ ] Seed tracking in JSON
  - [ ] RAG retrieval interface (may not need)
  - [ ] Tool calling
  - [ ] Flush out JSON information placeholders
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

- [ ] eCFR Injection System
  - [ ] Pull eCFR sections
  - [ ] Figure out RAG vs (tool call + subagent summary) - then create to do list
- [ ] Cron Trigger

- [ ] Create Full Version Evaluation Harness
  - [ ] Plan implementation strategy
  - [ ] Define inputs (edge cases included)
  - [ ] Load inputs

- [ ] Add Full Version Evaluation Metrics
  - [ ] Plan implementation strategy
  - [ ] Define metrics
  - [ ] Define success
  - [ ] Embed performance metrics into code
  - [ ] Analyze performance metrics
  - [ ] Output performance metrics

- [ ] Harden Full Version
  - [ ] Test, modify, repeat until pass

- [ ] Documentation
  - [ ] Update README.md
  - [ ] Update architecture.md
  - [ ] Update setup.md
  - [ ] Update configuration.md
  - [ ] Update output_formats.md

# Future Additions

- [ ]

# Notes
