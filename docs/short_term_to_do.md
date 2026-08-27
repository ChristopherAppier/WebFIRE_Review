- [ ] Add basic prompt selector
  # analyze_chunks()
  - [ ] Load new system prompt for the first chunk (use chunk name/number)
  # settings.yml
  - [ ] Add prompt for stack test and one for other reports
  - [ ] Add prompt bank choice descriptions
  # load_system_prompt()
  - [ ] Feed prompt bank choice descriptions and first chunk in each set in
  - [ ] LLM outputs choice name
  - [ ] Pull full prompt text from settings.yml based on LLM choice
  - [ ] Return full prompt text and choice
  # analyze_chunks()
  - [ ] Save prompt choice to JSON w metadata
