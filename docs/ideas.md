# VERY IMPORTANT - IMPLEMENT THESE ITEMS

- Create a file that tracks progress in a run and a setting that allows it to pick up from that spot on the next attempt
- For chunking, use "layout aware parsing" libraries
- For chunking, use metadata carry-forward. Have a summary of the document from the first review and keep it with every other chunk for the overall context of the document. (maybe do this at prompt selection step. Have llm review for prompt selection and one for the "core idea" of the document to be appended to all chunks)
-

# Unsorted

- Use facility name in doc dl spreadsheet for doc naming
- Use report type / sub-type in doc dl spreadsheet for doc naming prompt assistance
- Add OCR settings.yml flag for overriding existing OCR (for quality control purposes)
- For LLM based chunking strategy: chunk/summarize/stitch
- Use table specific parser for chunking in full version
- Create a config validation utility
  - Include chunk step calculation validation (chunk_size - chunk_overlap must be > 0, set to 5k if not)
  - Check that audit chance is integer
- After x LLM calls, wait y time (thermal management)

# Data Dashboard

- Incorporate the following data into a streamlit dashboard
  - Report Info
    - Date
    - Count
    - Type
    - MB (show download bar below map)
    - Download time/speed
    - Lat/long (Add to map once downloaded)
  - OCR
    - Number pdfs total
    - Number OCR
    - Number of pages OCR
    - Time / speed
  - Chunking
    - Number pdfs
    - Number chunks
    - Chunk size / overlap / etc
  - LLM Review
    - Model card
    - Think/output streaming
    - JSON key/values
    - Time / token speeds
  - Flow chart (animate what step its at)
