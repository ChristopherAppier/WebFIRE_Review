from ai_review.pipeline import main as ai_review
from audit.pipeline import main as audit_reviews
from common import startup
from python_review.pipeline import main as python_review
from retrieve.pipeline import main as retrieve_documents
from summarize.pipeline import main as summarize_reviews


def main():

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    # Runs the document retrieval process
    retrieve_documents(config, paths)

    # Runs the LLM review process
    ai_review(config, paths)

    # Runs the python review process
    python_review(config, paths)

    # Runs the audit process
    audit_reviews(config, paths)

    # Runs the summary report building process
    summarize_reviews(config, paths)


if __name__ == "__main__":
    main()
