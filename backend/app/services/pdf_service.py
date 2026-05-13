# backend/app/services/pdf_service.py

import pdfplumber
import PyPDF2
import os
from typing import Optional


class PDFService:

    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """
        Extract text from a PDF file.
        Tries pdfplumber first (better for complex layouts),
        falls back to PyPDF2 if that fails.
        """
        text = None

        # Method 1 — pdfplumber (handles tables, columns better)
        try:
            text = PDFService._extract_with_pdfplumber(file_path)
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2...")

        # Method 2 — PyPDF2 fallback
        if not text or len(text.strip()) < 10:
            try:
                text = PDFService._extract_with_pypdf2(file_path)
            except Exception as e:
                print(f"PyPDF2 also failed: {e}")
                return None

        return text.strip() if text else None


    @staticmethod
    def _extract_with_pdfplumber(file_path: str) -> str:
        """Extract text page by page using pdfplumber."""
        pages_text = []

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(f"--- Page {i+1} ---\n{page_text}")

        return "\n\n".join(pages_text)


    @staticmethod
    def _extract_with_pypdf2(file_path: str) -> str:
        """Fallback extraction using PyPDF2."""
        pages_text = []

        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(f"--- Page {i+1} ---\n{page_text}")

        return "\n\n".join(pages_text)


    @staticmethod
    def get_page_count(file_path: str) -> int:
        """Get total number of pages in a PDF."""
        try:
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0


    @staticmethod
    def is_valid_pdf(file_path: str) -> bool:
        """Check if the file is a valid readable PDF."""
        try:
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages) > 0
        except Exception:
            return False