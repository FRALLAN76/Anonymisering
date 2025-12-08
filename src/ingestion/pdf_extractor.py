"""PDF-textextraktion med OCR-fallback."""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import io

import fitz  # PyMuPDF
from PIL import Image
import pytesseract

from src.core.models import ExtractedDocument, PageContent
from src.core.exceptions import ExtractionError


@dataclass
class ExtractionConfig:
    """Konfiguration för extraktion."""

    ocr_enabled: bool = True
    ocr_language: str = "swe"
    min_text_threshold: int = 50  # Minsta antal tecken för att undvika OCR
    dpi: int = 300
    timeout_seconds: int = 60


class PDFExtractor:
    """Extraherar text från PDF-dokument."""

    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initiera PDFExtractor.

        Args:
            config: Konfiguration för extraktion
        """
        self.config = config or ExtractionConfig()

    def extract(self, pdf_path: Path | str) -> ExtractedDocument:
        """
        Extrahera all text från en PDF.

        Args:
            pdf_path: Sökväg till PDF-fil

        Returns:
            ExtractedDocument med all extraherad text

        Raises:
            ExtractionError: Vid fel under extraktion
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise ExtractionError(f"Filen finns inte: {pdf_path}")

        if not pdf_path.suffix.lower() == ".pdf":
            raise ExtractionError(f"Filen är inte en PDF: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_content = self._extract_page(page, page_num)
                pages.append(page_content)

            doc.close()

            full_text = "\n\n".join(p.text for p in pages if p.text)

            return ExtractedDocument(
                source_path=str(pdf_path),
                pages=pages,
                total_pages=len(pages),
                full_text=full_text,
                extraction_method=self._determine_method(pages),
                metadata=self._extract_metadata(pdf_path),
            )

        except fitz.FileDataError as e:
            raise ExtractionError(f"Ogiltig PDF-fil: {e}")
        except Exception as e:
            raise ExtractionError(f"Kunde inte extrahera PDF: {e}")

    def _extract_page(self, page: fitz.Page, page_num: int) -> PageContent:
        """
        Extrahera text från en sida.

        Args:
            page: PyMuPDF page-objekt
            page_num: Sidnummer (0-indexerat)

        Returns:
            PageContent med extraherad text
        """
        # Försök med direkt textextraktion först
        text = page.get_text().strip()

        # Om för lite text och OCR är aktiverat, försök med OCR
        if len(text) < self.config.min_text_threshold and self.config.ocr_enabled:
            ocr_text = self._ocr_page(page)
            if len(ocr_text) > len(text):
                text = ocr_text
                method = "ocr"
            else:
                method = "native"
        else:
            method = "native"

        return PageContent(
            page_number=page_num + 1,  # 1-indexerat för användare
            text=text,
            extraction_method=method,
            confidence=self._estimate_confidence(text, method),
        )

    def _ocr_page(self, page: fitz.Page) -> str:
        """
        Kör OCR på en sida.

        Args:
            page: PyMuPDF page-objekt

        Returns:
            OCR-extraherad text
        """
        try:
            # Rendera sida till bild
            pix = page.get_pixmap(dpi=self.config.dpi)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Kör OCR
            text = pytesseract.image_to_string(
                img,
                lang=self.config.ocr_language,
                config="--psm 1",  # Automatic page segmentation
            )

            return text.strip()

        except Exception:
            # Om OCR misslyckas, returnera tom sträng
            return ""

    def _estimate_confidence(self, text: str, method: str) -> float:
        """
        Uppskatta konfidensen i extraktionen.

        Args:
            text: Extraherad text
            method: Extraktionsmetod

        Returns:
            Konfidens mellan 0 och 1
        """
        if method == "native":
            return 0.95

        if not text:
            return 0.0

        # För OCR, räkna andel läsbara tecken
        readable = sum(1 for c in text if c.isalnum() or c.isspace() or c in ".,;:!?-åäöÅÄÖ")
        ratio = readable / len(text) if text else 0

        return min(0.9, ratio)

    def _determine_method(self, pages: list[PageContent]) -> str:
        """
        Bestäm övergripande extraktionsmetod.

        Args:
            pages: Lista med sidinnehåll

        Returns:
            "native", "ocr" eller "mixed"
        """
        if not pages:
            return "native"

        ocr_count = sum(1 for p in pages if p.extraction_method == "ocr")

        if ocr_count == 0:
            return "native"
        elif ocr_count == len(pages):
            return "ocr"
        else:
            return "mixed"

    def _extract_metadata(self, pdf_path: Path) -> dict:
        """
        Extrahera metadata från PDF.

        Args:
            pdf_path: Sökväg till PDF

        Returns:
            Metadata som dict
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata or {}
            doc.close()

            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "file_size_bytes": pdf_path.stat().st_size,
            }
        except Exception:
            return {"file_size_bytes": pdf_path.stat().st_size}

    def extract_text_only(self, pdf_path: Path | str) -> str:
        """
        Enkel metod för att bara extrahera text.

        Args:
            pdf_path: Sökväg till PDF

        Returns:
            All text från dokumentet
        """
        result = self.extract(pdf_path)
        return result.full_text
