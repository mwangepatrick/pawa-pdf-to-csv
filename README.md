# pawa-pdf-to-csv

A command-line tool to extract tables (or text) from PDF files and save them as CSV.

## Usage

```bash
# Extract tables from a PDF
python pdf_to_csv.py invoice.pdf

# Specify output file
python pdf_to_csv.py invoice.pdf -o results.csv

# Fall back to text extraction if no tables found
python pdf_to_csv.py report.pdf --text-fallback
```

## Requirements

```bash
pip install pdfplumber pandas
```
