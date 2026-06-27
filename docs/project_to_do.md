# Computer Setup

- [X] Ollama
  - [X] Models + settings
- [X] VS Code
  - [X] Extensions
  - [X] Settings
  - [ ] Formatter and Linter
- [X] Python
  - [X] Create env
  - [X] Download libraries
- [X] GitHub

# Documentation

- [X] Fill in README.md
- [ ] Fill in architecture.md
- [ ] Fill in setup.md
- [ ] Fill in configuration.md
- [ ] Fill in output_formats.md
- [ ] Create Business Plan
- [ ] Create master slide deck

# MVP Version

- [ ] Create MVP Version
  - [ ] Add print statements at major steps

  - [X] Common
    - [X] find_project_root
    - [X] load_settings
    - [X] build_paths

  - [ ] WebFIRE report pull
    - [ ] Refactor / review
    - [ ] Fix HTTPS TLS certificate verification
    - [ ] Use settings.yml info for URLs, etc.

  - [X] OCR
    - [X] Refactor / review

  - [X] Routing
    - [X] Refactor / review
    - [X] Rewrite using magic library (accurately determines file type)
    - [X] Fix zip_extract.py so that it properly routes zips that contained a folder of mixed file types

  - [ ] Text Chunking
    - [ ] Refactor / review
    - [ ] Generalize chunking function for use in renaming (future proof)?

  - [ ] AI Reviewer
    - [x] Ingest chunk + prompt
    - [ ] Process + output JSON (issue flag, issue description)
    - [ ] Add to JSON via scripting (facility name, document name)
    - [ ] Seed randomizer and tracking
    - [ ] JSON validation
    - [ ] Reviewer prompt
    - [ ] Refactor

  - [ ] Summary Report Building
    - [ ] Pull JSONs
    - [ ] Create report
    - [ ] Refactor

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
  - [ ] Test, modify, repeat until pass

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
  - [ ] Add download retries

 - [ ] File Routing
  - [ ] Check spreadsheets for EPA template layout - route to Other folder if not using the template

  - [ ] OCR
    - [ ] Add LLM w vision + text capabilities or structured table parser for table OCR

  - [ ] Text Chunking
    - [ ] Add summarization to chunks
    - [ ] Add context based stitching after summarization to balance context buildup vs coherency of report

  - [ ] File Renaming
    - [X] Deterministic NLP research
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
    - [ ] RAG retrieval interface
    - [ ] Tool calling
    - [ ] Refactor

  - [ ] AI Auditor
    - [ ] Auditor prompt bank
    - [ ] Auditor prompt selection
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
- JSON from reviewer contain model chain of reasoning, citations, confidence levels, RAG retrievals