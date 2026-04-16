from pathlib import Path

import pandas as pd
import pdfplumber


def is_valid_pdf(file_path: Path) -> bool:
    """Check if a file is a valid PDF by reading magic bytes."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
        return header == b"%PDF-"
    except (OSError, IOError):
        return False


def convert_pdf(
    pdf_path: Path,
    output_path: Path,
    text_fallback: bool = False,
) -> dict:
    """
    Convert a PDF to CSV.

    Returns a dict with keys:
        status: "completed" | "failed"
        total_pages: int
        row_count: int (if completed)
        error: str (if failed)
    """
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            total_pages = len(pdf.pages)
            frames = []

            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    header = table[0]
                    rows = table[1:]
                    if any(cell for cell in header):
                        df = pd.DataFrame(rows, columns=header)
                    else:
                        df = pd.DataFrame(table)
                    df.insert(0, "_page", page_num)
                    frames.append(df)

            if frames:
                combined = pd.concat(frames, ignore_index=True)
                combined.to_csv(str(output_path), index=False, encoding="utf-8-sig")
                return {
                    "status": "completed",
                    "total_pages": total_pages,
                    "row_count": len(combined),
                }

            if text_fallback:
                text_rows = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    for line in text.splitlines():
                        line = line.strip()
                        if line:
                            text_rows.append([page_num, line])

                if text_rows:
                    df = pd.DataFrame(text_rows, columns=["page", "text"])
                    df.to_csv(str(output_path), index=False, encoding="utf-8-sig")
                    return {
                        "status": "completed",
                        "total_pages": total_pages,
                        "row_count": len(df),
                    }

            return {
                "status": "failed",
                "total_pages": total_pages,
                "row_count": 0,
                "error": "No tables found in the PDF.",
            }

    except Exception as e:
        return {
            "status": "failed",
            "total_pages": 0,
            "row_count": 0,
            "error": f"Processing error: {str(e)}",
        }
