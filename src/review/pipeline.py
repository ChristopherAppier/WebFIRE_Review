from common.prompts import select_prompts
from review.chunk import chunk_pdfs, chunk_spreadsheets
from review.review import review_chunks


def main(config, paths):

    # Chunking the OCR'd PDFs into overlapping text chunks and saving them
    chunk_pdfs(config, paths)

    # Converting spreadsheets into text chunks for review
    chunk_spreadsheets(config, paths)

    # Selecting the prompts for each report based on the overall context
    select_prompts(config, paths)

    # Analyzing the chunks using an LLM and storing the results in JSON format
    review_chunks(config, paths)


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    main(config, paths)
