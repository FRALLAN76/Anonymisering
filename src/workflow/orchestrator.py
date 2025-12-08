"""Workflow-orchestrator for menprovning.

Koordinerar hela pipelinen fran dokument till maskerad utdata.
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.core.models import (
    AnalysisResult,
    Entity,
    ExtractedDocument,
    SensitivityAssessment,
    SensitivityLevel,
)
from src.ingestion.pdf_extractor import PDFExtractor
from src.ner.regex_ner import RegexNER
from src.ner.postprocessor import EntityPostprocessor
from src.analysis.sensitivity_analyzer import SensitivityAnalyzer, SensitivityAnalyzerConfig
from src.masking.masker import EntityMasker, MaskingConfig, MaskingResult
from src.llm.client import LLMConfig

logger = logging.getLogger(__name__)


@dataclass
class WorkflowConfig:
    """Konfiguration for workflow."""

    # LLM
    use_llm: bool = True
    llm_api_key: Optional[str] = None
    llm_model: str = "openai/gpt-4o-mini"

    # NER
    use_bert_ner: bool = True  # KB-BERT for battre namnigenkanning

    # Maskning
    masking_style: str = "brackets"

    # Bearbetning
    max_sections_to_analyze: int = 50
    analyze_all_sections: bool = False


@dataclass
class WorkflowResult:
    """Resultat fran workflow."""

    document_id: str
    source_path: str
    original_text: str
    masked_text: str
    entities: list[Entity]
    assessments: list[SensitivityAssessment]
    masking_result: MaskingResult
    overall_sensitivity: SensitivityLevel
    processing_time_ms: float
    statistics: dict = field(default_factory=dict)


class MenprovningWorkflow:
    """
    Huvudworkflow for menprovning.

    Koordinerar:
    1. Dokumentextraktion (PDF -> text)
    2. NER (identifiera entiteter)
    3. Kanslighetsanalys (LLM + regler)
    4. Maskning (applicera regler)
    """

    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        Initiera workflow.

        Args:
            config: Konfiguration
        """
        self.config = config or WorkflowConfig()

        # Initiera komponenter
        self._extractor = PDFExtractor()
        self._regex_ner = RegexNER()
        self._postprocessor = EntityPostprocessor()
        self._masker: Optional[EntityMasker] = None
        self._analyzer: Optional[SensitivityAnalyzer] = None

    @property
    def masker(self) -> EntityMasker:
        """Lazy loading av masker."""
        if self._masker is None:
            from src.masking.masker import MaskingStyle
            style_map = {
                "brackets": MaskingStyle.BRACKETS,
                "redacted": MaskingStyle.REDACTED,
                "placeholder": MaskingStyle.PLACEHOLDER,
                "anonymized": MaskingStyle.ANONYMIZED,
            }
            config = MaskingConfig(
                style=style_map.get(self.config.masking_style, MaskingStyle.BRACKETS)
            )
            self._masker = EntityMasker(config)
        return self._masker

    @property
    def analyzer(self) -> SensitivityAnalyzer:
        """Lazy loading av analyzer."""
        if self._analyzer is None:
            llm_config = None
            if self.config.use_llm and self.config.llm_api_key:
                llm_config = LLMConfig(
                    api_key=self.config.llm_api_key,
                    model=self.config.llm_model,
                )
            analyzer_config = SensitivityAnalyzerConfig(llm_config=llm_config)
            self._analyzer = SensitivityAnalyzer(analyzer_config)
        return self._analyzer

    def process_document(
        self,
        document_path: str,
        requester_ssn: Optional[str] = None,
    ) -> WorkflowResult:
        """
        Bearbeta ett dokument genom hela pipelinen.

        Args:
            document_path: Sokvag till dokumentet
            requester_ssn: Bestellarens personnummer (for partsinsyn)

        Returns:
            WorkflowResult med all information
        """
        start_time = time.time()
        path = Path(document_path)

        logger.info(f"Borjar bearbetning av {path.name}")

        # 1. Extrahera text
        logger.info("Steg 1: Extraherar text...")
        doc = self._extractor.extract(str(path))

        # 2. NER
        logger.info("Steg 2: Kor NER...")
        entities = self._run_ner(doc.full_text)

        # 3. Kanslighetsanalys
        logger.info("Steg 3: Analyserar kanslighet...")
        assessments, overall_level = self._analyze_sensitivity(doc.full_text, entities)

        # 4. Identifiera bestellarens entiteter
        requester_entities = set()
        if requester_ssn:
            requester_entities = self._identify_requester_entities(
                requester_ssn, entities, doc.full_text
            )

        # 5. Maskning
        logger.info("Steg 4: Applicerar maskning...")
        masking_result = self.masker.mask_text(
            doc.full_text,
            entities,
            assessments,
            requester_entities,
        )

        # Berakna tid
        processing_time = (time.time() - start_time) * 1000

        # Skapa statistik
        statistics = self._create_statistics(
            doc, entities, assessments, masking_result
        )

        logger.info(f"Bearbetning klar pa {processing_time:.0f}ms")

        return WorkflowResult(
            document_id=path.stem,
            source_path=str(path),
            original_text=doc.full_text,
            masked_text=masking_result.masked_text,
            entities=entities,
            assessments=assessments,
            masking_result=masking_result,
            overall_sensitivity=overall_level,
            processing_time_ms=processing_time,
            statistics=statistics,
        )

    def process_text(
        self,
        text: str,
        document_id: str = "unknown",
        requester_ssn: Optional[str] = None,
    ) -> WorkflowResult:
        """
        Bearbeta text direkt (utan PDF-extraktion).

        Args:
            text: Texten att bearbeta
            document_id: Identifierare
            requester_ssn: Bestellarens personnummer

        Returns:
            WorkflowResult
        """
        start_time = time.time()

        # 1. NER
        entities = self._run_ner(text)

        # 2. Kanslighetsanalys
        assessments, overall_level = self._analyze_sensitivity(text, entities)

        # 3. Identifiera bestellarens entiteter
        requester_entities = set()
        if requester_ssn:
            requester_entities = self._identify_requester_entities(
                requester_ssn, entities, text
            )

        # 4. Maskning
        masking_result = self.masker.mask_text(
            text,
            entities,
            assessments,
            requester_entities,
        )

        processing_time = (time.time() - start_time) * 1000

        return WorkflowResult(
            document_id=document_id,
            source_path="",
            original_text=text,
            masked_text=masking_result.masked_text,
            entities=entities,
            assessments=assessments,
            masking_result=masking_result,
            overall_sensitivity=overall_level,
            processing_time_ms=processing_time,
            statistics={},
        )

    def _run_ner(self, text: str) -> list[Entity]:
        """Kor NER pa text."""
        # Regex NER
        raw_entities = self._regex_ner.extract_entities(text)

        # BERT NER (valfritt)
        bert_entities = None
        if self.config.use_bert_ner:
            try:
                from src.ner.bert_ner import BertNER
                bert_ner = BertNER()
                bert_entities = bert_ner.extract_entities(text)
            except Exception as e:
                logger.warning(f"BERT NER misslyckades: {e}")

        # Postprocessing
        return self._postprocessor.process(raw_entities, bert_entities)

    def _analyze_sensitivity(
        self,
        text: str,
        entities: list[Entity],
    ) -> tuple[list[SensitivityAssessment], SensitivityLevel]:
        """Analysera kanslighet i text."""
        assessments = []

        # Dela upp i sektioner
        sections = self.analyzer.split_into_sections(text)

        # Begrinsa antal sektioner att analysera
        sections_to_analyze = sections
        if not self.config.analyze_all_sections:
            sections_to_analyze = sections[:self.config.max_sections_to_analyze]

        # Analysera varje sektion
        for section in sections_to_analyze:
            try:
                assessment = self.analyzer.analyze_section(section, entities)
                assessments.append(assessment)
            except Exception as e:
                logger.warning(f"Kunde inte analysera sektion: {e}")

        # Berakna overgripande niva
        overall_level = self._calculate_overall_level(assessments)

        return assessments, overall_level

    def _calculate_overall_level(
        self,
        assessments: list[SensitivityAssessment],
    ) -> SensitivityLevel:
        """Berakna overgripande kanslighetsniva."""
        if not assessments:
            return SensitivityLevel.MEDIUM

        # Hogsta nivla vinner
        level_priority = {
            SensitivityLevel.CRITICAL: 4,
            SensitivityLevel.HIGH: 3,
            SensitivityLevel.MEDIUM: 2,
            SensitivityLevel.LOW: 1,
        }

        max_level = SensitivityLevel.LOW
        max_priority = 0

        for assessment in assessments:
            priority = level_priority.get(assessment.level, 0)
            if priority > max_priority:
                max_priority = priority
                max_level = assessment.level

        return max_level

    def _identify_requester_entities(
        self,
        requester_ssn: str,
        entities: list[Entity],
        text: str,
    ) -> set[str]:
        """
        Identifiera vilka entiteter som tillhor bestallaren.

        Args:
            requester_ssn: Bestellarens personnummer
            entities: Alla entiteter
            text: Dokumenttexten

        Returns:
            Set med entitetstexter som tillhor bestallaren
        """
        requester_entities = set()

        # Laga till personnumret
        requester_entities.add(requester_ssn)

        # Normalisera personnummer (med/utan bindestreck)
        normalized = requester_ssn.replace("-", "")
        requester_entities.add(normalized)
        if len(normalized) == 12:
            requester_entities.add(f"{normalized[:8]}-{normalized[8:]}")
        elif len(normalized) == 10:
            requester_entities.add(f"{normalized[:6]}-{normalized[6:]}")

        # TODO: Identifiera bestellarens namn baserat pa personnummer
        # Detta kraver integration med folkbokforingsdata eller
        # analys av dokumentet for att koppla namn till personnummer

        return requester_entities

    def _create_statistics(
        self,
        doc: ExtractedDocument,
        entities: list[Entity],
        assessments: list[SensitivityAssessment],
        masking_result: MaskingResult,
    ) -> dict:
        """Skapa statistik over bearbetningen."""
        from collections import Counter

        entity_types = Counter(e.type.value for e in entities)
        category_counts = Counter(a.primary_category.value for a in assessments)
        level_counts = Counter(a.level.value for a in assessments)

        return {
            "document": {
                "pages": doc.total_pages,
                "characters": len(doc.full_text),
            },
            "entities": {
                "total": len(entities),
                "by_type": dict(entity_types),
            },
            "assessments": {
                "total": len(assessments),
                "by_category": dict(category_counts),
                "by_level": dict(level_counts),
            },
            "masking": masking_result.statistics,
        }


def create_workflow(
    api_key: Optional[str] = None,
    use_llm: bool = True,
    masking_style: str = "brackets",
) -> MenprovningWorkflow:
    """
    Fabriksfunktion for att skapa en workflow.

    Args:
        api_key: OpenRouter API-nyckel
        use_llm: Anvand LLM for analys
        masking_style: Maskeringsstil

    Returns:
        Konfigurerad MenprovningWorkflow
    """
    config = WorkflowConfig(
        use_llm=use_llm,
        llm_api_key=api_key,
        masking_style=masking_style,
    )
    return MenprovningWorkflow(config)
