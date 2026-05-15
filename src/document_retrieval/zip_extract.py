import zipfile
import io
from pathlib import Path

def recursive_zip_extract(raw_path):
    
    """Extracts the contents of all zip files in a folder on a loop until the list of files is the same between two runs, which indicates that it has extracted everything it can. The purpose is to extract nested zips."""
    
    loop_num = 1 #index for loop number
    loop_one_extractions = 0
    
    #Sets the previous_file_list to an empty array for loop 1
    if loop_num == 1:
        previous_file_list = []
        file_list = [f.name for f in Path(raw_path).iterdir() if f.is_file()]

    # Main recursive extraction loop
    while file_list != previous_file_list and loop_num < 5: 
        
        # Creates the list of files in the folder before the extraction loop
        previous_file_list = file_list.copy()
        
        for file_name in file_list:
            if not file_name.endswith('.zip'): 
                continue # Skips to next file if this one is not a zip
            
            zip_path = raw_path / file_name
            
            # First attempt: standard open (handles most zip files)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(zip_path.parent)
                    filenames = zf.namelist()
                
            except zipfile.BadZipFile:
                # Second attempt: find zip signature manually and open from offset
                offset = find_zip_offset(zip_path)
                if offset == 0:
                    continue
                with open(zip_path, 'rb') as f:
                    f.seek(offset)
                    data = io.BytesIO(f.read())
                try:    
                    with zipfile.ZipFile(data, 'r') as zf:
                        zf.extractall(zip_path.parent)
                        filenames = zf.namelist()
                except zipfile.BadZipFile:
                    continue
            try:
                for name in filenames:
                    extracted_file = zip_path.parent / name
                    if not extracted_file.exists() or extracted_file.stat().st_size == 0:
                        raise ValueError(f'Extraction failed for {name}: file missing or empty')
                
                zip_path.unlink()
                if loop_num == 1:
                    loop_one_extractions += 1
            except ValueError as e:
                print(f'Could not validate extracted files for {zip_path.name}: {e}')
            except OSError as e:
                print(f'Could not finalize extraction for {zip_path.name}: {e}')

        # Creates a list of files in the folder after the extraction loop
        file_list = [f.name for f in Path(raw_path).iterdir() if f.is_file()]
        
        # Iterating the loop count
        loop_num += 1

    return loop_one_extractions


def find_zip_offset(zip_path: Path) -> int:
    """Find the offset where the actual zip data begins (handles prepended content)."""
    with open(zip_path, 'rb') as f:
        while chunk := f.read(65536):  # Read 64KB at a time
            if b'PK\x03\x04' in chunk:
                return chunk.find(b'PK\x03\x04')
    return 0
    

def rename_zip_to_pdf(raw_path):

    file_list = [f.name for f in Path(raw_path).iterdir() if f.is_file()]  
    
    zips_renamed = 0

    for file_name in file_list:
        if file_name.endswith('.zip'):
            try: 
                old_path = raw_path / file_name
                new_path = old_path.with_suffix('.pdf')
                old_path.rename(new_path)
                zips_renamed += 1
            except (Exception):
                pass

    return zips_renamed


def file_sort(raw_path):

    file_list = [f.name for f in Path(raw_path).iterdir() if f.is_file()]
    spreadsheets_moved = pdfs_moved = other_moved = 0 # Trackers for files moved

    # Main loop through files
    for file_name in file_list:
        
        # Moving Spreadsheets
        if file_name.endswith(('.xls', '.xlsx', 'xlsm')):
            spreadsheets_moved += 1
            src = raw_path / file_name
            dest_dir = raw_path.parent / "spreadsheets"
            dest = dest_dir / file_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            src.rename(dest)
        
        # Moving PDFs
        elif file_name.endswith(('.pdf', '.PDF')):
            pdfs_moved += 1
            src = raw_path / file_name
            dest_dir = raw_path.parent / "pdfs"
            dest = dest_dir / file_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            src.rename(dest)
            
        # Moving other files
        else:
            other_moved += 1
            src = raw_path / file_name
            dest_dir = raw_path.parent / "other"
            dest = dest_dir / file_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            src.rename(dest)
        
    return spreadsheets_moved, pdfs_moved, other_moved


def print_statistics(zips_extracted, zips_renamed, files_moved, num_original_zips):
    
    spreadsheets = files_moved[0]
    pdfs = files_moved[1]
    other = files_moved[2]
    zip_eff = round(100 * (zips_extracted + zips_renamed) / num_original_zips)
    
    print('*'*50)
    print('Zip Extraction Statistics')
    print('*'*50)
    print(f'Total starting ZIPs: {num_original_zips}')
    print(f'WebFIRE ZIPs extracted: {zips_extracted}')
    print(f'ZIPs converted to pdf: {zips_renamed}')
    print(f'ZIP extraction/renaming efficiency {zip_eff}%')
    print(f'Spreadsheets extracted: {spreadsheets}')
    print(f'PDFs extracted: {pdfs}')
    print(f'Other files extracted: {other}')
    print('*'*50)

    return


def extract_and_route_files(project_root):
    
    # Logs the original number of ZIPs downloaded from WebFIRE
    raw_path = project_root / "data" / "raw"
    num_original_zips = len([f for f in raw_path.iterdir() if f.is_file() and not f.name.startswith('.') and f.name.endswith('.zip')])
    
    # Extracts all zips recursively and logs number extracted in loop 1
    zips_extracted = recursive_zip_extract(raw_path) 
    
    # Renames the remaining "zips" to pdfs to handle WebFIRE's error that names pdf files as .zip
    zips_renamed = rename_zip_to_pdf(raw_path) 
    
    files_moved = file_sort(raw_path) #this should return 3 values, spreadsheets, pdfs, other
    
    #print_statistics(zips_extracted, zips_renamed, files_moved, num_original_zips)
    
    return

if __name__ == "__main__":
    extract_and_route_files()