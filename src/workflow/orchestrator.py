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
    DocumentParty,
    Entity,
    ExtractedDocument,
    PersonRole,
    SensitivityAssessment,
    SensitivityLevel,
    RequesterType,
    RequesterContext,
)
from src.ingestion.pdf_extractor import PDFExtractor
from src.ner.regex_ner import RegexNER
from src.ner.postprocessor import EntityPostprocessor
from src.analysis.sensitivity_analyzer import SensitivityAnalyzer, SensitivityAnalyzerConfig
from src.analysis.party_analyzer import PartyAnalyzer, PartyAnalyzerConfig
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
    parties: list[DocumentParty] = field(default_factory=list)  # Identifierade parter


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
        self._party_analyzer: Optional[PartyAnalyzer] = None

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

    @property
    def party_analyzer(self) -> PartyAnalyzer:
        """Lazy loading av partsanalysator."""
        if self._party_analyzer is None:
            llm_config = None
            if self.config.use_llm and self.config.llm_api_key:
                llm_config = LLMConfig(
                    api_key=self.config.llm_api_key,
                    model=self.config.llm_model,
                )
            analyzer_config = PartyAnalyzerConfig(llm_config=llm_config)
            self._party_analyzer = PartyAnalyzer(analyzer_config)
        return self._party_analyzer

    def process_document(
        self,
        document_path: str,
        requester_ssn: Optional[str] = None,
        requester_type: Optional[RequesterType] = None,
        requester_party_id: Optional[str] = None,
        requester_context: Optional[RequesterContext] = None,
    ) -> WorkflowResult:
        """
        Bearbeta ett dokument genom hela pipelinen.

        Args:
            document_path: Sokvag till dokumentet
            requester_ssn: Bestellarens personnummer (for partsinsyn)
            requester_type: Typ av bestallare (SUBJECT_SELF, PARENT_1, etc.)
            requester_party_id: Part-ID om bestallaren ar identifierad part
            requester_context: Kravstallningskontext fran dialog

        Returns:
            WorkflowResult med all information
        """
        start_time = time.time()
        path = Path(document_path)

        # Anvand kontext om tillganglig
        ctx = requester_context or getattr(self, 'requester_context', None)
        if ctx:
            requester_type = requester_type or ctx.requester_type
            requester_ssn = requester_ssn or ctx.requester_ssn
            logger.info(f"Kravstallning: {ctx.requester_type}, relation: {ctx.relation_type}")

        logger.info(f"Borjar bearbetning av {path.name}")

        # 1. Extrahera text
        logger.info("Steg 1: Extraherar text...")
        doc = self._extractor.extract(str(path))

        # 2. NER
        logger.info("Steg 2: Kor NER...")
        entities = self._run_ner(doc.full_text)

        # 3. Partsanalys (identifiera alla parter)
        logger.info("Steg 3: Identifierar parter...")
        parties = self._analyze_parties(doc.full_text, entities)

        # 4. Kanslighetsanalys
        logger.info("Steg 4: Analyserar kanslighet...")
        assessments, overall_level = self._analyze_sensitivity(doc.full_text, entities)

        # 5. Identifiera bestallarens entiteter och part
        requester_entities = set()
        requester_party_id = self._identify_requester_party(
            requester_ssn, requester_type, requester_party_id,
            parties, entities, doc.full_text
        )

        if requester_ssn:
            requester_entities = self._identify_requester_entities(
                requester_ssn, entities, doc.full_text
            )

        # 6. Maskning med partsinsyn och kravstallningskontext
        logger.info("Steg 5: Applicerar maskning...")
        masking_result = self._apply_party_aware_masking(
            doc.full_text,
            entities,
            assessments,
            requester_type or RequesterType.PUBLIC,
            requester_party_id,
            parties,
            ctx,
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
            parties=parties,
        )

    def process_text(
        self,
        text: str,
        document_id: str = "unknown",
        requester_ssn: Optional[str] = None,
        requester_type: Optional[RequesterType] = None,
        requester_party_id: Optional[str] = None,
        requester_context: Optional[RequesterContext] = None,
    ) -> WorkflowResult:
        """
        Bearbeta text direkt (utan PDF-extraktion).

        Args:
            text: Texten att bearbeta
            document_id: Identifierare
            requester_ssn: Bestellarens personnummer
            requester_type: Typ av bestallare (SUBJECT_SELF, PARENT_1, etc.)
            requester_party_id: Part-ID om bestallaren ar identifierad part
            requester_context: Kravstallningskontext fran dialog

        Returns:
            WorkflowResult
        """
        start_time = time.time()

        # Anvand kontext om tillganglig
        ctx = requester_context or getattr(self, 'requester_context', None)
        if ctx:
            requester_type = requester_type or ctx.requester_type
            requester_ssn = requester_ssn or ctx.requester_ssn

        # 1. NER
        entities = self._run_ner(text)

        # 2. Partsanalys
        parties = self._analyze_parties(text, entities)

        # 3. Kanslighetsanalys
        assessments, overall_level = self._analyze_sensitivity(text, entities)

        # 4. Identifiera beställarens entiteter och part
        requester_entities = set()
        requester_party_id = self._identify_requester_party(
            requester_ssn, requester_type, requester_party_id,
            parties, entities, text
        )

        if requester_ssn:
            requester_entities = self._identify_requester_entities(
                requester_ssn, entities, text
            )

        # 5. Maskning med partsinsyn och kravstallningskontext
        masking_result = self._apply_party_aware_masking(
            text,
            entities,
            assessments,
            requester_type or RequesterType.PUBLIC,
            requester_party_id,
            parties,
            ctx,
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
            parties=parties,
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

        # Postprocessing med LLM-stöd
        llm_config = None
        if self.config.use_llm and self.config.llm_api_key:
            llm_config = LLMConfig(
                api_key=self.config.llm_api_key,
                model=self.config.llm_model,
            )

        entities = self._postprocessor.process(
            raw_entities, 
            bert_entities, 
            text=text, 
            llm_config=llm_config
        )

        # Slå samman angränsande personnamn (t.ex. "Anna" + "Andersson" -> "Anna Andersson")
        entities = self._postprocessor.merge_adjacent_persons(entities)

        return entities

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

    def _analyze_parties(
        self,
        text: str,
        entities: list[Entity],
    ) -> list:
        """
        Analysera och identifiera alla parter i dokumentet.

        Args:
            text: Dokumenttexten
            entities: Identifierade entiteter

        Returns:
            Lista med DocumentParty-objekt
        """
        try:
            return self.party_analyzer.identify_parties(text, entities)
        except Exception as e:
            logger.warning(f"Partsanalys misslyckades: {e}")
            return []

    def _identify_requester_party(
        self,
        requester_ssn: Optional[str],
        requester_type: Optional[RequesterType],
        requester_party_id: Optional[str],
        parties: list,
        entities: list[Entity],
        text: str,
    ) -> Optional[str]:
        """
        Identifiera beställarens part-ID.

        Args:
            requester_ssn: Beställarens personnummer
            requester_type: Typ av beställare
            requester_party_id: Explicit part-ID
            parties: Alla identifierade parter
            entities: Alla entiteter
            text: Dokumenttexten

        Returns:
            Beställarens part-ID eller None
        """
        # Om explicit part-ID anges, använd det
        if requester_party_id:
            return requester_party_id

        # Om inga parter identifierats, returnera None
        if not parties:
            return None

        # Försök matcha personnummer till part
        if requester_ssn:
            normalized_ssn = requester_ssn.replace("-", "")
            for party in parties:
                if party.ssn and party.ssn.replace("-", "") == normalized_ssn:
                    return party.party_id

        # Om ingen explicit match, använd heuristik baserat på requester_type
        if requester_type == RequesterType.SUBJECT_SELF:
            # Huvudpersonen - försök hitta SUBJECT-rollen
            for party in parties:
                if party.role == PersonRole.SUBJECT:
                    return party.party_id
        
        elif requester_type in (RequesterType.PARENT_1, RequesterType.PARENT_2):
            # Förälder - försök hitta föräldrarollen
            for party in parties:
                if party.relation in ["mamma", "pappa", "förälder"]:
                    return party.party_id

        # Default: första parten
        return parties[0].party_id if parties else None

    def _apply_party_aware_masking(
        self,
        text: str,
        entities: list[Entity],
        assessments: list[SensitivityAssessment],
        requester_type: RequesterType,
        requester_party_id: Optional[str],
        parties: list,
        requester_context: Optional[RequesterContext] = None,
    ) -> MaskingResult:
        """
        Applicera maskning med partsinsyn och kravstallningskontext.

        Args:
            text: Texten att maskera
            entities: Alla entiteter
            assessments: Känslighetsbedömningar
            requester_type: Typ av beställare
            requester_party_id: Beställarens part-ID
            parties: Alla identifierade parter
            requester_context: Kravstallningskontext fran dialog

        Returns:
            MaskingResult
        """
        # Hämta maskeringsregler baserat på beställartyp
        masking_rules = self.party_analyzer.get_masking_rules(
            requester_type, requester_party_id, parties
        )

        # Standardmaskering för entiteter som inte har specifika regler
        requester_entities = set()
        if requester_party_id:
            # Hitta beställarens entiteter baserat på part-ID
            for party in parties:
                if party.party_id == requester_party_id:
                    # Lägg till alla namn och alias för denna part
                    if party.name:
                        requester_entities.add(party.name)
                    requester_entities.update(party.aliases)
                    if party.ssn:
                        requester_entities.add(party.ssn)
                        requester_entities.add(party.ssn.replace("-", ""))

        # Bestam maskeringsstranghet baserat pa kontext
        strictness = "MODERATE"
        if requester_context:
            strictness = requester_context.get_masking_strictness()
            logger.info(f"Maskeringsniva fran kravstallning: {strictness}")

            # Om samtycke finns, kan vi vara mer generosa
            if requester_context.has_consent:
                logger.info("Samtycke finns - kan lamna ut mer")
                strictness = "RELAXED"

        # Applicera standardmaskering med stranghetsniva
        return self.masker.mask_text(
            text,
            entities,
            assessments,
            requester_entities,
            masking_strictness=strictness,
        )

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
    analyze_all_sections: bool = True,
    requester_context: Optional["RequesterContext"] = None,
) -> MenprovningWorkflow:
    """
    Fabriksfunktion for att skapa en workflow.

    Args:
        api_key: OpenRouter API-nyckel
        use_llm: Anvand LLM for analys
        masking_style: Maskeringsstil
        analyze_all_sections: Analysera hela dokumentet
        requester_context: Kravstallningskontext (vem begar, relation, etc.)

    Returns:
        Konfigurerad MenprovningWorkflow
    """
    config = WorkflowConfig(
        use_llm=use_llm,
        llm_api_key=api_key,
        masking_style=masking_style,
        analyze_all_sections=analyze_all_sections,
    )
    workflow = MenprovningWorkflow(config)
    workflow.requester_context = requester_context
    return workflow
