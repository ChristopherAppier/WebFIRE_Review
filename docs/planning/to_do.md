# Extra Token Burn Tasks
- [ ] Update documentation (after MVP finalized)
- [ ] Update / cleanup comments in all scripts

# Update environment.yml
- [x] Update environment.yml with necessary dependencies for final MVP version

# Prompt selection functionality
- [x] Add basic prompt selector
  ## prompt_bank.yml
  - [x] Add prompt for stack test and one for other reports
  - [x] Add prompt bank choice descriptions
  ## download.py > parse_search_results()
  - [x] Add prompt column
  ## prompts.py
  - [x] Feed prompt bank choice descriptions and first chunk in each set in
  - [x] LLM outputs choice name
  - [x] Write prompt choice to spreadsheet
  ## review.py > load_system_prompt()
  - [x] Pull prompt choice from spreadsheet
  - [x] Pull full prompt text from settings.yml based on spreadsheet
  - [x] Return full prompt text
  ## review.py > analyze_chunks()
  - [x] Save prompt choice to JSON w metadata

# Overall context carry forward
- [x] Add a mechanism to carry forward the overall context of the document into each analysis

# Concurrent downloads
- [x] Add concurrent download for webfire files

# Add error handling / logging for each /src subfolder individually via Plan>Agent
- [x] Logging fully implemented

# Evaluation implementation
- [ ] Evaluation specifics (docs/info/evaluation.md)
- [ ] Create a test harness for each pipeline

# Run evaluation testing
- [ ] Assemble data set
  - [ ] Good dataset of each type w answers
  - [ ] Bad/invalid data set
- [ ] Evaluate each pipeline
- [ ] Evaluate entire workflow
- [ ] Revise / retest until criteria pass

# Update documentation
