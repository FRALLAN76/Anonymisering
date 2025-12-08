"""Pytest fixtures för menprövningstester."""

import pytest
from pathlib import Path
import fitz  # PyMuPDF


@pytest.fixture
def tmp_pdf(tmp_path: Path) -> Path:
    """Skapa en enkel test-PDF med text."""
    pdf_path = tmp_path / "test_document.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Detta är ett testdokument för menprövning.\n"
        "Här finns känslig information som ska analyseras.\n"
        "Agnes Grenqvist har personnummer 199001011234."
    )
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def tmp_pdf_multipage(tmp_path: Path) -> Path:
    """Skapa en test-PDF med flera sidor."""
    pdf_path = tmp_path / "multipage_document.pdf"
    doc = fitz.open()

    for i in range(3):
        page = doc.new_page()
        page.insert_text(
            (50, 50),
            f"Sida {i + 1}\n"
            f"Detta är innehåll på sida {i + 1}.\n"
            f"Mer text för att testa extraktion."
        )

    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def tmp_empty_pdf(tmp_path: Path) -> Path:
    """Skapa en tom PDF (simulerar skannat dokument utan OCR)."""
    pdf_path = tmp_path / "empty_document.pdf"
    doc = fitz.open()
    doc.new_page()  # Tom sida
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def sample_entities() -> list[dict]:
    """Exempelentiteter för testning."""
    return [
        {"text": "Agnes Grenqvist", "type": "PERSON", "start": 0, "end": 15},
        {"text": "199001011234", "type": "SSN", "start": 50, "end": 62},
        {"text": "070-123 45 67", "type": "PHONE", "start": 100, "end": 113},
    ]


@pytest.fixture
def sample_sensitive_texts() -> list[dict]:
    """Exempel på känsliga texter för klassificeringstestning."""
    return [
        {
            "text": "Patienten har diagnosticerats med depression.",
            "expected_category": "MENTAL_HEALTH",
            "expected_level": "CRITICAL",
        },
        {
            "text": "Modern har dokumenterat alkoholmissbruk sedan 2018.",
            "expected_category": "ADDICTION",
            "expected_level": "CRITICAL",
        },
        {
            "text": "Familjen har ekonomiska svårigheter och skulder hos kronofogden.",
            "expected_category": "ECONOMY",
            "expected_level": "HIGH",
        },
        {
            "text": "Möte hölls på kontoret den 15 januari.",
            "expected_category": "NEUTRAL",
            "expected_level": "LOW",
        },
    ]


@pytest.fixture
def test_data_dir() -> Path:
    """Sökväg till test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def gold_standard_dir() -> Path:
    """Sökväg till gold standard data."""
    return Path(__file__).parent.parent / "validation" / "gold_standard"
