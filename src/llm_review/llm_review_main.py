from pathlib import Path
from common import utilities
from chunk_handler import chunk_pdfs
from analysis_handler import analyze_chunks

def main():

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)
    
    # Chunking the OCR'd PDFs into overlapping text chunks
    chunk_pdfs(paths, config['chunk_size'], config['chunk_overlap'], "source_pdf")
    
    # Analyzing the chunks using the AI model and storing the results in JSON format
    analyze_chunks(paths, config)

if __name__ == "__main__":
    main()