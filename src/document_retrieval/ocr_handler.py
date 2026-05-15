import subprocess
from pathlib import Path

def apply_ocr(project_root):
    """
    Apply OCR to every PDF in the specified folder.
    
    Args:
        folder_path: Path to folder containing PDF files
    """
    
    folder_path = project_root / "data" / "pdfs"
    folder_path = Path(folder_path)

    for pdf_file in sorted(folder_path.glob("*.pdf")):
        cmd = [
            "ocrmypdf",
            "-s",
            "-q",
            "--invalidate-digital-signatures",
            str(pdf_file),
            str(pdf_file),
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"Processed: {pdf_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"OCR failed for {pdf_file.name}: {e}")
            continue
        except FileNotFoundError as e:
            print(f"ocrmypdf not found: {e}")
            continue
    
    return

if __name__ == "__main__":
    
    project_root = Path(__file__).parent.parent.parent
    
    apply_ocr(project_root)