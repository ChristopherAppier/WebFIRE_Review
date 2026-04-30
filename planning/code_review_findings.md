# Code Review: Flaws in src/document_retrieval Python Scripts

## Context

I've reviewed the Python scripts in `src/document_retrieval/` and identified multiple flaws across security, resource management, error handling, and logic.

---

## Critical Flaws Found

### 1. **Security Vulnerability: Command Injection in ocr_handler.py**
**File:** `src/document_retrieval/ocr_handler.py` (line 18)

```python
cmd = f'ocrmypdf -s -q --invalidate-digital-signatures "{pdf_file}" "{pdf_file}"'
subprocess.run(cmd, check=True, shell=True)
```

**Issue:** Using `shell=True` with f-string variable interpolation allows arbitrary command injection. An attacker could craft a PDF filename containing `; rm -rf /` or similar.

**Impact:** HIGH - Arbitrary command execution via crafted filenames.

**Fix:** Use `subprocess.run()` with a list of arguments instead of shell=True:
```python
subprocess.run([
    'ocrmypdf', '-s', '-q',
    '--invalidate-digital-signatures', str(pdf_file),
    str(pdf_file)
], check=True)
```

---

### 2. **Resource Leak: Unclosed Session in download_handler.py**
**File:** `src/document_retrieval/download_handler.py` (lines 174, 182-216)

```python
def fetch_all_reports(...):
    session = build_session()
    # ... loop through reports ...
    return {...}
```

**Issue:** The `requests.Session` object created in `build_session()` is never closed. Each request within the session creates a connection pool entry; with large report batches, this causes connection exhaustion.

**Impact:** MEDIUM - Resource exhaustion and eventual API failures.

**Fix:** Wrap in `with` context or explicitly call `session.close()`:
```python
def fetch_all_reports(start_date, end_date, state, project_root):
    session = build_session()
    try:
        # ... download logic ...
    finally:
        session.close()
```

---

### 3. **Resource Leak: Files Extracted but Not Closed**
**File:** `src/document_retrieval/zip_extract.py` (lines 38-42, 46)

```python
with open(zip_path, 'rb') as f:
    f.seek(offset)
    data = io.BytesIO(f.read())
try:
    zf = zipfile.ZipFile(data, 'r')
zf.extractall(zip_path.parent)  # Line 46 - context manager not used!
zip_path.unlink()
```

**Issue:** `zf.extractall()` doesn't close the ZipFile. On error paths, the file handle remains open.

**Impact:** MEDIUM - File descriptor exhaustion on systems with limited open file limits.

**Fix:** Use context manager or explicitly close:
```python
with zipfile.ZipFile(data, 'r') as zf:
    zf.extractall(zip_path.parent)
```

---

### 4. **Logic Error: Incorrect YAML Config Loading**
**File:** `src/document_retrieval/main.py` (lines 10-16)

```python
def load_config():
    config_path = project_root / "config" / "settings.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)    # Opens file, returns result
    return yaml.safe_load(config_path)  # DEAD CODE: Never executes!
```

**Issue:** Second `yaml.safe_load(config_path)` passes a `Path` object instead of file content. This line is unreachable dead code.

**Impact:** LOW - Confusing but harmless (dead code doesn't affect runtime).

**Fix:** Remove dead code:
```python
def load_config():
    config_path = project_root / "config" / "settings.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
```

---

### 5. **Error Handling Bug: Misclassified Errors in download_handler.py**
**File:** `src/document_retrieval/download_handler.py` (lines 156, 208)

```python
# Line 156 - wrong error message
return False, None, f"Unexpected content type: {r.headers.get('Content-Type', 'unknown')}"

# Line 208 - wrong error field population
'error': file_type if not success else None,
```

**Issue:** When file type detection fails, `file_type` contains the Content-Type header string. This gets stored as the error message, but the logic is confusing.

**Impact:** MEDIUM - Errors are logged incorrectly, making debugging harder.

**Fix:** Use explicit boolean flag:
```python
if not r.content[:2] == b"PK":
    if r.content[:4] == b"%PDF":
        file_type = "pdf"
        return True, filepath, file_type
    else:
        return False, None, f"Content-Type: {r.headers.get('Content-Type')}"
```

---

### 6. **Logic Error: Invalid PDF Content Detection**
**File:** `src/document_retrieval/download_handler.py` (line 150)

```python
if r.content[:4] == b"%PDF":
    file_type = "pdf"
    return True, filepath, file_type
```

**Issue:** PDFs start with `%PDF-`, not just `%PDF`. A file starting with `%PDF` could be a false positive.

**Impact:** MEDIUM - Incorrectly labeled non-PDF files as PDFs.

**Fix:** Check for actual PDF header:
```python
if r.content[:5] == b"%PDF-":
    file_type = "pdf"
```

---

### 7. **Race Condition: File Exists Check Then Create**
**File:** `src/document_retrieval/download_handler.py` (lines 135-136)

```python
filepath = output_dir / f"{doc_id}.zip"

if filepath.exists():
    return True, filepath, "already_cached"

try:
    r = session.get(...)
```

**Issue:** Between `exists()` check and actual download, another process could create the file.

**Impact:** LOW - Rare race condition, but can cause skipped downloads.

**Fix:** Download to temp file, then rename:
```python
import tempfile
import shutil

temp_file = output_dir / f"{doc_id}.zip.tmp"
r = session.get(...)
temp_file.write_bytes(r.content)
temp_file.rename(filepath)  # Atomic on POSIX
```

---

### 8. **Error Handling: Empty Exception Catch**
**File:** `src/document_retrieval/ocr_handler.py` (lines 20-21)

```python
except (Exception):  # Catches EVERYTHING, including KeyboardInterrupt!
    continue
```

**Impact:** HIGH - Swallows all errors including `KeyboardInterrupt`, making it impossible to stop the process.

**Fix:** Catch specific exceptions:
```python
except subprocess.CalledProcessError as e:
    print(f"OCR failed for {pdf_file.name}: {e}")
    continue
except FileNotFoundError as e:
    print(f"ocrmypdf not found: {e}")
    continue
```

---

### 9. **Error Handling: Bare Exception in zip_extract.py**
**File:** `src/document_retrieval/zip_extract.py` (lines 57-58)

```python
except (zipfile.BadZipFile, Exception):  # Exception is redundant!
    pass
```

**Impact:** MEDIUM - `Exception` is a parent class of `BadZipFile`, making the tuple redundant. Silently swallowing all other exceptions hides bugs.

**Fix:** Remove bare `Exception`:
```python
except zipfile.BadZipFile:
    print(f"Could not extract: {zip_path.name}")
    pass
```

---

### 10. **Logic Error: Missing Statistics Output**
**File:** `src/document_retrieval/zip_extract.py` (line 171)

```python
#print_statistics(zips_extracted, zips_renamed, files_moved, num_original_zips)
```

**Issue:** Statistics function is commented out, leaving the user without visibility into processing results.

**Impact:** LOW - UX issue, not a bug.

**Fix:** Uncomment:
```python
print_statistics(zips_extracted, zips_renamed, files_moved, num_original_zips)
```

---

### 11. **Inefficiency: Linear Search for ZIP Offset**
**File:** `src/document_retrieval/zip_extract.py` (lines 71-75)

```python
def find_zip_offset(zip_path: Path) -> int:
    with open(zip_path, 'rb') as f:
        data = f.read()  # Loads entire file into memory!
    offset = data.find(b'PK\x03\x04')
    return offset if offset != -1 else 0
```

**Issue:** Reads entire file into memory before searching. For large ZIPs, this is wasteful.

**Impact:** MEDIUM - Memory inefficiency on large corrupted archives.

**Fix:** Stream reading:
```python
def find_zip_offset(zip_path: Path) -> int:
    with open(zip_path, 'rb') as f:
        while chunk := f.read(65536):  # Read 64KB at a time
            if b'PK\x03\x04' in chunk:
                return chunk.find(b'PK\x03\x04')
    return 0
```

---

### 12. **Error Handling: Timer Always Defaults to UTC**
**File:** `src/document_retrieval/timer_manager.py` (lines 20, 27)

```python
start = (datetime.utcnow() - timedelta(days=default_interval))
end = datetime.utcnow()
```

**Issue:** Always uses UTC timezone. If the server runs in a different timezone, date ranges will be wrong, potentially missing data.

**Impact:** MEDIUM - Data inconsistency across timezones.

**Fix:** Use system timezone:
```python
start = datetime.now() - timedelta(days=default_interval)
end = datetime.now()
```

---

## Summary Table

| File | Issue | Severity | Category |
|------|-------|-|-|
| `ocr_handler.py` | Command injection via `shell=True` | **HIGH** | Security |
| `ocr_handler.py` | Swallows `KeyboardInterrupt` | **HIGH** | Error Handling |
| `download_handler.py` | Session not closed | MEDIUM | Resource Leak |
| `download_handler.py` | Race condition on file exists | LOW | Concurrency |
| `download_handler.py` | Invalid PDF header check | MEDIUM | Logic |
| `download_handler.py` | Misclassified errors | MEDIUM | Error Handling |
| `zip_extract.py` | Unclosed ZipFile handles | MEDIUM | Resource Leak |
| `zip_extract.py` | Bare `Exception` catch | MEDIUM | Error Handling |
| `zip_extract.py` | Whole-file read for offset | MEDIUM | Performance |
| `main.py` | Dead code in load_config | LOW | Code Quality |
| `timer_manager.py` | Always uses UTC timezone | MEDIUM | Logic |

---

## Verification Plan

To verify fixes:
1. Create test PDFs with special characters in names
2. Test OCR process doesn't crash on injection attempts
3. Verify session closes after large batch downloads
4. Test corrupted ZIPs don't leave open file handles
5. Verify statistics are printed after extraction
6. Test timezone handling with `TZ` environment variable
