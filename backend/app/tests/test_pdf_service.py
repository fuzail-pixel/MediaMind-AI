# backend/app/tests/test_pdf_service.py

import pytest
import os
import tempfile
from app.services.pdf_service import PDFService
from types import SimpleNamespace
from unittest.mock import patch, mock_open


def create_test_pdf(path: str):
    """Create a minimal real PDF for testing."""
    try:
        import reportlab.pdfgen.canvas as canvas
        c = canvas.Canvas(path)
        c.drawString(100, 750, "Test Document")
        c.drawString(100, 700, "This is a test PDF for MediaMind AI.")
        c.save()
        return True
    except ImportError:
        # reportlab not available — write minimal PDF bytes manually
        with open(path, 'wb') as f:
            f.write(b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n')
        return False


def test_get_page_count_valid():
    """Test page count on a valid PDF."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        path = f.name
    try:
        create_test_pdf(path)
        count = PDFService.get_page_count(path)
        assert isinstance(count, int)
        assert count >= 0
    finally:
        os.unlink(path)


def test_get_page_count_invalid():
    """Test page count on invalid file returns 0."""
    count = PDFService.get_page_count("/nonexistent/file.pdf")
    assert count == 0


def test_is_valid_pdf_nonexistent():
    """Test validity check on non-existent file."""
    result = PDFService.is_valid_pdf("/nonexistent/file.pdf")
    assert result == False


def test_extract_text_nonexistent():
    """Test text extraction on non-existent file returns None."""
    result = PDFService.extract_text("/nonexistent/file.pdf")
    assert result is None


def test_extract_with_pypdf2_invalid():
    """Test PyPDF2 extraction on invalid file."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"not a real pdf")
        path = f.name
    try:
        result = PDFService._extract_with_pypdf2(path)
        assert isinstance(result, str)
    except Exception:
        pass  # expected for invalid PDF
    finally:
        os.unlink(path)


def test_extract_text_uses_pdfplumber_when_text_is_good():
    with patch("app.services.pdf_service.PDFService._extract_with_pdfplumber", return_value="   this is valid extracted text   "), \
         patch("app.services.pdf_service.PDFService._extract_with_pypdf2") as pypdf2_mock:
        result = PDFService.extract_text("dummy.pdf")

    assert result == "this is valid extracted text"
    pypdf2_mock.assert_not_called()


def test_extract_text_falls_back_to_pypdf2_when_pdfplumber_too_short():
    with patch("app.services.pdf_service.PDFService._extract_with_pdfplumber", return_value="short"), \
         patch("app.services.pdf_service.PDFService._extract_with_pypdf2", return_value="fallback text from pypdf2"):
        result = PDFService.extract_text("dummy.pdf")

    assert result == "fallback text from pypdf2"


def test_extract_text_returns_none_when_both_methods_fail():
    with patch("app.services.pdf_service.PDFService._extract_with_pdfplumber", side_effect=Exception("pdfplumber fail")), \
         patch("app.services.pdf_service.PDFService._extract_with_pypdf2", side_effect=Exception("pypdf2 fail")):
        result = PDFService.extract_text("dummy.pdf")

    assert result is None


def test_extract_with_pdfplumber_collects_only_non_empty_pages():
    pages = [
        SimpleNamespace(extract_text=lambda: "Page one text"),
        SimpleNamespace(extract_text=lambda: None),
        SimpleNamespace(extract_text=lambda: "Page three text"),
    ]

    class DummyPDF:
        def __init__(self, pages):
            self.pages = pages

    class DummyCtx:
        def __init__(self, pages):
            self.pdf = DummyPDF(pages)
        def __enter__(self):
            return self.pdf
        def __exit__(self, exc_type, exc, tb):
            return False

    with patch("app.services.pdf_service.pdfplumber.open", return_value=DummyCtx(pages)):
        result = PDFService._extract_with_pdfplumber("dummy.pdf")

    assert "--- Page 1 ---" in result
    assert "Page one text" in result
    assert "--- Page 3 ---" in result
    assert "Page three text" in result
    assert "--- Page 2 ---" not in result


def test_extract_with_pypdf2_collects_only_non_empty_pages():
    pages = [
        SimpleNamespace(extract_text=lambda: "First"),
        SimpleNamespace(extract_text=lambda: ""),
        SimpleNamespace(extract_text=lambda: "Third"),
    ]
    fake_reader = SimpleNamespace(pages=pages)

    with patch("builtins.open", mock_open(read_data=b"%PDF-1.4")), \
         patch("app.services.pdf_service.PyPDF2.PdfReader", return_value=fake_reader):
        result = PDFService._extract_with_pypdf2("dummy.pdf")

    assert "--- Page 1 ---" in result
    assert "First" in result
    assert "--- Page 3 ---" in result
    assert "Third" in result
    assert "--- Page 2 ---" not in result


def test_is_valid_pdf_true_when_pages_exist():
    class DummyPDF:
        pages = [object()]

    class DummyCtx:
        def __enter__(self):
            return DummyPDF()
        def __exit__(self, exc_type, exc, tb):
            return False

    with patch("app.services.pdf_service.pdfplumber.open", return_value=DummyCtx()):
        assert PDFService.is_valid_pdf("dummy.pdf") is True