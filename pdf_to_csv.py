#!/usr/bin/env python3
"""
PDF to CSV Converter
Extracts tables (or text) from a PDF and saves them as CSV files.

Usage:
    python pdf_to_csv.py input.pdf
    python pdf_to_csv.py input.pdf --output output.csv
    python pdf_to_csv.py input.pdf --all-pages
"""

import sys
import argparse
import csv
import pdfplumber
import pandas as pd
from pathlib import Path


def extract_tables(pdf_path: str) -> list[pd.DataFrame]:
    """Extract all tables from all pages of the PDF."""
    frames = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                # Use first row as header if it looks like one
                header = table[0]
                rows = table[1:]
                if any(cell for cell in header):  # non-empty header row
                    df = pd.DataFrame(rows, columns=header)
                else:
                    df = pd.DataFrame(table)
                df.insert(0, "_page", page_num)
                frames.append(df)
    return frames


def extract_text_as_csv(pdf_path: str) -> list[list[str]]:
    """Fallback: extract text lines as single-column rows."""
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if line:
                    rows.append([page_num, line])
    return rows


def save_csv(df: pd.DataFrame, output_path: str) -> None:
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description="Convert PDF tables to CSV")
    parser.add_argument("input", help="Path to the input PDF file")
    parser.add_argument("-o", "--output", help="Output CSV file path (default: same name as input)")
    parser.add_argument(
        "--text-fallback",
        action="store_true",
        help="If no tables found, extract raw text lines instead",
    )
    args = parser.parse_args()

    pdf_path = Path(args.input)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else pdf_path.with_suffix(".csv")

    print(f"Reading: {pdf_path}")
    tables = extract_tables(str(pdf_path))

    if tables:
        combined = pd.concat(tables, ignore_index=True)
        save_csv(combined, str(output_path))
        print(f"Extracted {len(tables)} table(s), {len(combined)} rows -> {output_path}")
    elif args.text_fallback:
        rows = extract_text_as_csv(str(pdf_path))
        if rows:
            df = pd.DataFrame(rows, columns=["page", "text"])
            save_csv(df, str(output_path))
            print(f"No tables found. Extracted {len(rows)} text lines -> {output_path}")
        else:
            print("No content extracted from PDF.", file=sys.stderr)
            sys.exit(1)
    else:
        print(
            "No tables found in the PDF.\n"
            "Tip: use --text-fallback to extract raw text lines instead.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
