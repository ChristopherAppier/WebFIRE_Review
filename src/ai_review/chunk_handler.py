import pdfplumber
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def chunk_pdfs(
    pdf_directory: str = None,
    chunk_size: int = None,
    overlap: int = 100,
    chunk_prefix: str = "source_pdf"
):
    """
    Reads OCR'd PDFs and creates overlapping chunks of the text.

    Args:
        pdf_directory: Path to folder containing PDF files
        chunk_size: Number of words per chunk (read from settings.yaml)
        overlap: Number of words to overlap between chunks (default: 100)
        chunk_prefix: Prefix for chunk filenames (default: "source_pdf")

    Returns:
        List of tuples containing (chunk_path, chunk_info)
    """

    output_directory = pdf_directory / 'chunks'
    chunks_created = []

    pdf_files = sorted([f for f in pdf_directory.glob("*.pdf")])

    if not pdf_files:
        logger.warning(f"No PDF files found in: {pdf_directory}")
        return chunks_created

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    for pdf_file in pdf_files:
        try:
            chunks = _process_single_pdf(
                pdf_file=pdf_file,
                output_dir=Path(output_directory),
                chunk_size=chunk_size,
                overlap=overlap,
                prefix=chunk_prefix
            )
            chunks_created.extend(chunks)
            logger.info(f"Processed {pdf_file.name}: created {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {str(e)}")
            continue

    logger.info(f"Total chunks created: {len(chunks_created)}")
    return chunks_created


def _process_single_pdf(
    pdf_file: Path,
    output_dir: Path,
    chunk_size: int,
    overlap: int,
    prefix: str
) -> List[Tuple[Path, Dict]]:
    """
    Process a single PDF and create fixed-size overlapping chunks.

    Args:
        pdf_file: Path to the PDF file
        output_dir: Output directory for chunks
        chunk_size: Number of words per chunk
        overlap: Number of words to overlap between chunks
        prefix: Filename prefix for chunks

    Returns:
        List of (chunk_path, chunk_info) tuples
    """

    chunks = []

    try:
        with pdfplumber.open(pdf_file) as pdf:
            all_text = _extract_pdf_text(pdf)
            word_tokens = all_text.split()
            logger.info(f"  Extracted {len(word_tokens)} words from {pdf_file.name}")
    except Exception as e:
        logger.error(f"  Failed to extract text from {pdf_file.name}: {str(e)}")
        return chunks

    if not word_tokens:
        logger.warning(f"  No text extracted from {pdf_file.name}, skipping")
        return chunks

    chunk_num = 0
    current_start = 0
    step = chunk_size - overlap  # how far to advance each iteration

    if step <= 0:
        logger.error(f"  overlap ({overlap}) must be less than chunk_size ({chunk_size}). Aborting.")
        return chunks

    while current_start < len(word_tokens):
        chunk_end = min(current_start + chunk_size, len(word_tokens))
        chunk_text = ' '.join(word_tokens[current_start:chunk_end])

        if chunk_text.strip():
            chunk_num += 1
            chunk_path, chunk_info = _save_chunk(
                chunk_text=chunk_text,
                output_dir=output_dir,
                prefix=prefix,
                source_pdf=str(pdf_file.name),
                chunk_num=chunk_num,
                start_idx=current_start,
                end_idx=chunk_end,
                word_count=len(chunk_text.split())
            )
            chunks.append((chunk_path, chunk_info))

        current_start += step

    return chunks


def _extract_pdf_text(pdf) -> str:
    """
    Extract text from all pages of a PDF.

    Args:
        pdf: Open pdfplumber PDF object

    Returns:
        Full text content as a single string
    """

    text_parts = []

    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
        else:
            logger.debug(f"Page has no extractable text: {page.number}")

    return '\n\n'.join(text_parts)


def _save_chunk(
    chunk_text: str,
    output_dir: Path,
    prefix: str,
    source_pdf: str,
    chunk_num: int,
    start_idx: int,
    end_idx: int,
    word_count: int
) -> Tuple[Path, Dict]:
    """
    Save a chunk to a text file.

    Args:
        chunk_text: Text content of the chunk
        output_dir: Output directory
        prefix: Filename prefix
        source_pdf: Source PDF filename
        chunk_num: Chunk number
        start_idx: Start word index
        end_idx: End word index
        word_count: Number of words in chunk

    Returns:
        Tuple of (file_path, metadata_dict)
    """

    chunk_id = f"{chunk_num:03d}"
    filename = f"{prefix}_{source_pdf.replace('.pdf', '')}_chunk_{chunk_id}.txt"

    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(chunk_text)

    metadata = {
        'source_pdf': source_pdf,
        'chunk_num': chunk_num,
        'start_idx': start_idx,
        'end_idx': end_idx,
        'word_count': word_count,
        'created_at': datetime.now().isoformat()
    }

    return (filepath, metadata)