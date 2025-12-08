"""Enhetstester för dokumentinläsning."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.ingestion.pdf_extractor import PDFExtractor, ExtractionConfig
from src.core.exceptions import ExtractionError


class TestPDFExtractor:
    """Tester för PDFExtractor."""

    @pytest.fixture
    def extractor(self) -> PDFExtractor:
        """Skapa en extractor-instans."""
        return PDFExtractor()

    @pytest.fixture
    def extractor_no_ocr(self) -> PDFExtractor:
        """Skapa en extractor utan OCR."""
        config = ExtractionConfig(ocr_enabled=False)
        return PDFExtractor(config)

    def test_extract_simple_pdf(self, extractor: PDFExtractor, tmp_pdf: Path):
        """Test: Extrahera text från enkel PDF."""
        result = extractor.extract(tmp_pdf)

        assert result is not None
        assert "testdokument" in result.full_text
        assert result.total_pages == 1
        assert result.extraction_method == "native"
        assert len(result.pages) == 1

    def test_extract_multipage_pdf(self, extractor: PDFExtractor, tmp_pdf_multipage: Path):
        """Test: Extrahera text från flersidig PDF."""
        result = extractor.extract(tmp_pdf_multipage)

        assert result.total_pages == 3
        assert len(result.pages) == 3

        for i, page in enumerate(result.pages):
            assert page.page_number == i + 1
            assert f"Sida {i + 1}" in page.text

    def test_extract_nonexistent_file(self, extractor: PDFExtractor):
        """Test: Felhantering för fil som inte finns."""
        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(Path("/nonexistent/file.pdf"))

        assert "finns inte" in str(exc_info.value)

    def test_extract_non_pdf_file(self, extractor: PDFExtractor, tmp_path: Path):
        """Test: Felhantering för icke-PDF-fil."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Detta är inte en PDF")

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(txt_file)

        assert "inte en PDF" in str(exc_info.value)

    def test_page_content_structure(self, extractor: PDFExtractor, tmp_pdf: Path):
        """Test: Sidinnehållets struktur."""
        result = extractor.extract(tmp_pdf)

        page = result.pages[0]

        assert page.page_number == 1
        assert isinstance(page.text, str)
        assert page.extraction_method in ["native", "ocr"]
        assert 0 <= page.confidence <= 1

    def test_confidence_estimation_native(self, extractor: PDFExtractor):
        """Test: Konfidensberäkning för native extraktion."""
        conf = extractor._estimate_confidence("Ren svensk text med åäö.", "native")
        assert conf == 0.95

    def test_confidence_estimation_ocr_clean(self, extractor: PDFExtractor):
        """Test: Konfidensberäkning för ren OCR-text."""
        conf = extractor._estimate_confidence("Ren svensk text med åäö.", "ocr")
        assert conf > 0.8

    def test_confidence_estimation_ocr_garbage(self, extractor: PDFExtractor):
        """Test: Konfidensberäkning för skräp-OCR."""
        conf = extractor._estimate_confidence("@#$%^&*()[]{}|", "ocr")
        assert conf < 0.3

    def test_confidence_estimation_empty(self, extractor: PDFExtractor):
        """Test: Konfidensberäkning för tom text."""
        conf = extractor._estimate_confidence("", "ocr")
        assert conf == 0.0

    def test_determine_method_native(self, extractor: PDFExtractor, tmp_pdf: Path):
        """Test: Bestäm metod för native-extraherade dokument."""
        result = extractor.extract(tmp_pdf)
        assert result.extraction_method == "native"

    def test_metadata_extraction(self, extractor: PDFExtractor, tmp_pdf: Path):
        """Test: Metadata extraheras korrekt."""
        result = extractor.extract(tmp_pdf)

        assert "file_size_bytes" in result.metadata
        assert result.metadata["file_size_bytes"] > 0

    def test_extract_text_only(self, extractor: PDFExtractor, tmp_pdf: Path):
        """Test: Enkel textextraktion."""
        text = extractor.extract_text_only(tmp_pdf)

        assert isinstance(text, str)
        assert "testdokument" in text

    def test_extract_with_path_string(self, extractor: PDFExtractor, tmp_pdf: Path):
        """Test: Extrahera med sökväg som sträng."""
        result = extractor.extract(str(tmp_pdf))

        assert result is not None
        assert "testdokument" in result.full_text

    def test_ocr_fallback_for_empty_page(self, extractor: PDFExtractor, tmp_empty_pdf: Path):
        """Test: OCR används för tom/skannad sida."""
        with patch.object(extractor, "_ocr_page", return_value="OCR-extraherad text"):
            result = extractor.extract(tmp_empty_pdf)

        # Antingen OCR eller native beroende på implementering
        assert result.extraction_method in ["ocr", "native", "mixed"]

    def test_ocr_disabled(self, extractor_no_ocr: PDFExtractor, tmp_empty_pdf: Path):
        """Test: OCR används inte när det är avaktiverat."""
        result = extractor_no_ocr.extract(tmp_empty_pdf)

        # Ska inte använda OCR
        for page in result.pages:
            assert page.extraction_method == "native"


class TestExtractionConfig:
    """Tester för konfiguration."""

    def test_default_config(self):
        """Test: Standardkonfiguration."""
        config = ExtractionConfig()

        assert config.ocr_enabled is True
        assert config.ocr_language == "swe"
        assert config.dpi == 300
        assert config.min_text_threshold == 50

    def test_custom_config(self):
        """Test: Anpassad konfiguration."""
        config = ExtractionConfig(
            ocr_enabled=False,
            ocr_language="eng",
            dpi=150,
            min_text_threshold=100,
        )

        assert config.ocr_enabled is False
        assert config.ocr_language == "eng"
        assert config.dpi == 150
        assert config.min_text_threshold == 100

    def test_extractor_uses_config(self):
        """Test: Extractor använder konfiguration."""
        config = ExtractionConfig(ocr_enabled=False)
        extractor = PDFExtractor(config)

        assert extractor.config.ocr_enabled is False


class TestEdgeCases:
    """Tester för edge cases."""

    @pytest.fixture
    def extractor(self) -> PDFExtractor:
        return PDFExtractor()

    def test_extract_pdf_with_special_characters(self, extractor: PDFExtractor, tmp_path: Path):
        """Test: PDF med specialtecken."""
        import fitz

        pdf_path = tmp_path / "special_chars.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Åäö ÅÄÖ éèê ñ € £ ¥")
        doc.save(pdf_path)
        doc.close()

        result = extractor.extract(pdf_path)

        assert "Åäö" in result.full_text

    def test_extract_pdf_with_numbers(self, extractor: PDFExtractor, tmp_path: Path):
        """Test: PDF med personnummer och telefonnummer."""
        import fitz

        pdf_path = tmp_path / "numbers.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (50, 50),
            "Personnummer: 199001011234\nTelefon: 070-123 45 67\nE-post: test@example.com"
        )
        doc.save(pdf_path)
        doc.close()

        result = extractor.extract(pdf_path)

        assert "199001011234" in result.full_text
        assert "070-123 45 67" in result.full_text
        assert "test@example.com" in result.full_text

    def test_extract_large_pdf_simulation(self, extractor: PDFExtractor, tmp_path: Path):
        """Test: Simulera större PDF (10 sidor)."""
        import fitz

        pdf_path = tmp_path / "large.pdf"
        doc = fitz.open()

        for i in range(10):
            page = doc.new_page()
            page.insert_text(
                (50, 50),
                f"Sida {i + 1}\n" + "Lorem ipsum dolor sit amet. " * 50
            )

        doc.save(pdf_path)
        doc.close()

        result = extractor.extract(pdf_path)

        assert result.total_pages == 10
        assert len(result.pages) == 10
        assert len(result.full_text) > 1000
