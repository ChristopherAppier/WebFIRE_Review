import magic
from pathlib import Path

folder_name = Path('/Users/chrisappier/Documents/WebFIRE_Review/data/raw')

for file_name in folder_name.iterdir():
    # Identify by MIME type (more useful)
    mime_type = magic.from_file(file_name, mime=True)
    print(file_name.name, mime_type)