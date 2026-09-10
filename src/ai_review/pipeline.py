from ai_review.chunk import chunk_pdfs
from ai_review.context import create_overall_context
from ai_review.review import review_chunks
from common.prompts import select_prompts


def main(config, paths):

    # Chunking the OCR'd PDFs into overlapping text chunks and save them
    chunk_pdfs(config, paths)

    # Creating a short overall context description for each report
    create_overall_context(config, paths)

    # Selecting the prompts for each report based on the overall context
    select_prompts(config, paths)

    # Analyzing the chunks using an LLM and storing the results in JSON format
    review_chunks(config, paths)


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    main(config, paths)
