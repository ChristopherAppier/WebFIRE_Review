from common import utilities
from document_retrieval.doc_retrieval_main import main as document_retrieval
from llm_review.llm_review_main import main as llm_review
from summary_report.summary_report_main import main as summary_report

def main():
    
    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    # Removes previous run data (if enabled in settings.yml) and checks folder structure
    utilities.data_dir_clean(config, paths)

    # Runs the document retrieval process
    document_retrieval(config, paths)

    # Runs the LLM review process
    llm_review(config, paths)

    # Runs the summary report builder
    summary_report(config, paths)

if __name__ == "__main__":
    main() 