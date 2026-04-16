import pytest
from pathlib import Path
from app.converter import convert_pdf, is_valid_pdf


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_is_valid_pdf_with_real_pdf(tmp_path):
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 minimal content")
    assert is_valid_pdf(pdf_file) is True


def test_is_valid_pdf_with_non_pdf(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not a pdf")
    assert is_valid_pdf(txt_file) is False


def test_is_valid_pdf_with_fake_extension(tmp_path):
    fake = tmp_path / "fake.pdf"
    fake.write_text("this is not really a PDF")
    assert is_valid_pdf(fake) is False


def test_convert_pdf_with_tables(tmp_path):
    pytest.importorskip("reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors

    pdf_path = tmp_path / "tables.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    table_data = [
        ["Name", "Age", "City"],
        ["Alice", "30", "Nairobi"],
        ["Bob", "25", "Mombasa"],
    ]
    style = TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
    doc.build([Table(table_data, style=style)])

    output_path = tmp_path / "output.csv"
    result = convert_pdf(pdf_path, output_path, text_fallback=False)
    assert result["status"] == "completed"
    assert result["row_count"] >= 2
    assert result["total_pages"] >= 1
    assert output_path.exists()


def test_convert_pdf_no_tables_no_fallback(tmp_path):
    pytest.importorskip("reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    pdf_path = tmp_path / "nodata.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    doc.build([Paragraph("Just some text, no tables.", styles["Normal"])])

    output_path = tmp_path / "output.csv"
    result = convert_pdf(pdf_path, output_path, text_fallback=False)
    assert result["status"] == "failed"
    assert "No tables found" in result["error"]


def test_convert_pdf_no_tables_with_fallback(tmp_path):
    pytest.importorskip("reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    pdf_path = tmp_path / "textonly.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    doc.build([Paragraph("Some text content here.", styles["Normal"])])

    output_path = tmp_path / "output.csv"
    result = convert_pdf(pdf_path, output_path, text_fallback=True)
    assert result["status"] == "completed"
    assert result["row_count"] >= 1
    assert output_path.exists()
