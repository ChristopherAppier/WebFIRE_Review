import logging

import pdfplumber

logger = logging.getLogger(__name__)


class PdfExtractionError(RuntimeError):
    """Raised when text cannot be extracted from a PDF."""


def validate_chunk_config(config):
    """Return validated chunk size, overlap, and optional cap settings."""
    chunk_size = config.get("chunk_size")
    overlap = config.get("chunk_overlap")
    chunk_cap = config.get("chunk_cap")

    if (
        isinstance(chunk_size, bool)
        or not isinstance(chunk_size, int)
        or chunk_size < 1
    ):
        raise ValueError("chunk_size must be a positive integer")
    if isinstance(overlap, bool) or not isinstance(overlap, int) or overlap < 0:
        raise ValueError("chunk_overlap must be a non-negative integer")
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    if chunk_cap is not None and (
        isinstance(chunk_cap, bool) or not isinstance(chunk_cap, int) or chunk_cap < 1
    ):
        raise ValueError("chunk_cap must be a positive integer or null")

    return chunk_size, overlap, chunk_cap


def chunk_pdfs(config, paths):
    """
    Reads OCR'd PDFs and creates overlapping chunks of the text.

    Args:
        paths: Dictionary containing paths to various directories
        config: Dictionary containing chunking configuration
    """
    logger.info(f"\n{'*' * 50}\n\nStarting PDF chunking process")

    chunk_settings = validate_chunk_config(config)
    pdf_files = sorted([f for f in paths["pdf_dir"].glob("*.pdf")])
    counts = {"total": len(pdf_files), "chunked": 0, "empty": 0, "failed": 0}

    if not pdf_files:
        logger.warning("No PDF files found in %s", paths["pdf_dir"])
        return counts

    logger.info(f"\nFound {len(pdf_files)} PDF files to process\n")

    # Process each PDF file and create chunks
    for pdf_file in pdf_files:
        try:
            num_chunks = process_single_pdf(
                config,
                paths["chunk_dir"],
                pdf_file,
                chunk_settings=chunk_settings,
            )
            if num_chunks > 0:
                counts["chunked"] += 1
            else:
                counts["empty"] += 1
        except Exception:
            counts["failed"] += 1
            logger.exception("Failed to process PDF %s", pdf_file.name)

    log_summary = (
        logger.info if counts["failed"] == counts["empty"] == 0 else logger.warning
    )
    log_summary(
        "PDF chunking finished: total=%d chunked=%d empty=%d failed=%d",
        counts["total"],
        counts["chunked"],
        counts["empty"],
        counts["failed"],
    )
    return counts


def process_single_pdf(config, output_dir, pdf_file, *, chunk_settings=None):
    """
    Process a single PDF and create fixed-size overlapping chunks.

    Args:
        config: Dictionary containing chunking configuration
        output_dir: Output directory for chunks
        pdf_file: Path object of the PDF file to process
    Returns:
        int: Number of chunks created for the PDF
    """
    chunk_size, overlap, chunk_cap = chunk_settings or validate_chunk_config(config)
    chunk_num = 0
    step = chunk_size - overlap

    # Extract text from the PDF using pdfplumber
    try:
        with pdfplumber.open(pdf_file) as pdf:
            word_tokens = []
            # Extract text from each page and split into words
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    word_tokens.extend(page_text.split())

    except Exception as error:
        raise PdfExtractionError(
            f"Could not extract text from {pdf_file.name}"
        ) from error
    # If no text was extracted, log a message and skip to the next PDF
    if not word_tokens:
        logger.warning(f"No text extracted from {pdf_file.name}, skipping")
        return 0

    # Create overlapping chunks of the extracted text and save them
    for current_start in range(0, len(word_tokens), step):
        if chunk_cap is not None and chunk_num >= chunk_cap:
            break

        # Sets the end index for the current chunk at the smaller of chunk size or end of the word list
        chunk_end = min(current_start + chunk_size, len(word_tokens))
        chunk_text = " ".join(word_tokens[current_start:chunk_end])

        # Saving the chunk to a text file if it contains any text
        if chunk_text.strip():
            chunk_id = f"{chunk_num:03d}"
            filename = f"{pdf_file.stem}_chunk_{chunk_id}.txt"
            filepath = output_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(chunk_text)
            chunk_num += 1

    logger.info("Processed %s: created %d chunks", pdf_file.name, chunk_num)

    return chunk_num


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    chunk_pdfs(config, paths)
