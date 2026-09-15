"""Count documents listed in the `Document List` column of report_table.csv.

`Document List` entries are expected to be pipe-separated (|).
"""

import csv
from pathlib import Path


project_root = Path(__file__).resolve().parents[2]
report_table_path = project_root / "data" / "http" / "report_table.csv"

with report_table_path.open(mode="r", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    rows = list(reader)

total_documents = 0

for row in rows:
    raw_doc_list = (row.get("Document List") or "").strip()

    if not raw_doc_list:
        row["Num Reports"] = 0
        continue

    # Ignore empty entries if there are leading/trailing separators.
    documents = [doc.strip() for doc in raw_doc_list.split("|") if doc.strip()]
    row["Num Reports"] = len(documents)
    total_documents += row["Num Reports"]

print(f"Rows processed: {len(rows)}")
print(f"Total documents listed in 'Document List': {total_documents}")
