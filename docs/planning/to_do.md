# Update environment.yml
- [x] Update environment.yml with necessary dependencies for final MVP version

# Extra Token Burn Tasks
- [ ] Update architecture.md for final MVP version
- [ ] Update setup.md for final MVP version
- [ ] Update configuration.md for final MVP version
- [ ] Update output_formats.md for final MVP version
- [ ] Update / cleanup comments in all scripts

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
- [ ] Add a mechanism to carry forward the overall context of the document into each analysis
## use the first chunk as part of the prompt sent for each review. Should be an easy mod.

# Add concise error handling / logging for each script individually via Plan>Agent
