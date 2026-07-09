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

  - [x] WebFIRE report pull
    - [x] Refactor / review
    - [x] Fix HTTPS TLS certificate verification
    - [x] Use settings.yml info for URLs, etc.

  - [x] OCR
    - [x] Refactor / review

  - [x] Routing
    - [x] Refactor / review
    - [x] Rewrite using magic library (accurately determines file type)
    - [x] Fix zip_extract.py so that it properly routes zips that contained a folder of mixed file types
    - [x] Make zip_extract.py write document names in the zip to the http report table (needed for embedding facility name in review JSON) - non zips are already correct

  - [x] Text Chunking
    - [x] Refactor / review
    - [x] Generalize chunking function for use in renaming (future proof)?
    - [ ] Add # chunks created text

  - [x] AI Reviewer
    - [x] Ingest chunk + prompt
    - [x] Process + output JSON (issue flag, issue description)
    - [x] Add additional info to JSON via scripting
    - [x] JSON validation
    - [x] Reviewer prompt
    - [x] Add retry looping
    - [x] Refactor
    - [x] Shift to omlx and openai
    - [ ] Add document review name to JSON

  - [ ] Summary Report Building
    - [x] Pull JSONs
    - [x] Create report
    - [ ] Compress chunk reviews for same document (req doc review name first)
    - [ ] Visual dashboard via Streamlit

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
  - [ ] Scrape html file for facility info
  - [x] Add download retries

- [ ] File Routing
- [ ] Check spreadsheets for EPA template layout - route to Other folder if not using the template

- [ ] OCR
  - [ ] Add LLM w vision + text capabilities or structured table parser for table OCR
  - [ ] Add setting to OCR all reports (do not rely on other sources for OCR quality)

- [ ] Text Chunking
  - [ ] Add summarization to chunks
  - [ ] Add context based stitching after summarization to balance context buildup vs coherency of report

- [ ] File Renaming
  - [x] Deterministic NLP research
  - [ ] Chunk file
  - [ ] Ingest (NLP)
  - [ ] Output potential facility names (NLP)
  - [ ] Use LLM to select report type and best name (may not be necessary if html scraping gets name)
  - [ ] Check output format
  - [ ] Change name
  - [ ] Refactor

- [ ] AI Reviewer
  - [ ] Reviewer prompt selection
  - [ ] Reviewer prompt bank
  - [ ] Seed randomizer and tracking
  - [ ] RAG retrieval interface
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

- [ ] eCFR RAG
  - [ ] Pull eCFR sections
  - [ ] Initial RAG scan
  - [ ] Automated update that scans for eCFR updates
  - [ ] RAG scans after updates
  - [ ] RAG retreival integrated into reviewer
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
