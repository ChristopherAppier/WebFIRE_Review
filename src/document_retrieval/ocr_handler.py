import subprocess
import tempfile
import os
import sys
from pathlib import Path

def apply_ocr(paths, config):
    """
    Apply OCR to every PDF in the specified folder.
    
    Args:
        paths: Dictionary containing paths to various data directories
        config: Dictionary containing OCR configuration
    """

    ocr_env = _build_ocr_env()

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
                cmd, check=True, capture_output=True, text=True, env=ocr_env
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
    
    return

def _build_ocr_env():
    """Create subprocess env with explicit Tesseract and tessdata locations."""
    env = os.environ.copy()
    py_dir = Path(sys.executable).resolve().parent
    # Conda/venv prefix is usually one level above the Python executable directory.
    env_prefix = py_dir.parent if py_dir.name in {"bin", "Scripts"} else py_dir

    tesseract_candidates = [
        env_prefix / "Library" / "bin" / "tesseract.exe",  # Windows conda
        env_prefix / "bin" / "tesseract",  # macOS/Linux conda/venv
        py_dir / "tesseract",  # Adjacent to executable in some envs
    ]
    for candidate in tesseract_candidates:
        if candidate.exists():
            env["PATH"] = f"{candidate.parent}{os.pathsep}{env.get('PATH', '')}"
            break

    tessdata_candidates = [
        env_prefix / "Library" / "share" / "tessdata",  # Windows conda
        env_prefix / "share" / "tessdata",  # macOS/Linux conda/venv
        env_prefix / "share" / "tesseract" / "tessdata",  # alt layout
    ]
    for candidate in tessdata_candidates:
        if (candidate / "eng.traineddata").exists():
            env["TESSDATA_PREFIX"] = str(candidate)
            break

    return env

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)
    
    apply_ocr(paths, config)