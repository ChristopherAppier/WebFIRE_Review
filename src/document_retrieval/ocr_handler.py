import subprocess
import tempfile
import os
import sys
from pathlib import Path
import yaml


def _load_settings(project_root):
    """Load settings.yml with a safe empty fallback."""
    config_path = project_root / "config" / "settings.yml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_ocr_jobs_per_file(settings):
    """Read OCRmyPDF jobs-per-file from settings with safe fallback."""
    try:
        jobs = int(settings.get("ocr_jobs_per_file", 1))
        return max(1, jobs)
    except Exception:
        return 1


def _load_ocr_renderer(settings):
    """Read OCRmyPDF renderer from settings with safe fallback."""
    renderer = str(settings.get("ocr_pdf_renderer", "auto")).strip().lower()
    if renderer in {"auto", "hocr", "sandwich"}:
        return renderer
    return "auto"


def _build_ocr_env():
    """Create subprocess env with explicit Tesseract and tessdata locations."""
    env = os.environ.copy()
    env_root = Path(sys.executable).resolve().parent

    tesseract_candidates = [
        env_root / "Library" / "bin" / "tesseract.exe",  # Windows conda
        env_root / "bin" / "tesseract",  # macOS/Linux
    ]
    for candidate in tesseract_candidates:
        if candidate.exists():
            env["PATH"] = f"{candidate.parent}{os.pathsep}{env.get('PATH', '')}"
            break

    tessdata_candidates = [
        env_root / "Library" / "share" / "tessdata",  # Windows conda
        env_root / "share" / "tessdata",  # macOS/Linux
    ]
    for candidate in tessdata_candidates:
        if (candidate / "eng.traineddata").exists():
            env["TESSDATA_PREFIX"] = str(candidate)
            break

    return env

def apply_ocr(project_root):
    """
    Apply OCR to every PDF in the specified folder.
    
    Args:
        folder_path: Path to folder containing PDF files
    """
    
    settings = _load_settings(project_root)
    folder_path = Path(project_root / "data" / "pdfs")
    jobs_per_file = _load_ocr_jobs_per_file(settings)
    renderer = _load_ocr_renderer(settings)
    ocr_env = _build_ocr_env()

    for pdf_file in sorted(folder_path.glob("*.pdf")):
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", dir=pdf_file.parent, delete=False
        ) as tmp_file:
            temp_output = Path(tmp_file.name)

        cmd = [
            sys.executable,
            "-m",
            "ocrmypdf",
            "--jobs",
            str(jobs_per_file),
            "--pdf-renderer",
            renderer,
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

if __name__ == "__main__":
    
    project_root = Path(__file__).parent.parent.parent
    
    apply_ocr(project_root)