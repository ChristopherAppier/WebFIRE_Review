import zipfile
import io
from pathlib import Path
from typing import Dict, List

def find_zip_offset(zip_path: Path) -> int:
    """Find the offset where the actual zip data begins (handles prepended content)."""
    with open(zip_path, 'rb') as f:
        data = f.read()
    offset = data.find(b'PK\x03\x04')
    return offset if offset != -1 else 0


def extract_zip_and_delete(zip_path: Path) -> Dict:
    """
    Extract zip contents to the same directory, then delete the original zip file.
    Handles prepended PDF bytes by searching for ZIP signature and extracting from offset.
    If no PK signature found, marks file as 'converted' (assumes bare PDF).
    """
    result = {
        'zip': str(zip_path),
        'status': 'success',
        'extracted_files': [],
        'total_files': 0,
        'converted_to_pdf': False,
        'nested_found': False
    }
    
    try:
        # First attempt: standard open (handles most zip files)
        try:
            zf = zipfile.ZipFile(zip_path, 'r')
        except zipfile.BadZipFile:
            # Second attempt: find zip signature manually and open from offset
            offset = find_zip_offset(zip_path)
            if offset == 0:
                # No PK signature - assume it's a bare PDF, mark as converted
                print(f"  No PK signature found, marking as 'converted' (bare PDF)")
                result['status'] = 'converted'
                result['converted_to_pdf'] = True
                return result
            print(f"  Prepended data detected, zip starts at byte {offset}")
                with open(zip_path, 'rb') as f:
                    f.seek(offset)
                    data = io.BytesIO(f.read())
                zf = zipfile.ZipFile(data, 'r')
        
        with zf:
            filenames = zf.namelist()
            zf.extractall(Path(zip_path).parent)
            
            # Verify extraction integrity
            for name in filenames:
                extracted_file = Path(zip_path).parent / name
                if not extracted_file.exists() or extracted_file.stat().st_size == 0:
                    raise Exception(f"Extraction failed for {name}: File missing or empty")
        
        result['extracted_files'] = filenames
        result['total_files'] = len(filenames)
        
        # Delete original zip
        zip_path.unlink()
        result['zip_deleted'] = True
        
    except zipfile.BadZipFile as e:
        result['status'] = 'error'
        result['error'] = f'Invalid zip: {str(e)}'
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
    
    return result


def extract_nested_zips(extract_dir: Path) -> int:
    """
    Recursively extract any ZIP files found in the extracted directory.
    """
    nested_count = 0
    
    for zip_file in extract_dir.glob('*.zip'):
        if zip_file.exists():
            print(f"  Nested zip found: {zip_file.name}")
            result = extract_zip_and_delete(zip_file)
            if result['status'] == 'success':
                nested_count += 1
                print(f"  Nested zip extracted: {zip_file.name} -> {result['total_files']} files")
    
    return nested_count


def extract_multiple_zips(zip_files: List[Path]) -> List[Dict]:
    """
    Extract multiple zip files.
    """
    results = []  # List of individual extraction results
    
    print(f"Extracting {len(zip_files)} zip files")
    
    for zip_file in zip_files:
        if zip_file.exists():
            result = extract_zip_and_delete(zip_file)
            results.append(result)
            
            if result['status'] == 'success':
                pass
            elif result['status'] == 'error':
                pass
            elif result['status'] == 'converted':
                pass
        
        # Extract nested zips from extracted folder
        extract_dir = Path(zip_file).parent
        nested_found = extract_nested_zips(extract_dir)
        if nested_found > 0:
            print(f"  Found {nested_found} nested zip(s)")
            
    return results


# Main function for CLI use
def extract_and_route_files(config):
    """
    Process all zip files in a directory with recursive extraction.
    """
    project_root = Path(__file__).parent.parent.parent
    
    directory = project_root / config['directories']['raw_data_dir']
    
    zip_files = list(directory.glob('*.zip'))
    
    if not zip_files:
        print(f"No zip files found in {directory}")
        return
    
    print(f"Found {len(zip_files)} zip files to process")
    
    iteration = 0
    stable_iterations = 3
    previous_file_count = len(zip_files)
    all_results = []
    
    while iteration < stable_iterations:
        iteration += 1
        print(f"\n=== Iteration {iteration} ===")
        zip_files = list(directory.glob('*.zip'))
        print(f"Checking {len(zip_files)} zip files")
        
        if not zip_files:
            print("No more zip files to process")
            break
        
        iteration_results = extract_multiple_zips(zip_files)
        all_results.extend(iteration_results)
        
        # Get remaining zip files
        remaining_count = len(zip_files)
        print(f"Iteration {iteration}: {remaining_count} remaining zips")
        
        # If no change from previous iteration, we're stable
        if remaining_count == previous_file_count:
            print(f"Stable: no change from previous iteration")
            break
        
        # Update previous count
        previous_file_count = remaining_count
        
        # If all zips were extracted this iteration, we're done
        if remaining_count == 0:
            print("All zips extracted successfully")
            break
    
    # Final pass with remaining zips
    zip_files = list(directory.glob('*.zip'))
    print(f"\n=== Final pass: {len(zip_files)} remaining zips ===")
    final_results = extract_multiple_zips(zip_files)
    all_results.extend(final_results)
    
    # Calculate final statistics
    success_count = len([r for r in all_results if r['status'] == 'success'])
    failed_count = len([r for r in all_results if r['status'] == 'error'])
    converted_count = len([r for r in all_results if r['status'] == 'converted' or r['status'] == 'deleted_already'])
    extracted_count = sum(r.get('total_files', 0) for r in all_results if r['status'] == 'success')
    
    results = {
        'total': success_count + failed_count + converted_count,
        'successful': success_count,
        'failed': failed_count,
        'converted': converted_count,
        'total_extracts': extracted_count
    }
    
    if results['total'] > 0:
        results['success_rate'] = (results['successful'] / results['total'] * 100)
    
    print(f"\nResults:")
    print(f"  Processed: {results['total']} files")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Converted to PDF: {results['converted']}")
    print(f"  Total extracts: {results['total_extracts']} files")
    print(f"  Success rate: {results['success_rate']:.1f}%")
    
    # Convert remaining zip files to pdf
    converted_count = 0
    for zip_file in directory.glob('*.zip'):
        print(f"Converting {zip_file.name} to pdf")
        try:
            zip_file.rename(zip_file.with_suffix('.pdf'))
            converted_count += 1
        except Exception as e:
            print(f"  Failed to convert {zip_file.name}: {e}")
    
    print(f"  Converted {converted_count} files to PDF")
    
    return results
