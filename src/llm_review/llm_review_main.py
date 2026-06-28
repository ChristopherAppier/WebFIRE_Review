from llm_review.chunk_handler import chunk_pdfs
from llm_review.analysis_handler import analyze_chunks

def main(config, paths):
    
    # Chunking the OCR'd PDFs into overlapping text chunks and save them
    #chunk_pdfs(config, paths)
    
    # Analyzing the chunks using an LLM and storing the results in JSON format
    analyze_chunks(config, paths)

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    main(config, paths)