# Utvecklingsplan: AI-stött Menprövningsverktyg v2.0
**Datum:** 2025-12-01
**Version:** 2.0
**Status:** Utvecklingsredo

---

## SAMMANFATTNING

En praktisk utvecklingsplan med **testdriven utveckling (TDD)** och **automatisk validering** av varje modul. Planen fokuserar på hur systemet faktiskt byggs, testas och valideras kontinuerligt.

### Kärnprinciper
1. **Varje modul har automatiska tester innan implementation**
2. **Validering mot gold standard för AI-komponenter**
3. **CI/CD från dag 1**
4. **Inkrementell leverans - fungerande system efter varje sprint**

---

## 1. SYSTEMARKITEKTUR

### 1.1 Modulär Struktur

```
menprovning/
├── src/
│   ├── core/                    # Kärnlogik
│   │   ├── __init__.py
│   │   ├── config.py            # Konfiguration
│   │   ├── models.py            # Pydantic-modeller
│   │   └── exceptions.py        # Custom exceptions
│   │
│   ├── ingestion/               # MODUL 1: Dokumentinläsning
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py     # PDF → text
│   │   ├── ocr_handler.py       # OCR för skannade dok
│   │   ├── docx_extractor.py    # Word-dokument
│   │   └── preprocessor.py      # Textnormalisering
│   │
│   ├── ner/                     # MODUL 2: Named Entity Recognition
│   │   ├── __init__.py
│   │   ├── bert_ner.py          # KBLab BERT NER
│   │   ├── entity_linker.py     # Länka entiteter
│   │   └── postprocessor.py     # Efterbearbetning
│   │
│   ├── classification/          # MODUL 3: Känslighetskategorisering
│   │   ├── __init__.py
│   │   ├── bert_classifier.py   # BERT-baserad
│   │   ├── rule_classifier.py   # Regelbaserad backup
│   │   └── ensemble.py          # Kombinera resultat
│   │
│   ├── llm/                     # MODUL 4: GPT-OSS Integration
│   │   ├── __init__.py
│   │   ├── client.py            # API-klient
│   │   ├── prompts/             # Prompt-templates
│   │   │   ├── sensitivity.py
│   │   │   ├── relations.py
│   │   │   ├── reasoning.py
│   │   │   └── insight.py
│   │   ├── response_parser.py   # JSON-parsing
│   │   └── fallback.py          # Fallback vid fel
│   │
│   ├── analysis/                # MODUL 5: Analysmotor
│   │   ├── __init__.py
│   │   ├── sensitivity_engine.py
│   │   ├── relation_graph.py    # NetworkX-grafer
│   │   ├── risk_scorer.py       # Riskpoängsättning
│   │   └── aggregator.py        # Kombinera all analys
│   │
│   ├── legal/                   # MODUL 6: Juridisk logik
│   │   ├── __init__.py
│   │   ├── osl_rules.py         # OSL-regler
│   │   ├── time_assessment.py   # 70-årsgräns etc
│   │   ├── consent_handler.py   # Samtycke
│   │   └── motivation_gen.py    # Generera motiveringar
│   │
│   ├── masking/                 # MODUL 7: Maskning
│   │   ├── __init__.py
│   │   ├── text_masker.py       # Textersättning
│   │   ├── pdf_masker.py        # PDF-maskning
│   │   └── strategies.py        # Maskningsstrategier
│   │
│   ├── workflow/                # MODUL 8: Arbetsflöde
│   │   ├── __init__.py
│   │   ├── case_manager.py      # Ärendehantering
│   │   ├── state_machine.py     # Status-hantering
│   │   └── audit_logger.py      # Revision
│   │
│   └── api/                     # MODUL 9: REST API
│       ├── __init__.py
│       ├── main.py              # FastAPI app
│       ├── routes/
│       │   ├── cases.py
│       │   ├── documents.py
│       │   ├── analysis.py
│       │   └── decisions.py
│       └── middleware/
│           ├── auth.py
│           └── logging.py
│
├── tests/                       # AUTOMATISKA TESTER
│   ├── conftest.py              # Pytest fixtures
│   ├── fixtures/                # Testdata
│   │   ├── documents/           # Test-PDF:er
│   │   ├── gold_standard/       # Annoterad data
│   │   └── synthetic/           # Genererad testdata
│   │
│   ├── unit/                    # Enhetstester
│   │   ├── test_ingestion.py
│   │   ├── test_ner.py
│   │   ├── test_classification.py
│   │   ├── test_llm.py
│   │   ├── test_analysis.py
│   │   ├── test_legal.py
│   │   ├── test_masking.py
│   │   └── test_workflow.py
│   │
│   ├── integration/             # Integrationstester
│   │   ├── test_pipeline.py
│   │   ├── test_api.py
│   │   └── test_end_to_end.py
│   │
│   ├── validation/              # AI-validering
│   │   ├── test_ner_accuracy.py
│   │   ├── test_classification_accuracy.py
│   │   ├── test_llm_quality.py
│   │   └── test_overall_precision.py
│   │
│   └── benchmarks/              # Prestandatester
│       ├── bench_ingestion.py
│       ├── bench_ner.py
│       └── bench_llm.py
│
├── validation/                  # Valideringsramverk
│   ├── gold_standard/           # Manuellt annoterad data
│   │   ├── README.md
│   │   ├── documents/
│   │   ├── annotations/
│   │   └── schema.json
│   │
│   ├── metrics/                 # Mätningsverktyg
│   │   ├── ner_metrics.py
│   │   ├── classification_metrics.py
│   │   ├── llm_metrics.py
│   │   └── report_generator.py
│   │
│   └── scripts/
│       ├── annotate.py          # Hjälpverktyg för annotation
│       ├── evaluate.py          # Kör validering
│       └── compare_models.py    # Jämför versioner
│
├── frontend/                    # React-frontend
│   ├── src/
│   ├── tests/
│   └── package.json
│
├── infrastructure/              # DevOps
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.worker
│   │   └── docker-compose.yml
│   ├── k8s/
│   └── terraform/
│
├── scripts/                     # Hjälpskript
│   ├── setup_dev.sh
│   ├── run_tests.sh
│   ├── validate_models.sh
│   └── generate_synthetic_data.py
│
├── pyproject.toml
├── pytest.ini
├── .pre-commit-config.yaml
└── Makefile
```

---

## 2. GOLD STANDARD & VALIDERINGSRAMVERK

### 2.1 Skapa Gold Standard Dataset

**Mål:** 100 annoterade dokument för validering

```python
# validation/gold_standard/schema.json
{
  "document_id": "doc_001",
  "source_file": "testakt_001.pdf",
  "annotated_by": "jurist_expert",
  "annotated_date": "2025-01-15",

  "entities": [
    {
      "id": "ent_001",
      "text": "Agnes Grenqvist",
      "type": "PERSON",
      "start": 145,
      "end": 160,
      "role": "mormor",
      "is_requester": false
    },
    {
      "id": "ent_002",
      "text": "070-123 45 67",
      "type": "PHONE",
      "start": 234,
      "end": 247,
      "belongs_to": "ent_001"
    }
  ],

  "sections": [
    {
      "id": "sec_001",
      "text": "Agnes har haft missbruksproblem sedan 2015...",
      "start": 500,
      "end": 650,
      "sensitivity": {
        "level": "HIGH",
        "category": "ADDICTION",
        "secondary_categories": ["HEALTH", "STIGMA"],
        "legal_basis": "OSL 26:1",
        "reasoning": "Känslig hälsoinformation om tredje part"
      },
      "affected_persons": ["ent_001"],
      "recommended_action": "MASK_COMPLETE"
    }
  ],

  "relations": [
    {
      "person1": "ent_001",
      "person2": "ent_003",
      "relation_type": "grandmother_of",
      "conflict": true,
      "conflict_description": "Vårdnadstvist pågår"
    }
  ],

  "overall_decision": {
    "sections_to_mask": ["sec_001", "sec_003", "sec_007"],
    "sections_partial_mask": ["sec_004"],
    "sections_to_release": ["sec_002", "sec_005", "sec_006"],
    "legal_motivation": "Med hänsyn till..."
  }
}
```

### 2.2 Annotation-verktyg

```python
# validation/scripts/annotate.py
"""
Verktyg för att skapa gold standard annotationer.
Kör: python -m validation.scripts.annotate path/to/document.pdf
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

class AnnotationSession:
    """Interaktivt annotationsverktyg."""

    def __init__(self, document_path: Path):
        self.document_path = document_path
        self.document_id = document_path.stem
        self.annotations = {
            "document_id": self.document_id,
            "source_file": document_path.name,
            "entities": [],
            "sections": [],
            "relations": []
        }

    def run(self):
        """Kör interaktiv annotation."""
        console.print(f"\n[bold]Annoterar: {self.document_path}[/bold]\n")

        # Extrahera text
        text = self._extract_text()

        # Steg 1: Annotera entiteter
        self._annotate_entities(text)

        # Steg 2: Annotera känsliga sektioner
        self._annotate_sections(text)

        # Steg 3: Annotera relationer
        self._annotate_relations()

        # Steg 4: Övergripande beslut
        self._annotate_decision()

        # Spara
        self._save()

        console.print("\n[green]✓ Annotation sparad![/green]")

    def _annotate_entities(self, text: str):
        """Annotera entiteter interaktivt."""
        console.print("\n[bold cyan]STEG 1: ENTITETER[/bold cyan]")
        console.print("Markera personer, telefonnummer, adresser etc.\n")

        entity_types = ["PERSON", "PHONE", "EMAIL", "ADDRESS", "SSN", "ORG", "LOCATION"]

        while True:
            entity_text = Prompt.ask("Entitetstext (tom för att avsluta)")
            if not entity_text:
                break

            entity_type = Prompt.ask(
                "Typ",
                choices=entity_types,
                default="PERSON"
            )

            # Hitta position i text
            start = text.find(entity_text)
            if start == -1:
                console.print("[red]Hittades inte i texten![/red]")
                continue

            entity = {
                "id": f"ent_{len(self.annotations['entities']) + 1:03d}",
                "text": entity_text,
                "type": entity_type,
                "start": start,
                "end": start + len(entity_text)
            }

            if entity_type == "PERSON":
                entity["role"] = Prompt.ask("Roll (t.ex. 'mormor', 'barn', 'anmälare')")

            self.annotations["entities"].append(entity)
            console.print(f"[green]✓ Lade till: {entity}[/green]")

    def _annotate_sections(self, text: str):
        """Annotera känsliga sektioner."""
        console.print("\n[bold cyan]STEG 2: KÄNSLIGA SEKTIONER[/bold cyan]")

        sensitivity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        categories = [
            "HEALTH", "MENTAL_HEALTH", "ADDICTION", "VIOLENCE",
            "FAMILY", "ECONOMY", "HOUSING", "SEXUAL", "CRIMINAL", "NEUTRAL"
        ]
        actions = ["RELEASE", "MASK_PARTIAL", "MASK_COMPLETE"]

        while True:
            section_text = Prompt.ask("\nKänslig text (tom för att avsluta)")
            if not section_text:
                break

            start = text.find(section_text)

            level = Prompt.ask("Känslighetsnivå", choices=sensitivity_levels)
            category = Prompt.ask("Kategori", choices=categories)
            reasoning = Prompt.ask("Motivering")
            action = Prompt.ask("Rekommendation", choices=actions)

            section = {
                "id": f"sec_{len(self.annotations['sections']) + 1:03d}",
                "text": section_text,
                "start": start,
                "end": start + len(section_text) if start != -1 else -1,
                "sensitivity": {
                    "level": level,
                    "category": category,
                    "legal_basis": "OSL 26:1",
                    "reasoning": reasoning
                },
                "recommended_action": action
            }

            self.annotations["sections"].append(section)
            console.print(f"[green]✓ Lade till sektion[/green]")

    def _save(self):
        """Spara annotationer till fil."""
        output_path = Path("validation/gold_standard/annotations") / f"{self.document_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.annotations, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python annotate.py <document.pdf>")
        sys.exit(1)

    session = AnnotationSession(Path(sys.argv[1]))
    session.run()
```

---

## 3. MODUL-FÖR-MODUL UTVECKLING MED VALIDERING

### 3.1 MODUL 1: Dokumentinläsning

**Fil:** `src/ingestion/pdf_extractor.py`

```python
"""
PDF-textextraktion med OCR-fallback.
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

from src.core.models import ExtractedDocument, PageContent
from src.core.exceptions import ExtractionError


@dataclass
class ExtractionConfig:
    """Konfiguration för extraktion."""
    ocr_enabled: bool = True
    ocr_language: str = "swe"
    min_text_confidence: float = 0.8
    dpi: int = 300


class PDFExtractor:
    """Extraherar text från PDF-dokument."""

    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()

    def extract(self, pdf_path: Path) -> ExtractedDocument:
        """
        Extrahera all text från en PDF.

        Args:
            pdf_path: Sökväg till PDF-fil

        Returns:
            ExtractedDocument med all extraherad text

        Raises:
            ExtractionError: Vid fel under extraktion
        """
        if not pdf_path.exists():
            raise ExtractionError(f"Filen finns inte: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            pages = []

            for page_num, page in enumerate(doc):
                page_content = self._extract_page(page, page_num)
                pages.append(page_content)

            doc.close()

            return ExtractedDocument(
                source_path=str(pdf_path),
                pages=pages,
                total_pages=len(pages),
                full_text="\n\n".join(p.text for p in pages),
                extraction_method=self._determine_method(pages)
            )

        except Exception as e:
            raise ExtractionError(f"Kunde inte extrahera PDF: {e}")

    def _extract_page(self, page: fitz.Page, page_num: int) -> PageContent:
        """Extrahera text från en sida."""

        # Försök med direkt textextraktion först
        text = page.get_text()

        # Om lite text, försök med OCR
        if len(text.strip()) < 50 and self.config.ocr_enabled:
            text = self._ocr_page(page)
            method = "ocr"
        else:
            method = "native"

        return PageContent(
            page_number=page_num + 1,
            text=text.strip(),
            extraction_method=method,
            confidence=self._estimate_confidence(text, method)
        )

    def _ocr_page(self, page: fitz.Page) -> str:
        """OCR på en sida."""
        # Rendera sida till bild
        pix = page.get_pixmap(dpi=self.config.dpi)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        # Kör OCR
        text = pytesseract.image_to_string(
            img,
            lang=self.config.ocr_language,
            config='--psm 1'  # Automatic page segmentation
        )

        return text

    def _estimate_confidence(self, text: str, method: str) -> float:
        """Uppskatta konfidensen i extraktionen."""
        if method == "native":
            return 0.95

        # För OCR, kolla textens "renhet"
        if not text:
            return 0.0

        # Räkna andel läsbara tecken
        readable = sum(1 for c in text if c.isalnum() or c.isspace())
        ratio = readable / len(text)

        return min(0.9, ratio)

    def _determine_method(self, pages: list[PageContent]) -> str:
        """Bestäm övergripande extraktionsmetod."""
        ocr_count = sum(1 for p in pages if p.extraction_method == "ocr")

        if ocr_count == 0:
            return "native"
        elif ocr_count == len(pages):
            return "ocr"
        else:
            return "mixed"
```

**Test:** `tests/unit/test_ingestion.py`

```python
"""
Enhetstester för dokumentinläsning.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import fitz

from src.ingestion.pdf_extractor import PDFExtractor, ExtractionConfig
from src.core.exceptions import ExtractionError


class TestPDFExtractor:
    """Tester för PDFExtractor."""

    @pytest.fixture
    def extractor(self):
        """Skapa en extractor-instans."""
        return PDFExtractor()

    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Skapa en test-PDF."""
        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Detta är ett testdokument.\nRad två.")
        doc.save(pdf_path)
        doc.close()
        return pdf_path

    def test_extract_simple_pdf(self, extractor, sample_pdf):
        """Test: Extrahera text från enkel PDF."""
        result = extractor.extract(sample_pdf)

        assert result is not None
        assert "testdokument" in result.full_text
        assert result.total_pages == 1
        assert result.extraction_method == "native"

    def test_extract_nonexistent_file(self, extractor):
        """Test: Felhantering för fil som inte finns."""
        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(Path("/nonexistent/file.pdf"))

        assert "finns inte" in str(exc_info.value)

    def test_extract_with_ocr_fallback(self, extractor, tmp_path):
        """Test: OCR används för skannade dokument."""
        # Skapa en PDF med bara en bild (simulera skanning)
        pdf_path = tmp_path / "scanned.pdf"
        doc = fitz.open()
        page = doc.new_page()
        # Ingen text, bara tom sida
        doc.save(pdf_path)
        doc.close()

        with patch.object(extractor, '_ocr_page', return_value="OCR-text"):
            result = extractor.extract(pdf_path)

        assert "OCR-text" in result.full_text or result.extraction_method in ["ocr", "mixed"]

    def test_confidence_estimation(self, extractor):
        """Test: Konfidensberäkning."""
        # Ren text = hög konfidens
        conf_clean = extractor._estimate_confidence("Ren svensk text", "ocr")
        assert conf_clean > 0.8

        # Skräptext = låg konfidens
        conf_garbage = extractor._estimate_confidence("@#$%^&*()", "ocr")
        assert conf_garbage < 0.5

    def test_page_content_structure(self, extractor, sample_pdf):
        """Test: Sidinnehållets struktur."""
        result = extractor.extract(sample_pdf)

        assert len(result.pages) == 1
        page = result.pages[0]

        assert page.page_number == 1
        assert isinstance(page.text, str)
        assert page.extraction_method in ["native", "ocr"]
        assert 0 <= page.confidence <= 1


class TestExtractionConfig:
    """Tester för konfiguration."""

    def test_default_config(self):
        """Test: Standardkonfiguration."""
        config = ExtractionConfig()

        assert config.ocr_enabled is True
        assert config.ocr_language == "swe"
        assert config.dpi == 300

    def test_custom_config(self):
        """Test: Anpassad konfiguration."""
        config = ExtractionConfig(
            ocr_enabled=False,
            ocr_language="eng",
            dpi=150
        )

        assert config.ocr_enabled is False
        assert config.ocr_language == "eng"
```

**Valideringstest:** `tests/validation/test_ingestion_accuracy.py`

```python
"""
Validera extraktionskvalitet mot gold standard.
"""

import pytest
from pathlib import Path
import json
from difflib import SequenceMatcher

from src.ingestion.pdf_extractor import PDFExtractor
from validation.metrics.extraction_metrics import ExtractionMetrics


class TestIngestionAccuracy:
    """Validera extraktionskvalitet."""

    @pytest.fixture
    def gold_standard_docs(self):
        """Ladda gold standard dokument."""
        gold_dir = Path("validation/gold_standard")
        docs = []

        for annotation_file in (gold_dir / "annotations").glob("*.json"):
            with open(annotation_file) as f:
                annotation = json.load(f)

            pdf_path = gold_dir / "documents" / annotation["source_file"]
            if pdf_path.exists():
                docs.append({
                    "annotation": annotation,
                    "pdf_path": pdf_path
                })

        return docs

    @pytest.fixture
    def extractor(self):
        return PDFExtractor()

    def test_extraction_completeness(self, extractor, gold_standard_docs):
        """
        Test: All annoterad text finns i extraktionen.
        Krav: >= 98% av annoterade entiteter ska finnas i extraherad text.
        """
        if not gold_standard_docs:
            pytest.skip("Inga gold standard dokument tillgängliga")

        total_entities = 0
        found_entities = 0

        for doc in gold_standard_docs:
            result = extractor.extract(doc["pdf_path"])
            extracted_text = result.full_text.lower()

            for entity in doc["annotation"]["entities"]:
                total_entities += 1
                if entity["text"].lower() in extracted_text:
                    found_entities += 1

        recall = found_entities / total_entities if total_entities > 0 else 0

        assert recall >= 0.98, f"Extraktion recall för låg: {recall:.2%}"

    def test_text_fidelity(self, extractor, gold_standard_docs):
        """
        Test: Extraherad text matchar originalet.
        Krav: >= 95% likhet med manuellt verifierad text.
        """
        if not gold_standard_docs:
            pytest.skip("Inga gold standard dokument tillgängliga")

        similarities = []

        for doc in gold_standard_docs:
            result = extractor.extract(doc["pdf_path"])

            # Jämför med annoterade sektioners text
            for section in doc["annotation"]["sections"]:
                expected = section["text"].lower()

                # Hitta bästa matchning i extraherad text
                similarity = self._find_best_match(expected, result.full_text.lower())
                similarities.append(similarity)

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0

        assert avg_similarity >= 0.95, f"Textlikhet för låg: {avg_similarity:.2%}"

    def _find_best_match(self, needle: str, haystack: str) -> float:
        """Hitta bästa matchning för en sträng."""
        if needle in haystack:
            return 1.0

        # Sliding window för att hitta bästa matchning
        needle_len = len(needle)
        best_ratio = 0

        for i in range(len(haystack) - needle_len + 1):
            window = haystack[i:i + needle_len]
            ratio = SequenceMatcher(None, needle, window).ratio()
            best_ratio = max(best_ratio, ratio)

            if best_ratio > 0.95:  # Tillräckligt bra
                break

        return best_ratio

    def test_ocr_quality(self, extractor, gold_standard_docs):
        """
        Test: OCR-kvalitet för skannade dokument.
        Krav: OCR-extraherad text ska ha >= 90% läsbarhet.
        """
        # Filtrera till OCR-dokument
        ocr_docs = [d for d in gold_standard_docs
                    if d["annotation"].get("is_scanned", False)]

        if not ocr_docs:
            pytest.skip("Inga skannade dokument i gold standard")

        for doc in ocr_docs:
            result = extractor.extract(doc["pdf_path"])

            # Verifiera att text är läsbar
            readable_ratio = self._calculate_readability(result.full_text)

            assert readable_ratio >= 0.90, \
                f"OCR-kvalitet för låg för {doc['pdf_path'].name}: {readable_ratio:.2%}"

    def _calculate_readability(self, text: str) -> float:
        """Beräkna andel läsbara tecken."""
        if not text:
            return 0.0

        readable = sum(1 for c in text if c.isalnum() or c.isspace() or c in ".,;:!?-")
        return readable / len(text)
```

---

### 3.2 MODUL 2: Named Entity Recognition (NER)

**Fil:** `src/ner/bert_ner.py`

```python
"""
KBLab Swedish BERT NER integration.
"""

from typing import List, Optional
from dataclasses import dataclass
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
import re

from src.core.models import Entity, EntityType


@dataclass
class NERConfig:
    """Konfiguration för NER."""
    model_name: str = "KB/bert-base-swedish-cased-ner"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size: int = 8
    max_length: int = 512
    confidence_threshold: float = 0.7


class BertNER:
    """KBLab BERT NER för svenska."""

    def __init__(self, config: Optional[NERConfig] = None):
        self.config = config or NERConfig()
        self._model = None
        self._tokenizer = None

    @property
    def model(self):
        """Lazy-loading av modell."""
        if self._model is None:
            self._load_model()
        return self._model

    @property
    def tokenizer(self):
        """Lazy-loading av tokenizer."""
        if self._tokenizer is None:
            self._load_model()
        return self._tokenizer

    def _load_model(self):
        """Ladda BERT-modell."""
        self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        self._model = AutoModelForTokenClassification.from_pretrained(
            self.config.model_name
        ).to(self.config.device)
        self._model.eval()

    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extrahera entiteter från text.

        Args:
            text: Texten att analysera

        Returns:
            Lista med identifierade entiteter
        """
        # Dela upp lång text i chunks
        chunks = self._split_text(text)
        all_entities = []

        for chunk_start, chunk_text in chunks:
            entities = self._process_chunk(chunk_text, chunk_start)
            all_entities.extend(entities)

        # Lägg till regelbaserade entiteter (personnummer, telefon etc)
        regex_entities = self._extract_regex_entities(text)
        all_entities.extend(regex_entities)

        # Deduplisera och sortera
        all_entities = self._deduplicate(all_entities)
        all_entities.sort(key=lambda e: e.start)

        return all_entities

    def _process_chunk(self, text: str, offset: int) -> List[Entity]:
        """Bearbeta en textchunk med BERT."""

        # Tokenisera
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_length,
            return_offsets_mapping=True
        )

        offset_mapping = inputs.pop("offset_mapping")[0]
        inputs = {k: v.to(self.config.device) for k, v in inputs.items()}

        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        predictions = torch.argmax(outputs.logits, dim=2)[0]
        confidences = torch.softmax(outputs.logits, dim=2)[0]

        # Konvertera till entiteter
        entities = []
        current_entity = None

        for idx, (pred, conf, (start, end)) in enumerate(
            zip(predictions, confidences, offset_mapping)
        ):
            if start == end:  # Specialtoken
                continue

            label = self.model.config.id2label[pred.item()]
            confidence = conf[pred].item()

            if label.startswith("B-"):  # Början av entitet
                if current_entity:
                    entities.append(current_entity)

                entity_type = self._map_label(label[2:])
                current_entity = Entity(
                    text=text[start:end],
                    type=entity_type,
                    start=offset + start,
                    end=offset + end,
                    confidence=confidence
                )

            elif label.startswith("I-") and current_entity:  # Fortsättning
                current_entity.text = text[current_entity.start - offset:end]
                current_entity.end = offset + end
                current_entity.confidence = min(current_entity.confidence, confidence)

            else:  # O-label eller mismatch
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None

        if current_entity:
            entities.append(current_entity)

        # Filtrera på konfidens
        entities = [e for e in entities if e.confidence >= self.config.confidence_threshold]

        return entities

    def _extract_regex_entities(self, text: str) -> List[Entity]:
        """Extrahera entiteter med regex (personnummer, telefon etc)."""
        entities = []

        # Svenska personnummer: YYMMDD-XXXX eller YYYYMMDD-XXXX
        pnr_pattern = r'\b(\d{6,8}[-\s]?\d{4})\b'
        for match in re.finditer(pnr_pattern, text):
            entities.append(Entity(
                text=match.group(1),
                type=EntityType.SSN,
                start=match.start(),
                end=match.end(),
                confidence=0.99
            ))

        # Telefonnummer
        phone_pattern = r'\b((?:\+46|0)[-\s]?\d{2,3}[-\s]?\d{2,3}[-\s]?\d{2,4})\b'
        for match in re.finditer(phone_pattern, text):
            entities.append(Entity(
                text=match.group(1),
                type=EntityType.PHONE,
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))

        # E-post
        email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        for match in re.finditer(email_pattern, text):
            entities.append(Entity(
                text=match.group(1),
                type=EntityType.EMAIL,
                start=match.start(),
                end=match.end(),
                confidence=0.99
            ))

        return entities

    def _split_text(self, text: str) -> List[tuple[int, str]]:
        """Dela upp text i hanterbara chunks."""
        max_chars = self.config.max_length * 4  # Ungefärlig mapping

        if len(text) <= max_chars:
            return [(0, text)]

        chunks = []
        sentences = text.split('.')

        current_chunk = ""
        current_start = 0

        for sentence in sentences:
            sentence = sentence + "."

            if len(current_chunk) + len(sentence) > max_chars:
                if current_chunk:
                    chunks.append((current_start, current_chunk))
                current_start = current_start + len(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence

        if current_chunk:
            chunks.append((current_start, current_chunk))

        return chunks

    def _map_label(self, label: str) -> EntityType:
        """Mappa BERT-label till EntityType."""
        mapping = {
            "PER": EntityType.PERSON,
            "LOC": EntityType.LOCATION,
            "ORG": EntityType.ORGANIZATION,
            "MISC": EntityType.MISC
        }
        return mapping.get(label, EntityType.MISC)

    def _deduplicate(self, entities: List[Entity]) -> List[Entity]:
        """Ta bort duplicerade entiteter."""
        seen = set()
        unique = []

        for entity in entities:
            key = (entity.text, entity.start, entity.end)
            if key not in seen:
                seen.add(key)
                unique.append(entity)

        return unique
```

**Valideringstest:** `tests/validation/test_ner_accuracy.py`

```python
"""
Validera NER-precision mot gold standard.

Mål:
- Precision >= 90%
- Recall >= 85%
- F1 >= 87%
"""

import pytest
from pathlib import Path
import json
from collections import defaultdict

from src.ner.bert_ner import BertNER
from validation.metrics.ner_metrics import NERMetrics


class TestNERAccuracy:
    """Validera NER mot gold standard."""

    @pytest.fixture
    def ner_model(self):
        return BertNER()

    @pytest.fixture
    def gold_standard(self):
        """Ladda gold standard annotationer."""
        gold_dir = Path("validation/gold_standard/annotations")
        annotations = []

        for f in gold_dir.glob("*.json"):
            with open(f) as fp:
                annotations.append(json.load(fp))

        return annotations

    def test_overall_precision(self, ner_model, gold_standard):
        """
        Test: Övergripande precision.
        Krav: >= 90% av förutsagda entiteter är korrekta.
        """
        if not gold_standard:
            pytest.skip("Ingen gold standard data")

        metrics = NERMetrics()

        for doc in gold_standard:
            # Extrahera full text från annotationen
            full_text = doc.get("full_text", "")
            if not full_text:
                continue

            # Kör NER
            predicted = ner_model.extract_entities(full_text)
            gold_entities = doc["entities"]

            # Beräkna precision
            metrics.add_document(predicted, gold_entities)

        precision = metrics.precision()

        assert precision >= 0.90, f"NER precision för låg: {precision:.2%}"

    def test_overall_recall(self, ner_model, gold_standard):
        """
        Test: Övergripande recall.
        Krav: >= 85% av verkliga entiteter hittas.
        """
        if not gold_standard:
            pytest.skip("Ingen gold standard data")

        metrics = NERMetrics()

        for doc in gold_standard:
            full_text = doc.get("full_text", "")
            if not full_text:
                continue

            predicted = ner_model.extract_entities(full_text)
            gold_entities = doc["entities"]

            metrics.add_document(predicted, gold_entities)

        recall = metrics.recall()

        assert recall >= 0.85, f"NER recall för låg: {recall:.2%}"

    def test_f1_score(self, ner_model, gold_standard):
        """
        Test: F1-score.
        Krav: >= 87%
        """
        if not gold_standard:
            pytest.skip("Ingen gold standard data")

        metrics = NERMetrics()

        for doc in gold_standard:
            full_text = doc.get("full_text", "")
            if not full_text:
                continue

            predicted = ner_model.extract_entities(full_text)
            metrics.add_document(predicted, doc["entities"])

        f1 = metrics.f1_score()

        assert f1 >= 0.87, f"NER F1 för låg: {f1:.2%}"

    def test_person_detection(self, ner_model, gold_standard):
        """
        Test: Personnamn hittas korrekt.
        Krav: >= 95% recall för PERSON-entiteter.
        """
        if not gold_standard:
            pytest.skip("Ingen gold standard data")

        person_found = 0
        person_total = 0

        for doc in gold_standard:
            full_text = doc.get("full_text", "")
            if not full_text:
                continue

            predicted = ner_model.extract_entities(full_text)
            predicted_persons = {e.text.lower() for e in predicted
                                if e.type.value == "PERSON"}

            for entity in doc["entities"]:
                if entity["type"] == "PERSON":
                    person_total += 1
                    if entity["text"].lower() in predicted_persons:
                        person_found += 1

        recall = person_found / person_total if person_total > 0 else 0

        assert recall >= 0.95, f"PERSON recall för låg: {recall:.2%}"

    def test_ssn_detection(self, ner_model, gold_standard):
        """
        Test: Personnummer hittas korrekt.
        Krav: 100% recall för SSN.
        """
        if not gold_standard:
            pytest.skip("Ingen gold standard data")

        ssn_found = 0
        ssn_total = 0

        for doc in gold_standard:
            full_text = doc.get("full_text", "")
            if not full_text:
                continue

            predicted = ner_model.extract_entities(full_text)
            predicted_ssn = {e.text.replace("-", "").replace(" ", "")
                           for e in predicted if e.type.value == "SSN"}

            for entity in doc["entities"]:
                if entity["type"] == "SSN":
                    ssn_total += 1
                    normalized = entity["text"].replace("-", "").replace(" ", "")
                    if normalized in predicted_ssn:
                        ssn_found += 1

        recall = ssn_found / ssn_total if ssn_total > 0 else 1.0

        assert recall >= 0.99, f"SSN recall för låg: {recall:.2%}"

    def test_per_type_metrics(self, ner_model, gold_standard):
        """
        Test: Detaljerade metrics per entitetstyp.
        """
        if not gold_standard:
            pytest.skip("Ingen gold standard data")

        type_metrics = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

        for doc in gold_standard:
            full_text = doc.get("full_text", "")
            if not full_text:
                continue

            predicted = ner_model.extract_entities(full_text)

            # Gruppera per typ
            pred_by_type = defaultdict(set)
            for e in predicted:
                pred_by_type[e.type.value].add(e.text.lower())

            gold_by_type = defaultdict(set)
            for e in doc["entities"]:
                gold_by_type[e["type"]].add(e["text"].lower())

            # Beräkna per typ
            all_types = set(pred_by_type.keys()) | set(gold_by_type.keys())

            for entity_type in all_types:
                pred_set = pred_by_type[entity_type]
                gold_set = gold_by_type[entity_type]

                type_metrics[entity_type]["tp"] += len(pred_set & gold_set)
                type_metrics[entity_type]["fp"] += len(pred_set - gold_set)
                type_metrics[entity_type]["fn"] += len(gold_set - pred_set)

        # Skriv ut rapport
        print("\n=== NER Metrics per Entity Type ===")
        for entity_type, counts in sorted(type_metrics.items()):
            tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            print(f"{entity_type:12} P={precision:.2%} R={recall:.2%} F1={f1:.2%}")
```

---

### 3.3 MODUL 4: GPT-OSS Integration

**Fil:** `src/llm/client.py`

```python
"""
GPT-OSS 120B klient.
"""

import asyncio
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.exceptions import LLMError


@dataclass
class LLMConfig:
    """Konfiguration för LLM."""
    endpoint: str = "http://localhost:8000/v1/chat/completions"
    model: str = "gpt-oss-120b"
    timeout: float = 60.0
    max_retries: int = 3
    default_temperature: float = 0.1
    default_max_tokens: int = 2000


class GPTOSSClient:
    """Klient för GPT-OSS 120B."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-loading av HTTP-klient."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client

    async def close(self):
        """Stäng klienten."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None
    ) -> str:
        """
        Skicka completion-request.

        Args:
            prompt: User-prompt
            system_prompt: System-instruktion
            temperature: Sampling temperature
            max_tokens: Max tokens i svar
            response_format: "json" för JSON-svar

        Returns:
            LLM-svar som sträng
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.default_temperature,
            "max_tokens": max_tokens or self.config.default_max_tokens
        }

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await self.client.post(
                self.config.endpoint,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException:
            raise LLMError("LLM timeout - försök igen")
        except httpx.HTTPStatusError as e:
            raise LLMError(f"LLM HTTP-fel: {e.response.status_code}")
        except Exception as e:
            raise LLMError(f"LLM-fel: {e}")

    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Skicka request och parsa JSON-svar.

        Returns:
            Parsat JSON som dict
        """
        response = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format="json"
        )

        return self._parse_json(response)

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """Parsa JSON från LLM-svar."""
        # Försök hitta JSON i svaret
        response = response.strip()

        # Om hela svaret är JSON
        if response.startswith("{"):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass

        # Försök hitta JSON-block
        start = response.find("{")
        end = response.rfind("}") + 1

        if start != -1 and end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass

        raise LLMError(f"Kunde inte parsa JSON från svar: {response[:200]}")

    async def health_check(self) -> bool:
        """Kontrollera att LLM-tjänsten är tillgänglig."""
        try:
            response = await self.complete(
                "Svara endast 'OK'",
                max_tokens=10
            )
            return "OK" in response.upper()
        except:
            return False
```

**Fil:** `src/llm/prompts/sensitivity.py`

```python
"""
Prompts för känslighetsbedömning.
"""

SYSTEM_PROMPT = """Du är expert på menprövning enligt Offentlighets- och
Sekretesslagen (OSL) kapitel 26. Din uppgift är att analysera textavsnitt
från sociala akter och bedöma deras känslighet.

VIKTIGA PRINCIPER:
1. Vid minsta tvivel, rekommendera maskning (omvänt skaderekvisit)
2. Barn under 18 år har förstärkt skydd
3. Våldsutsatta personer har särskilt skyddsbehov
4. Hälsouppgifter är generellt sekretessbelagda
5. Bedöm alltid relationella risker
6. Dokumentera alltid ditt resonemang
7. Var transparent om osäkerhet

Du svarar ALLTID i JSON-format enligt den specifikation som ges."""


def build_sensitivity_prompt(
    text: str,
    context: dict,
    entities: list
) -> str:
    """Bygg prompt för känslighetsbedömning."""

    entities_str = "\n".join([
        f"- {e['text']} ({e['type']})" for e in entities
    ])

    return f"""DOKUMENT-SAMMANHANG:
Dokumenttyp: {context.get('document_type', 'Socialakt')}
Beställare: {context.get('requester', 'Okänd')}
Relation till ärende: {context.get('relation', 'Okänd')}

IDENTIFIERADE ENTITETER:
{entities_str}

TEXTAVSNITT ATT BEDÖMA:
"{text}"

Analysera detta avsnitt och svara i följande JSON-format:
{{
  "sensitivity_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "primary_category": "HEALTH|MENTAL_HEALTH|ADDICTION|VIOLENCE|FAMILY|ECONOMY|HOUSING|SEXUAL|CRIMINAL|NEUTRAL",
  "secondary_categories": ["lista med sekundära kategorier"],
  "reasons": ["lista med konkreta skäl för bedömningen"],
  "affected_persons": ["lista över berörda personer"],
  "indirect_risks": ["indirekta risker om uppgiften röjs"],
  "context_notes": "förklaring av varför kontexten är viktig",
  "recommendation": "RELEASE|MASK_PARTIAL|MASK_COMPLETE",
  "confidence": 0.0-1.0,
  "legal_basis": "hänvisning till relevant lagrum"
}}"""
```

**Valideringstest:** `tests/validation/test_llm_quality.py`

```python
"""
Validera LLM-kvalitet för menprövning.

Tester:
1. Känslighetsbedömning matchar gold standard
2. JSON-format är korrekt
3. Konsekvens över flera anrop
4. Hantering av edge cases
"""

import pytest
import asyncio
import json
from pathlib import Path
from collections import Counter

from src.llm.client import GPTOSSClient, LLMConfig
from src.llm.prompts.sensitivity import SYSTEM_PROMPT, build_sensitivity_prompt


class TestLLMQuality:
    """Validera LLM-kvalitet."""

    @pytest.fixture
    def llm_client(self):
        return GPTOSSClient()

    @pytest.fixture
    def gold_standard(self):
        """Ladda gold standard för känslighetsbedömning."""
        gold_path = Path("validation/gold_standard/sensitivity_cases.json")
        if gold_path.exists():
            with open(gold_path) as f:
                return json.load(f)
        return []

    @pytest.mark.asyncio
    async def test_llm_available(self, llm_client):
        """Test: LLM-tjänsten är tillgänglig."""
        is_healthy = await llm_client.health_check()
        assert is_healthy, "GPT-OSS är inte tillgänglig"

    @pytest.mark.asyncio
    async def test_json_format_valid(self, llm_client):
        """Test: LLM returnerar giltig JSON."""
        test_text = "Patienten har diagnosticerats med depression."

        prompt = build_sensitivity_prompt(
            text=test_text,
            context={"document_type": "Socialakt"},
            entities=[{"text": "Patienten", "type": "PERSON"}]
        )

        response = await llm_client.complete_json(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT
        )

        # Verifiera att alla förväntade fält finns
        required_fields = [
            "sensitivity_level", "primary_category", "reasons",
            "recommendation", "confidence"
        ]

        for field in required_fields:
            assert field in response, f"Saknar fält: {field}"

        # Verifiera värdetyper
        assert response["sensitivity_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert isinstance(response["reasons"], list)
        assert 0 <= response["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_sensitivity_accuracy(self, llm_client, gold_standard):
        """
        Test: Känslighetsbedömning matchar experter.
        Krav: >= 85% överensstämmelse med gold standard.
        """
        if not gold_standard:
            pytest.skip("Ingen gold standard data")

        correct = 0
        total = 0

        for case in gold_standard[:20]:  # Begränsa för hastighet
            prompt = build_sensitivity_prompt(
                text=case["text"],
                context=case.get("context", {}),
                entities=case.get("entities", [])
            )

            response = await llm_client.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )

            total += 1

            # Jämför nivå (tillåt en nivås avvikelse)
            levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            pred_idx = levels.index(response["sensitivity_level"])
            gold_idx = levels.index(case["expected_level"])

            if abs(pred_idx - gold_idx) <= 1:
                correct += 1

        accuracy = correct / total if total > 0 else 0

        assert accuracy >= 0.85, f"Känslighetsbedömning accuracy för låg: {accuracy:.2%}"

    @pytest.mark.asyncio
    async def test_conservative_bias(self, llm_client):
        """
        Test: LLM är konservativ (hellre för känsligt än för lite).

        Vid osäkerhet ska modellen hellre klassa som HIGH än LOW
        (omvänt skaderekvisit).
        """
        ambiguous_cases = [
            "Maria berättar att hon ibland känner sig nere.",
            "Familjen har haft ekonomiska svårigheter.",
            "Barnen har ibland varit oroliga på kvällarna.",
        ]

        sensitivity_counts = Counter()

        for text in ambiguous_cases:
            prompt = build_sensitivity_prompt(
                text=text,
                context={},
                entities=[]
            )

            response = await llm_client.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )

            sensitivity_counts[response["sensitivity_level"]] += 1

        # Modellen ska INTE klassa dessa som LOW
        low_count = sensitivity_counts.get("LOW", 0)

        assert low_count == 0, \
            f"Modellen klassade {low_count} av {len(ambiguous_cases)} oklara fall som LOW"

    @pytest.mark.asyncio
    async def test_consistency(self, llm_client):
        """
        Test: Konsekvens över flera anrop.
        Samma input ska ge liknande output.
        """
        test_text = "Agnes har dokumenterad alkoholproblematik sedan 2018."

        responses = []

        for _ in range(3):
            prompt = build_sensitivity_prompt(
                text=test_text,
                context={},
                entities=[{"text": "Agnes", "type": "PERSON"}]
            )

            response = await llm_client.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.1  # Låg temperatur för konsekvens
            )

            responses.append(response)
            await asyncio.sleep(0.5)  # Undvik rate limiting

        # Alla ska ha samma sensitivity_level
        levels = [r["sensitivity_level"] for r in responses]

        assert len(set(levels)) == 1, \
            f"Inkonsekvent: fick olika nivåer {levels}"

        # Alla ska ha samma recommendation
        recommendations = [r["recommendation"] for r in responses]

        assert len(set(recommendations)) == 1, \
            f"Inkonsekvent: fick olika rekommendationer {recommendations}"

    @pytest.mark.asyncio
    async def test_child_protection(self, llm_client):
        """
        Test: Barn får förstärkt skydd.
        Uppgifter om barn ska alltid klassas som HIGH eller CRITICAL.
        """
        child_cases = [
            "Adrian, 5 år, har visat tecken på oro i förskolan.",
            "Barnet har sagt att pappa ibland blir arg.",
            "Skolsköterskan rapporterar att eleven ofta är trött.",
        ]

        for text in child_cases:
            prompt = build_sensitivity_prompt(
                text=text,
                context={"involves_children": True},
                entities=[{"text": "barnet", "type": "PERSON"}]
            )

            response = await llm_client.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )

            assert response["sensitivity_level"] in ["HIGH", "CRITICAL"], \
                f"Barnärende klassades som {response['sensitivity_level']}: {text[:50]}"

    @pytest.mark.asyncio
    async def test_category_accuracy(self, llm_client, gold_standard):
        """
        Test: Korrekt kategori tilldelas.
        """
        if not gold_standard:
            pytest.skip("Ingen gold standard data")

        category_correct = 0
        total = 0

        for case in gold_standard[:20]:
            prompt = build_sensitivity_prompt(
                text=case["text"],
                context=case.get("context", {}),
                entities=case.get("entities", [])
            )

            response = await llm_client.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )

            total += 1

            expected_category = case.get("expected_category")
            if expected_category:
                # Tillåt att rätt kategori är primär eller sekundär
                all_categories = [response["primary_category"]] + \
                                response.get("secondary_categories", [])

                if expected_category in all_categories:
                    category_correct += 1

        accuracy = category_correct / total if total > 0 else 0

        assert accuracy >= 0.80, f"Kategori-accuracy för låg: {accuracy:.2%}"

    @pytest.mark.asyncio
    async def test_reasoning_quality(self, llm_client):
        """
        Test: Motiveringar är meningsfulla.
        """
        test_text = "Socialtjänsten har mottagit en orosanmälan gällande barnen."

        prompt = build_sensitivity_prompt(
            text=test_text,
            context={},
            entities=[]
        )

        response = await llm_client.complete_json(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT
        )

        reasons = response.get("reasons", [])

        # Ska ha minst en motivering
        assert len(reasons) >= 1, "Saknar motivering"

        # Motiveringarna ska vara tillräckligt långa
        for reason in reasons:
            assert len(reason) >= 20, f"För kort motivering: {reason}"

        # Ska ha legal_basis
        legal_basis = response.get("legal_basis", "")
        assert "OSL" in legal_basis or "sekretess" in legal_basis.lower(), \
            f"Saknar lagstöd: {legal_basis}"
```

---

## 4. CI/CD PIPELINE

### 4.1 GitHub Actions Workflow

**Fil:** `.github/workflows/ci.yml`

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"
  POETRY_VERSION: "1.7.0"

jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install ruff mypy

      - name: Run ruff (linting)
        run: ruff check src tests

      - name: Run ruff (formatting)
        run: ruff format --check src tests

      - name: Run mypy (type checking)
        run: mypy src --ignore-missing-imports

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}

      - name: Install dependencies
        run: poetry install --with dev

      - name: Run unit tests
        run: |
          poetry run pytest tests/unit \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: menprovning_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install dependencies
        run: poetry install --with dev

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/menprovning_test
          REDIS_URL: redis://localhost:6379
        run: |
          poetry run pytest tests/integration -v

  ai-validation:
    name: AI Model Validation
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install dependencies
        run: poetry install --with dev

      - name: Download models
        run: |
          poetry run python -c "
          from transformers import AutoTokenizer, AutoModelForTokenClassification
          AutoTokenizer.from_pretrained('KB/bert-base-swedish-cased-ner')
          AutoModelForTokenClassification.from_pretrained('KB/bert-base-swedish-cased-ner')
          "

      - name: Run NER validation
        run: |
          poetry run pytest tests/validation/test_ner_accuracy.py \
            -v \
            --tb=short \
            --junitxml=reports/ner-validation.xml

      - name: Run classification validation
        run: |
          poetry run pytest tests/validation/test_classification_accuracy.py \
            -v \
            --tb=short \
            --junitxml=reports/classification-validation.xml

      - name: Upload validation reports
        uses: actions/upload-artifact@v4
        with:
          name: validation-reports
          path: reports/

  llm-validation:
    name: LLM Quality Validation
    runs-on: [self-hosted, gpu]  # Kör på egen runner med GPU
    needs: unit-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Check LLM availability
        run: |
          curl -f http://llm-server:8000/health || exit 1

      - name: Run LLM validation
        env:
          LLM_ENDPOINT: http://llm-server:8000/v1/chat/completions
        run: |
          poetry run pytest tests/validation/test_llm_quality.py \
            -v \
            --tb=short \
            --junitxml=reports/llm-validation.xml

      - name: Generate quality report
        run: |
          poetry run python validation/scripts/generate_report.py

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'

      - name: Run Bandit security linter
        run: |
          pip install bandit
          bandit -r src -ll

  build:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [integration-tests, security-scan]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build API image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: infrastructure/docker/Dockerfile.api
          push: false
          tags: menprovning-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 4.2 Pre-commit Hooks

**Fil:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, types-requests]
        args: [--ignore-missing-imports]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: detect-private-key

  - repo: local
    hooks:
      - id: run-unit-tests
        name: Run unit tests
        entry: poetry run pytest tests/unit -q --tb=no
        language: system
        pass_filenames: false
        always_run: true

      - id: check-test-coverage
        name: Check test coverage
        entry: poetry run pytest tests/unit --cov=src --cov-fail-under=80 -q --tb=no
        language: system
        pass_filenames: false
        always_run: true
```

---

## 5. MAKEFILE FÖR UTVECKLING

**Fil:** `Makefile`

```makefile
.PHONY: help install dev test lint format validate clean

PYTHON := python3.11
POETRY := poetry

help:
	@echo "Menprövningsverktyg - Utvecklingskommandon"
	@echo ""
	@echo "Setup:"
	@echo "  install      Installera alla dependencies"
	@echo "  dev          Sätt upp utvecklingsmiljö"
	@echo ""
	@echo "Test:"
	@echo "  test         Kör alla tester"
	@echo "  test-unit    Kör enhetstester"
	@echo "  test-int     Kör integrationstester"
	@echo "  test-val     Kör valideringstester"
	@echo "  coverage     Generera coverage-rapport"
	@echo ""
	@echo "Kvalitet:"
	@echo "  lint         Kör linting"
	@echo "  format       Formatera kod"
	@echo "  typecheck    Kör typkontroll"
	@echo ""
	@echo "AI Validering:"
	@echo "  validate-ner       Validera NER-precision"
	@echo "  validate-class     Validera klassificering"
	@echo "  validate-llm       Validera LLM-kvalitet"
	@echo "  validate-all       Kör alla valideringar"
	@echo "  report             Generera valideringsrapport"
	@echo ""
	@echo "Utveckling:"
	@echo "  run          Starta utvecklingsserver"
	@echo "  shell        Öppna Python-shell"
	@echo "  annotate     Starta annotationsverktyg"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Bygg Docker-images"
	@echo "  docker-up    Starta alla tjänster"
	@echo "  docker-down  Stoppa alla tjänster"

# === SETUP ===

install:
	$(POETRY) install --with dev

dev: install
	$(POETRY) run pre-commit install
	@echo "Utvecklingsmiljö redo!"

# === TESTER ===

test:
	$(POETRY) run pytest tests/ -v

test-unit:
	$(POETRY) run pytest tests/unit -v

test-int:
	$(POETRY) run pytest tests/integration -v

test-val:
	$(POETRY) run pytest tests/validation -v

coverage:
	$(POETRY) run pytest tests/unit \
		--cov=src \
		--cov-report=html \
		--cov-report=term-missing
	@echo "Coverage rapport: htmlcov/index.html"

# === KVALITET ===

lint:
	$(POETRY) run ruff check src tests

format:
	$(POETRY) run ruff format src tests

typecheck:
	$(POETRY) run mypy src --ignore-missing-imports

quality: lint typecheck
	@echo "Kvalitetskontroll klar!"

# === AI VALIDERING ===

validate-ner:
	$(POETRY) run pytest tests/validation/test_ner_accuracy.py -v \
		--tb=short \
		--junitxml=reports/ner-validation.xml

validate-class:
	$(POETRY) run pytest tests/validation/test_classification_accuracy.py -v \
		--tb=short \
		--junitxml=reports/classification-validation.xml

validate-llm:
	$(POETRY) run pytest tests/validation/test_llm_quality.py -v \
		--tb=short \
		--junitxml=reports/llm-validation.xml

validate-all: validate-ner validate-class validate-llm
	@echo "Alla valideringar klara!"

report:
	$(POETRY) run python validation/scripts/generate_report.py
	@echo "Rapport genererad: reports/validation_report.html"

# === BENCHMARKS ===

benchmark:
	$(POETRY) run pytest tests/benchmarks/ -v \
		--benchmark-only \
		--benchmark-json=reports/benchmark.json

benchmark-compare:
	$(POETRY) run pytest tests/benchmarks/ -v \
		--benchmark-only \
		--benchmark-compare=reports/benchmark_baseline.json

# === UTVECKLING ===

run:
	$(POETRY) run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

shell:
	$(POETRY) run ipython

annotate:
	@echo "Användning: make annotate FILE=path/to/document.pdf"
	$(POETRY) run python -m validation.scripts.annotate $(FILE)

# === GOLD STANDARD ===

generate-synthetic:
	$(POETRY) run python scripts/generate_synthetic_data.py \
		--output validation/gold_standard/synthetic \
		--count 50

# === DOCKER ===

docker-build:
	docker compose -f infrastructure/docker/docker-compose.yml build

docker-up:
	docker compose -f infrastructure/docker/docker-compose.yml up -d

docker-down:
	docker compose -f infrastructure/docker/docker-compose.yml down

docker-logs:
	docker compose -f infrastructure/docker/docker-compose.yml logs -f

# === CLEANUP ===

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage coverage.xml
	rm -rf reports/*.xml reports/*.html

# === CI SIMULERING ===

ci-local:
	@echo "=== Lint ==="
	$(MAKE) lint
	@echo "=== Type Check ==="
	$(MAKE) typecheck
	@echo "=== Unit Tests ==="
	$(MAKE) test-unit
	@echo "=== Coverage ==="
	$(MAKE) coverage
	@echo ""
	@echo "Lokal CI klar!"
```

---

## 6. UTVECKLINGS-SPRINTER

### Sprint 1 (Vecka 1-2): Grund & Extraktion

**Mål:** Fungerande dokumentinläsning med tester

```
☐ Projektstruktur enligt plan
☐ Poetry + dependencies
☐ Pre-commit hooks
☐ CI/CD pipeline (basic)
☐ PDFExtractor implementation
☐ OCR-fallback
☐ 10 annoterade testdokument (gold standard start)
☐ Unit tests för ingestion (>90% coverage)
☐ Validering: extraktion recall >= 98%
```

**Leverans:**
```bash
make test-unit  # Alla gröna
make validate-extraction  # >= 98% recall
```

---

### Sprint 2 (Vecka 3-4): NER

**Mål:** KBLab BERT NER integrerad och validerad

```
☐ BertNER implementation
☐ Regex-entiteter (personnummer, telefon, e-post)
☐ Entity linking (samma person = samma entitet)
☐ 20 ytterligare annoterade dokument
☐ Unit tests för NER
☐ Validering: NER F1 >= 87%
```

**Leverans:**
```bash
make validate-ner  # F1 >= 87%, PERSON recall >= 95%
```

---

### Sprint 3 (Vecka 5-6): Klassificering

**Mål:** Känslighetskategorisering med BERT

```
☐ BERT-klassificerare för kategorier
☐ Regelbaserad fallback
☐ Ensemble-kombination
☐ 30 ytterligare annoterade dokument
☐ Validering: klassificering accuracy >= 85%
```

**Leverans:**
```bash
make validate-class  # Accuracy >= 85%
```

---

### Sprint 4 (Vecka 7-8): GPT-OSS Integration

**Mål:** LLM-integration för djupanalys

```
☐ GPTOSSClient implementation
☐ Prompt-templates (sensitivity, relations, reasoning)
☐ JSON-parsing med felhantering
☐ Retry-logik och fallback
☐ Validering: LLM-kvalitet enligt spec
```

**Leverans:**
```bash
make validate-llm  # Alla tester gröna
```

---

### Sprint 5 (Vecka 9-10): Analysmotor

**Mål:** Komplett analyskedja BERT → LLM

```
☐ Orchestration layer
☐ Relationsgraf (NetworkX)
☐ Riskpoängsättning
☐ Aggregering av resultat
☐ End-to-end pipeline
☐ Validering: 50 dokument genom hela kedjan
```

**Leverans:**
```bash
make test-int  # Integration tests gröna
make validate-all  # Alla valideringar OK
```

---

### Sprint 6 (Vecka 11-12): Juridisk Logik & Maskning

**Mål:** OSL-regler och maskning

```
☐ OSL-regelmotor
☐ Tidsbedömning (70-årsgräns)
☐ Samtyckeshantering
☐ Motiveringsgenerering
☐ Textmaskning
☐ PDF-maskning
☐ Valideringstester för juridisk korrekthet
```

---

### Sprint 7 (Vecka 13-14): API & Arbetsflöde

**Mål:** REST API och ärendehantering

```
☐ FastAPI endpoints
☐ Ärendehantering (CRUD)
☐ Statushantering
☐ Audit logging
☐ API-dokumentation (OpenAPI)
☐ Integrationstester för API
```

---

### Sprint 8 (Vecka 15-16): Frontend MVP

**Mål:** Grundläggande webb-UI

```
☐ React-app setup
☐ Ärendevy
☐ Dokumentuppladdning
☐ Analysresultat med färgkodning
☐ Interaktiv maskning
☐ Beslutsformulär
```

---

### Sprint 9-10 (Vecka 17-20): Integration & Säkerhet

**Mål:** Produktionsredo system

```
☐ Integration med befintligt system
☐ Säkerhetsaudit
☐ Penetrationstester
☐ Prestandaoptimering
☐ Monitoring (Prometheus/Grafana)
☐ Dokumentation
☐ Utbildningsmaterial
```

---

## 7. VALIDERINGSRAPPORT-GENERATOR

**Fil:** `validation/scripts/generate_report.py`

```python
"""
Genererar HTML-rapport från valideringsresultat.
"""

from pathlib import Path
from datetime import datetime
import json
import xml.etree.ElementTree as ET
from jinja2 import Template

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Valideringsrapport - {{ timestamp }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .metric { display: inline-block; margin: 10px 20px; text-align: center; }
        .metric-value { font-size: 32px; font-weight: bold; }
        .metric-label { color: #666; }
        .pass { color: #28a745; }
        .fail { color: #dc3545; }
        .warn { color: #ffc107; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; }
        .test-pass { color: #28a745; }
        .test-fail { color: #dc3545; }
    </style>
</head>
<body>
    <h1>Menprövningsverktyg - Valideringsrapport</h1>
    <p>Genererad: {{ timestamp }}</p>

    <div class="summary">
        <h2>Sammanfattning</h2>
        <div class="metric">
            <div class="metric-value {{ 'pass' if ner_f1 >= 0.87 else 'fail' }}">
                {{ "%.1f"|format(ner_f1 * 100) }}%
            </div>
            <div class="metric-label">NER F1</div>
        </div>
        <div class="metric">
            <div class="metric-value {{ 'pass' if class_acc >= 0.85 else 'fail' }}">
                {{ "%.1f"|format(class_acc * 100) }}%
            </div>
            <div class="metric-label">Klassificering</div>
        </div>
        <div class="metric">
            <div class="metric-value {{ 'pass' if llm_quality >= 0.85 else 'fail' }}">
                {{ "%.1f"|format(llm_quality * 100) }}%
            </div>
            <div class="metric-label">LLM Kvalitet</div>
        </div>
        <div class="metric">
            <div class="metric-value {{ 'pass' if all_pass else 'fail' }}">
                {{ total_pass }}/{{ total_tests }}
            </div>
            <div class="metric-label">Tester</div>
        </div>
    </div>

    <h2>NER Validering</h2>
    <table>
        <tr>
            <th>Test</th>
            <th>Resultat</th>
            <th>Detaljer</th>
        </tr>
        {% for test in ner_tests %}
        <tr>
            <td>{{ test.name }}</td>
            <td class="{{ 'test-pass' if test.passed else 'test-fail' }}">
                {{ 'PASS' if test.passed else 'FAIL' }}
            </td>
            <td>{{ test.details }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2>Klassificering Validering</h2>
    <table>
        <tr>
            <th>Test</th>
            <th>Resultat</th>
            <th>Detaljer</th>
        </tr>
        {% for test in class_tests %}
        <tr>
            <td>{{ test.name }}</td>
            <td class="{{ 'test-pass' if test.passed else 'test-fail' }}">
                {{ 'PASS' if test.passed else 'FAIL' }}
            </td>
            <td>{{ test.details }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2>LLM Validering</h2>
    <table>
        <tr>
            <th>Test</th>
            <th>Resultat</th>
            <th>Detaljer</th>
        </tr>
        {% for test in llm_tests %}
        <tr>
            <td>{{ test.name }}</td>
            <td class="{{ 'test-pass' if test.passed else 'test-fail' }}">
                {{ 'PASS' if test.passed else 'FAIL' }}
            </td>
            <td>{{ test.details }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2>Rekommendationer</h2>
    <ul>
        {% for rec in recommendations %}
        <li>{{ rec }}</li>
        {% endfor %}
    </ul>
</body>
</html>
"""


def parse_junit_xml(xml_path: Path) -> list:
    """Parsa JUnit XML-rapport."""
    if not xml_path.exists():
        return []

    tree = ET.parse(xml_path)
    root = tree.getroot()

    tests = []
    for testcase in root.iter("testcase"):
        name = testcase.get("name", "Unknown")
        failure = testcase.find("failure")

        tests.append({
            "name": name,
            "passed": failure is None,
            "details": failure.text[:100] if failure is not None else "OK"
        })

    return tests


def calculate_metrics(tests: list) -> float:
    """Beräkna success rate."""
    if not tests:
        return 0.0
    passed = sum(1 for t in tests if t["passed"])
    return passed / len(tests)


def generate_recommendations(metrics: dict) -> list:
    """Generera rekommendationer baserat på metrics."""
    recs = []

    if metrics["ner_f1"] < 0.87:
        recs.append("NER: Överväg att fine-tuna BERT-modellen på domänspecifik data")

    if metrics["class_acc"] < 0.85:
        recs.append("Klassificering: Utöka träningsdata med fler exempel per kategori")

    if metrics["llm_quality"] < 0.85:
        recs.append("LLM: Förbättra prompts med fler few-shot exempel")

    if not recs:
        recs.append("Alla kvalitetsmål uppnådda!")

    return recs


def main():
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    # Parsa testresultat
    ner_tests = parse_junit_xml(reports_dir / "ner-validation.xml")
    class_tests = parse_junit_xml(reports_dir / "classification-validation.xml")
    llm_tests = parse_junit_xml(reports_dir / "llm-validation.xml")

    # Beräkna metrics
    all_tests = ner_tests + class_tests + llm_tests

    metrics = {
        "ner_f1": calculate_metrics(ner_tests),
        "class_acc": calculate_metrics(class_tests),
        "llm_quality": calculate_metrics(llm_tests),
        "total_pass": sum(1 for t in all_tests if t["passed"]),
        "total_tests": len(all_tests),
        "all_pass": all(t["passed"] for t in all_tests) if all_tests else False
    }

    # Generera rapport
    template = Template(REPORT_TEMPLATE)
    html = template.render(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ner_tests=ner_tests,
        class_tests=class_tests,
        llm_tests=llm_tests,
        recommendations=generate_recommendations(metrics),
        **metrics
    )

    output_path = reports_dir / "validation_report.html"
    output_path.write_text(html)

    print(f"Rapport genererad: {output_path}")
    print(f"\nSammanfattning:")
    print(f"  NER F1: {metrics['ner_f1']:.1%}")
    print(f"  Klassificering: {metrics['class_acc']:.1%}")
    print(f"  LLM Kvalitet: {metrics['llm_quality']:.1%}")
    print(f"  Tester: {metrics['total_pass']}/{metrics['total_tests']}")


if __name__ == "__main__":
    main()
```

---

## 8. JURIDISKT REGELRAMVERK

### 8.1 Strukturerade dokument för AI-analys

För att AI:n ska kunna göra korrekta menprövningsbedömningar krävs strukturerade, maskinläsbara regler. Följande dokument har skapats:

| Dokument | Syfte | Format |
|----------|-------|--------|
| `docs/MENPROVNING_HANDBOK.md` | Komplett handbok med OSL-regler | Markdown |
| `docs/OSL_RULES.json` | Maskinläsbar regelstruktur | JSON |
| `docs/MALL_REGELINSAMLING.md` | Mall för arkivariers regelinsamling | Markdown |

### 8.2 Regelstruktur

Handboken innehåller:
- **Lagrum-kopplingar**: Varje uppgiftstyp länkas till relevant paragraf i OSL
- **Känslighetskategorier**: HEALTH, ADDICTION, VIOLENCE, FAMILY, etc.
- **Entitetstyper**: PERSON, SSN, PHONE, ADDRESS, etc.
- **Rollanalys**: Beställare, tredje man, anmälare, tjänsteman
- **Beslutsstöd**: Konkreta regler för maskning/utlämnande

### 8.3 Arkivariernas bidrag

Arkivarier ska komplettera regelverket genom att:
1. Fylla i `MALL_REGELINSAMLING.md` med verksamhetsspecifika regler
2. Validera AI:ns bedömningar mot gold standard
3. Dokumentera edge cases och undantag

### 8.4 Testfil

Filen `testfilAi.pdf` (31 sidor) används som referens för validering. Den innehåller typiskt innehåll från en socialakt:
- Personnummer, namn, adresser
- Anmälningar från tredje part
- Känsliga uppgifter (missbruk, ekonomi, boende)
- Journalanteckningar och utredningar

---

## 9. SAMMANFATTNING

### Nyckelpunkter i denna plan:

1. **Modulär arkitektur** - Varje modul kan utvecklas, testas och valideras oberoende

2. **Testdriven utveckling** - Tester skrivs först, implementation följer

3. **Gold standard dataset** - Manuellt annoterad data för att validera AI-komponenter

4. **Automatisk validering** - CI/CD kör valideringstester vid varje push

5. **Tydliga kvalitetsmål:**
   - Extraktion recall: >= 98%
   - NER F1: >= 87%
   - Klassificering accuracy: >= 85%
   - LLM konsekvens och konservativ bias

6. **Inkrementell leverans** - Fungerande system efter varje sprint

7. **Rapportering** - Automatisk generering av valideringsrapporter

### Nästa steg:

1. ~~Skapa projektstruktur enligt plan~~ **KLART**
2. ~~Skapa juridiskt regelramverk~~ **KLART**
3. **Låt arkivarier fylla i MALL_REGELINSAMLING.md**
4. Börja med Sprint 1 (dokumentinläsning)
5. Parallellt: Påbörja annotation av gold standard dataset
6. Sätt upp CI/CD pipeline

---

**Dokument slut**
