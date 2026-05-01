import yaml
from pathlib import Path
from chunk_handler import chunk_pdfs
from analysis_handler import analyze_chunks
from json_compiler import compile_jsons

def load_config():
    """Load configuration from settings.yaml."""
    project_root = Path(__file__).parent.parent.parent # Finds the root folder of the project based on this main.py file location
    config_path = project_root / "config" / "settings.yaml" # Sets the path for the settings.yaml file
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
    return

def main():
    
    config = load_config()
    root_path = Path(__file__).parent.parent.parent
    pdf_path = root_path / 'data' / 'pdfs'
    
    chunk_size = config['chunk_size']
    chunk_overlap = config['chunk_overlap']
    
    chunk_pdfs(pdf_path, chunk_size, chunk_overlap, "source_pdf")
    
    #analyze_chunks()
    
    #compile_jsons()
    
    return

if __name__ == "__main__":
    main()