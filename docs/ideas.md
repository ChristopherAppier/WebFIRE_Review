# Unsorted
- Use facility name in doc dl spreadsheet for doc naming
- Use report type / sub-type in doc dl spreadsheet for doc naming prompt assistance
- Add OCR settings.yml flag for overriding existing OCR (for quality control purposes)
- For LLM based chunking strategy: chunk/summarize/stitch
- Use table specific parser for chunking in full version
- Create a config validation utility
    - Include chunk step calculation validation (chunk_size - chunk_overlap must be > 0, set to 5k if not)
    - Call this inside the load_config as a helper so that every file gets it without extra func calls
- Incorporate the data_dir_clean into the load_config function so every file gets it without extra func calls