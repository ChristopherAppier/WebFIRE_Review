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
        cmd = f'ocrmypdf -s -q --invalidate-digital-signatures "{pdf_file}" "{pdf_file}"'
        try:
            subprocess.run(cmd, check=True, shell=True)
            print(f"Processed: {pdf_file.name}")
        except (Exception):
            continue
    
    return

if __name__ == "__main__":
    
    project_root = Path(__file__).parent.parent.parent
    
    apply_ocr(project_root)