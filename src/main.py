from audit.pipeline import main as audit_reviews
from common import startup
from retrieve.pipeline import main as retrieve_documents
from review.pipeline import main as review_documents
from summarize.pipeline import main as summarize_reviews


def main():

    # Sets up logging and loads configuration options and file paths from settings.yml
    config, paths = startup.initialize_project()

    # Retrieves documents from WebFIRE
    retrieve_documents(config, paths)

    # Reviews the documents using a lightweight LLM
    review_documents(config, paths)

    # Audits flagged documents and their lightweight LLM review using a heavyweight LLM
    audit_reviews(config, paths)

    # Builds a summary report based on the LLM reviews
    summarize_reviews(config, paths)


if __name__ == "__main__":
    main()
