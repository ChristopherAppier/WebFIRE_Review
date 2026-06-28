import pdfplumber

def chunk_pdfs(config, paths):
    """
    Reads OCR'd PDFs and creates overlapping chunks of the text.

    Args:
        paths: Dictionary containing paths to various directories
        config: Dictionary containing chunking configuration
    """
    print(f"\n\n{'*' * 50}\nStarting PDF chunking process")

    # Creating a list of all PDF files
    pdfs_processed = 0
    zero_chunk_count = 0
    pdf_files = sorted([f for f in paths['pdf_dir'].glob("*.pdf")])

    if not pdf_files:
        print(f"\nNo PDF files found")
        return

    print(f"\nFound {len(pdf_files)} PDF files to process")

    # Process each PDF file and create chunks
    for pdf_file in pdf_files:
        try:
            num_chunks = process_single_pdf(config, paths['chunk_dir'], pdf_file)
            # Tracking the number of successfully proccessed PDFs
            if num_chunks > 0:
                pdfs_processed += 1
            if num_chunks == 0:
                zero_chunk_count += 1

        except Exception as e:
            print(f"Error processing {pdf_file.name}: {str(e)}")
            continue

    # Final summary of the chunking process
    if pdfs_processed == len(pdf_files):
        print(f"\nAll PDFs successfully processed.")
    else:
        print(f"\nTotal PDFs with chunks: {pdfs_processed} of {len(pdf_files)}\nTotal PDFs with 0 chunks: {zero_chunk_count} of {len(pdf_files)}\nSome PDFs may have failed to process or returned 0 chunks")

def process_single_pdf(config, output_dir, pdf_file):
    """
    Process a single PDF and create fixed-size overlapping chunks.

    Args:
        config: Dictionary containing chunking configuration
        output_dir: Output directory for chunks
        pdf_file: Path object of the PDF file to process
    Returns:
        int: Number of chunks created for the PDF
    """
    # Extract configuration parameters and defining chunking variables
    chunk_size = config.get('chunk_size')
    overlap = config.get('overlap')
    prefix = config.get('chunk_prefix')
    chunk_num = 0
    step = chunk_size - overlap

    # Error handling for invalid configuration values
    if step <= 0:
        print("Overlap must be smaller than chunk_size. Using default step size of 5000 words.")
        step = 5000

    # Extract text from the PDF using pdfplumber
    try:
        with pdfplumber.open(pdf_file) as pdf:
            word_tokens = []
            # Extract text from each page and split into words
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    word_tokens.extend(page_text.split())

    # If any error occurs during text extraction, print the error and skip to the next PDF
    except Exception as e:
        print(f"Failed to extract text from {pdf_file.name}: {str(e)}")
        return -1
    # If no text was extracted, print a message and skip to the next PDF
    if not word_tokens:
        print(f"No text extracted from {pdf_file.name}, skipping")
        return 0

    # Create overlapping chunks of the extracted text and save them
    for current_start in range(0, len(word_tokens), step):
        # Sets the end index for the current chunk at the smaller of chunk size or end of the word list
        chunk_end = min(current_start + chunk_size, len(word_tokens))
        chunk_text = ' '.join(word_tokens[current_start:chunk_end])

        # Saving the chunk to a text file if it contains any text
        if chunk_text.strip():
            chunk_id = f"{chunk_num:03d}"
            filename = f"{prefix}_{pdf_file.stem}_chunk_{chunk_id}.txt"
            filepath = output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chunk_text)
            chunk_num += 1

    print(f"Processed {pdf_file.name}: created {chunk_num} chunks")

    return chunk_num

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    chunk_pdfs(config, paths)