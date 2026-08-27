# Prompt selection functionality

- [ ] Add basic prompt selector
  # settings.yml
  - [x] Add prompt for stack test and one for other reports
  - [x] Add prompt bank choice descriptions
  # prompt_selecter.py
  - [ ] Feed prompt bank choice descriptions and first chunk in each set in
  - [ ] LLM outputs choice name
  - [ ] Write prompt choice to spreadsheet (using chunk name to find it?)
  # load_system_prompt()
  - [x] Pull prompt choice from spreadsheet
  - [x] Pull full prompt text from settings.yml based on spreadsheet \*\*\*
  - [x] Return full prompt text
  # analyze_chunks()
  - [x] Save prompt choice to JSON w metadata

\*\*\* What is a good way to stop from reading the spreadsheet/settings.yaml every chunk? Order the chunks?
