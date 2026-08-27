from llm_review.analysis_handler import analyze_chunks
from llm_review.chunk_handler import chunk_pdfs
from llm_review.prompt_selector import select_prompts


def main(config, paths):
    
    # Chunking the OCR'd PDFs into overlapping text chunks and save them
    chunk_pdfs(config, paths)

    # Selecting the prompts for each chunk based on the contents of the report
    select_prompts(config, paths)
    
    # Analyzing the chunks using an LLM and storing the results in JSON format
    analyze_chunks(config, paths)

if __name__ == "__main__":
    from common import utilities

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = utilities.initialize_project()

    main(config, paths)