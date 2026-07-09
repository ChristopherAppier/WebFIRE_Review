from common import utilities
from document_retrieval.doc_retrieval_main import main as document_retrieval
from llm_review.llm_review_main import main as llm_review
#from python_review.python_review_main import main as python_review
#from audit.audit_main import main as audit
from summary_report.summary_report_main import main as summary_report

def main():
    
    # Load configuration settings from settings.yml and store them in a dictionary
    config = utilities.load_config()

    # Builds the paths for the data directories and store them in a Paths object
    paths = utilities.build_paths(config)

    # Runs the document retrieval process
    document_retrieval(config, paths)

    # Runs the LLM review process
    llm_review(config, paths)

    # Runs the python review process
    #python_review(config, paths)

    # Runs the audit process
    #audit(config, paths)

    # Runs the summary report building process
    summary_report(config, paths)

if __name__ == "__main__":
    main() 