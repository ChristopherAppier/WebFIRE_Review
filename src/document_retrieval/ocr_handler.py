import os
import subprocess
import sys
import tempfile
from pathlib import Path


def apply_ocr(config, paths):
    """
    Apply OCR to every PDF in the specified folder.
    
    Args:
        config (dict): Dictionary containing OCR configuration.
        paths (dict): Dictionary containing paths to various data directories.
    """
    print(f"\n{'*' * 50}\n\nStarting OCR processing for PDFs\n")

    pdf_files = sorted(
        pdf_file
        for pdf_file in paths['pdf_dir'].glob("*")
        if pdf_file.is_file() and pdf_file.suffix.lower() == ".pdf"
    )

    for pdf_file in pdf_files:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", dir=pdf_file.parent, delete=False
        ) as tmp_file:
            temp_output = Path(tmp_file.name)

        cmd = [
            sys.executable,
            "-m",
            "ocrmypdf",
            "--jobs",
            str(config['ocr_jobs_per_file']),
            "--pdf-renderer",
            config['ocr_pdf_renderer'],
            "-s",
            "-q",
            "--invalidate-digital-signatures",
            str(pdf_file),
            str(temp_output),
        ]

        try:
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True
            )
            os.replace(temp_output, pdf_file)
            print(f"Processed: {pdf_file.name}")
            if result.stderr:
                print(result.stderr.strip())
        except subprocess.CalledProcessError as e:
            if temp_output.exists():
                temp_output.unlink(missing_ok=True)
            print(f"OCR failed for {pdf_file.name}: {e}")
            if e.stderr:
                print(e.stderr.strip())
            continue
        except FileNotFoundError as e:
            if temp_output.exists():
                temp_output.unlink(missing_ok=True)
            print(f"ocrmypdf not found: {e}")
            continue
        except Exception as e:
            if temp_output.exists():
                temp_output.unlink(missing_ok=True)
            print(f"Unexpected OCR error for {pdf_file.name}: {e}")
            continue
    
    print("\nOCR processing complete for PDFs")

if __name__ == "__main__":
    from common import utilities

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = utilities.initialize_project()

    apply_ocr(config, paths)