# Update environment.yml
- [ ] Update environment.yml with necessary dependencies for final MVP version

# Extra Token Burn Tasks
- [ ] Update architecture.md for final MVP version
- [ ] Update setup.md for final MVP version
- [ ] Update configuration.md for final MVP version
- [ ] Update output_formats.md for final MVP version

# Prompt selection functionality
- [ ] Add basic prompt selector
  ## prompt_bank.yml
  - [x] Add prompt for stack test and one for other reports
  - [x] Add prompt bank choice descriptions
  ## download_handler.py > parse_search_results()
  - [x] Add prompt column
  ## prompt_selecter.py
  - [ ] Feed prompt bank choice descriptions and first chunk in each set in
  - [ ] LLM outputs choice name
  - [ ] Write prompt choice to spreadsheet
  ## analysis_handler.py > load_system_prompt()
  - [x] Pull prompt choice from spreadsheet
  - [x] Pull full prompt text from settings.yml based on spreadsheet
  - [x] Return full prompt text
  ## analysis_handler.py > analyze_chunks()
  - [x] Save prompt choice to JSON w metadata

# Overall context carry forward
- [ ] Add a mechanism to carry forward the overall context of the document into each analysis
  ## prompt_bank.yml
  - [ ] Revise prompts to accommodate the initial context chunk
  - [ ] Add prompt for creating overall context to carry forward
  ## settings.yml
  - [x] Add directory for overall context files
  ## download_handler.py > parse_search_results()
  - [x] Add overall context column
  ## overall_context_creator.py
  - [ ] Feed in prompt and first chunk in each set in
  - [ ] LLM creates overall context text
  - [ ] Save overall context to a file
  - [ ] Save file name to spreadsheet for calling later
  ## analysis_handler.py > load_overall_context()
  - [ ] Pull file name from spreadsheet
  - [ ] Pull overall context from file
  - [ ] Stitch to chunk
  * May need to revise other functions to adapt method of pulling info from spreadsheet
  ## analysis_handler.py > analyze_chunks()
  - [ ] Save overall context to JSON
