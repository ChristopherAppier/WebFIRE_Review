from common import utilities
from document_retrieval.doc_retrieval_main import main as document_retrieval
from llm_review.llm_review_main import main as llm_review

def main():
    
    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    # Removes previous run data (if enabled in settings.yml) and checks folder structure
    utilities.data_dir_clean(config, paths)

    # Run the document retrieval process
    document_retrieval(config, paths)

    # Run the LLM review process
    llm_review(config, paths)

if __name__ == "__main__":
    main() 