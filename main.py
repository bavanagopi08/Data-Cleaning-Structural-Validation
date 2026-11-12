import csv
import os
import re
from collections import Counter
from datetime import datetime
from statistics import median

# 1. File paths
input_file = "dataset/marketing_campaign.csv"
output_folder = "output"

os.makedirs(output_folder, exist_ok=True)

# 2. Load dataset
print("Loading dataset...")

with open(input_file, "r", encoding="utf-8-sig", newline="") as f:
    sample = f.read(4096)
    f.seek(0)

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"

    reader = csv.reader(f, delimiter=delimiter)
    raw_headers = next(reader)

    headers = [
        re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", h.strip().lower())).strip("_")
        for h in raw_headers
    ]

    rows = []
    for values in reader:
        if not any(str(v).strip() for v in values):
            continue

        row = {}
        for i, header in enumerate(headers):
            row[header] = values[i].strip() if i < len(values) else ""
        rows.append(row)

original_rows = len(rows)
original_columns = len(headers)

print("Original rows:", original_rows)
print("Original columns:", original_columns)

# 3. Standardize missing values
missing_markers = {"", "na", "n/a", "null", "none", "?", "nan"}

for row in rows:
    for column in headers:
        value = str(row[column]).strip()
        if value.lower() in missing_markers:
            row[column] = ""
        else:
            row[column] = value

missing_before = sum(
    1 for row in rows for col in headers if row[col] == ""
)

# 4. Remove duplicate records
unique_rows = []
seen = set()

for row in rows:
    record = tuple(row[col] for col in headers)

    if record not in seen:
        seen.add(record)
        unique_rows.append(row)

duplicates_removed = len(rows) - len(unique_rows)
rows = unique_rows

# 5. Identify numeric and date columns
date_columns = [
    col for col in headers
    if "date" in col or col.startswith("dt_")
]

date_formats = [
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%y",
    "%d/%m/%y"
]

# 6. Standardize date columns
for column in date_columns:
    for row in rows:
        value = row[column]

        if value:
            parsed_date = None

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue

            if parsed_date:
                row[column] = parsed_date.strftime("%Y-%m-%d")
            else:
                row[column] = ""

# 7. Handle missing values
numeric_columns = []

for column in headers:
    if column in date_columns:
        continue

    values = [row[column] for row in rows if row[column] != ""]

    if values:
        try:
            for value in values:
                float(value.replace(",", ""))
            numeric_columns.append(column)
        except ValueError:
            pass

for column in headers:
    values = [row[column] for row in rows if row[column] != ""]

    if not values:
        continue

    if column in numeric_columns:
        numbers = [float(v.replace(",", "")) for v in values]
        fill_value = str(median(numbers))

        for row in rows:
            if row[column] == "":
                row[column] = fill_value

    else:
        fill_value = Counter(values).most_common(1)[0][0]

        for row in rows:
            if row[column] == "":
                row[column] = fill_value

# 8. Final validation
missing_after = sum(
    1 for row in rows for col in headers if row[col] == ""
)

remaining_duplicates = len(rows) - len({
    tuple(row[col] for col in headers) for row in rows
})

# 9. Save cleaned dataset
cleaned_file = os.path.join(
    output_folder, "cleaned_marketing_campaign.csv"
)

with open(cleaned_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)

# 10. Generate cleaning report
report_file = os.path.join(output_folder, "cleaning_report.txt")

with open(report_file, "w", encoding="utf-8") as f:
    f.write("DATA CLEANING & STRUCTURAL VALIDATION REPORT\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Original rows: {original_rows}\n")
    f.write(f"Original columns: {original_columns}\n")
    f.write(f"Cleaned rows: {len(rows)}\n")
    f.write(f"Duplicate records removed: {duplicates_removed}\n")
    f.write(f"Missing values before cleaning: {missing_before}\n")
    f.write(f"Missing values after cleaning: {missing_after}\n")
    f.write(f"Remaining duplicates: {remaining_duplicates}\n")
    f.write(f"Numeric columns: {len(numeric_columns)}\n")
    f.write(f"Date columns: {len(date_columns)}\n")
    f.write("\nCleaning process completed successfully.\n")

# 11. Display results
print("\nDATA CLEANING COMPLETED!")
print("------------------------------")
print("Original rows:", original_rows)
print("Cleaned rows:", len(rows))
print("Duplicates removed:", duplicates_removed)
print("Missing values before:", missing_before)
print("Missing values after:", missing_after)
print("Remaining duplicates:", remaining_duplicates)
print("\nCleaned dataset saved:", cleaned_file)
print("Cleaning report saved:", report_file)