from common import utilities
from chunk_handler import chunk_pdfs
from analysis_handler import analyze_chunks

def main(paths, config):
    
    # Chunking the OCR'd PDFs into overlapping text chunks and save them
    chunk_pdfs(paths, config)
    
    # Analyzing the chunks using an LLM and storing the results in JSON format
    analyze_chunks(paths, config)

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    # Removes previous run data (if enabled in settings.yml) and checks folder structure
    utilities.data_dir_clean(config, paths)

    main(paths, config)