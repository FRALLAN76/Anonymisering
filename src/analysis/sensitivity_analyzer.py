"""Känslighetsbedömning med LLM och OSL-regler.

Analyserar dokument och bedömer känslighetsnivå enligt OSL kapitel 26.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.core.models import (
    Entity,
    EntityType,
    MaskingAction,
    PersonRole,
    SensitivityAssessment,
    SensitivityCategory,
    SensitivityLevel,
)
from src.llm.client import LLMClient, LLMConfig
from src.llm.prompts import (
    SENSITIVITY_SYSTEM_PROMPT,
    ANALYZE_SECTION_PROMPT,
    ROLE_IDENTIFICATION_PROMPT,
    DOCUMENT_OVERVIEW_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class SensitivityAnalyzerConfig:
    """Konfiguration för känslighetsbedömning."""

    # LLM-inställningar
    llm_config: Optional[LLMConfig] = None

    # Analys-inställningar
    max_section_length: int = 2000
    min_section_length: int = 50
    batch_size: int = 5

    # OSL-regler
    osl_rules_path: Optional[str] = None

    # Konfidenströsklar
    min_confidence_for_mask: float = 0.6
    min_confidence_for_release: float = 0.8


class SensitivityAnalyzer:
    """
    Analyserar text för känslighetsbedömning enligt OSL.

    Kombinerar:
    - LLM-baserad innehållsanalys
    - Nyckelordsbaserad kategorisering
    - OSL-regelapplikation
    """

    # Mappning från strängvärden till enum
    CATEGORY_MAP = {
        "HEALTH": SensitivityCategory.HEALTH,
        "MENTAL_HEALTH": SensitivityCategory.MENTAL_HEALTH,
        "ADDICTION": SensitivityCategory.ADDICTION,
        "VIOLENCE": SensitivityCategory.VIOLENCE,
        "FAMILY": SensitivityCategory.FAMILY,
        "ECONOMY": SensitivityCategory.ECONOMY,
        "HOUSING": SensitivityCategory.HOUSING,
        "SEXUAL": SensitivityCategory.SEXUAL,
        "CRIMINAL": SensitivityCategory.CRIMINAL,
        "NEUTRAL": SensitivityCategory.NEUTRAL,
    }

    LEVEL_MAP = {
        "CRITICAL": SensitivityLevel.CRITICAL,
        "HIGH": SensitivityLevel.HIGH,
        "MEDIUM": SensitivityLevel.MEDIUM,
        "LOW": SensitivityLevel.LOW,
    }

    ACTION_MAP = {
        "RELEASE": MaskingAction.RELEASE,
        "MASK_PARTIAL": MaskingAction.MASK_PARTIAL,
        "MASK_COMPLETE": MaskingAction.MASK_COMPLETE,
        "ASSESS": MaskingAction.ASSESS,
    }

    def __init__(self, config: Optional[SensitivityAnalyzerConfig] = None):
        """
        Initiera analyzer.

        Args:
            config: Konfiguration
        """
        self.config = config or SensitivityAnalyzerConfig()
        self._llm_client: Optional[LLMClient] = None
        self._osl_rules: Optional[dict] = None

    @property
    def llm_client(self) -> LLMClient:
        """Lazy loading av LLM-klient."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self.config.llm_config)
        return self._llm_client

    @property
    def osl_rules(self) -> dict:
        """Lazy loading av OSL-regler."""
        if self._osl_rules is None:
            self._osl_rules = self._load_osl_rules()
        return self._osl_rules

    def _load_osl_rules(self) -> dict:
        """Ladda OSL-regler från JSON-fil."""
        rules_path = self.config.osl_rules_path
        if rules_path is None:
            # Standardsökväg
            rules_path = Path(__file__).parent.parent.parent / "docs" / "OSL_RULES.json"
        else:
            rules_path = Path(rules_path)

        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"OSL-regler inte funna: {rules_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Fel vid parsning av OSL-regler: {e}")
            return {}

    def analyze_section(
        self,
        text: str,
        entities: Optional[list[Entity]] = None,
    ) -> SensitivityAssessment:
        """
        Analysera ett textavsnitt.

        Args:
            text: Textavsnittet att analysera
            entities: Eventuella entiteter i avsnittet

        Returns:
            SensitivityAssessment med bedömning
        """
        # Först: nyckelordsbaserad föranalys
        keyword_result = self._keyword_analysis(text)

        # Om LLM är konfigurerad, använd den för djupare analys
        if self.llm_client.is_configured():
            try:
                llm_result = self._llm_analyze_section(text)
                # Kombinera resultat (LLM har prioritet vid konflikt)
                return self._combine_results(
                    text, keyword_result, llm_result, entities
                )
            except Exception as e:
                logger.warning(f"LLM-analys misslyckades, använder nyckelord: {e}")

        # Fallback till nyckelordsbaserad bedömning
        return self._create_assessment_from_keywords(text, keyword_result, entities)

    def _keyword_analysis(self, text: str) -> dict:
        """
        Analysera text baserat på nyckelord från OSL-regler.

        Args:
            text: Texten att analysera

        Returns:
            Dict med kategorier och träffar
        """
        text_lower = text.lower()
        results = {
            "categories": {},
            "keywords_found": [],
            "highest_level": "LOW",
        }

        categories = self.osl_rules.get("categories", {})

        for cat_name, cat_data in categories.items():
            keywords = cat_data.get("keywords", [])
            found = [kw for kw in keywords if kw.lower() in text_lower]

            if found:
                results["categories"][cat_name] = {
                    "keywords": found,
                    "count": len(found),
                    "default_level": cat_data.get("default_level", "MEDIUM"),
                }
                results["keywords_found"].extend(found)

                # Uppdatera högsta nivå
                level = cat_data.get("default_level", "MEDIUM")
                if self._level_priority(level) > self._level_priority(results["highest_level"]):
                    results["highest_level"] = level

        return results

    def _level_priority(self, level: str) -> int:
        """Returnera prioritet för en känslighetsnivå."""
        priorities = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return priorities.get(level, 0)

    def _llm_analyze_section(self, text: str) -> dict:
        """
        Analysera textavsnitt med LLM.

        Args:
            text: Texten att analysera

        Returns:
            Dict med LLM:s bedömning
        """
        prompt = ANALYZE_SECTION_PROMPT.format(text=text[:self.config.max_section_length])

        response = self.llm_client.chat_json(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SENSITIVITY_SYSTEM_PROMPT,
        )

        return response

    def _combine_results(
        self,
        text: str,
        keyword_result: dict,
        llm_result: dict,
        entities: Optional[list[Entity]],
    ) -> SensitivityAssessment:
        """
        Kombinera resultat från nyckelords- och LLM-analys.

        Args:
            text: Originaltexten
            keyword_result: Resultat från nyckelordsanalys
            llm_result: Resultat från LLM
            entities: Entiteter i texten

        Returns:
            Kombinerad SensitivityAssessment
        """
        # Extrahera LLM-resultat
        primary_category = llm_result.get("primary_category", "NEUTRAL")
        secondary_categories = llm_result.get("secondary_categories", [])
        sensitivity_level = llm_result.get("sensitivity_level", keyword_result["highest_level"])
        recommended_action = llm_result.get("recommended_action", "ASSESS")
        reasons = llm_result.get("reasons", [])
        confidence = llm_result.get("confidence", 0.7)
        legal_basis = llm_result.get("legal_basis", "OSL 26:1")

        # Lägg till nyckelord som inte fanns i LLM-resultatet
        all_keywords = set(llm_result.get("keywords_found", []))
        all_keywords.update(keyword_result.get("keywords_found", []))

        # Om nyckelordsanalys hittade kritisk kategori men LLM inte, höj nivån
        if (
            keyword_result["highest_level"] == "CRITICAL"
            and sensitivity_level not in ("CRITICAL", "HIGH")
        ):
            sensitivity_level = "HIGH"
            reasons.append("Nyckelordsanalys identifierade känsligt innehåll")

        # Skapa bedömning
        return SensitivityAssessment(
            text=text[:500] if len(text) > 500 else text,  # Trunkera för lagring
            start=0,
            end=len(text),
            level=self.LEVEL_MAP.get(sensitivity_level, SensitivityLevel.MEDIUM),
            primary_category=self.CATEGORY_MAP.get(primary_category, SensitivityCategory.NEUTRAL),
            secondary_categories=[
                self.CATEGORY_MAP.get(cat, SensitivityCategory.NEUTRAL)
                for cat in secondary_categories
            ],
            affected_persons=llm_result.get("affected_persons", []),
            reasons=reasons,
            legal_basis=legal_basis,
            recommended_action=self.ACTION_MAP.get(recommended_action, MaskingAction.ASSESS),
            confidence=confidence,
        )

    def _create_assessment_from_keywords(
        self,
        text: str,
        keyword_result: dict,
        entities: Optional[list[Entity]],
    ) -> SensitivityAssessment:
        """
        Skapa bedömning endast baserat på nyckeord.

        Args:
            text: Texten
            keyword_result: Nyckelordsresultat
            entities: Entiteter

        Returns:
            SensitivityAssessment
        """
        categories = keyword_result.get("categories", {})

        # Bestäm primär kategori (den med flest träffar)
        primary_category = "NEUTRAL"
        max_count = 0
        for cat_name, cat_data in categories.items():
            if cat_data["count"] > max_count:
                max_count = cat_data["count"]
                primary_category = cat_name

        # Bestäm rekommenderad åtgärd baserat på nivå
        level = keyword_result["highest_level"]
        if level == "CRITICAL":
            action = "MASK_COMPLETE"
        elif level == "HIGH":
            action = "MASK_COMPLETE"
        elif level == "MEDIUM":
            action = "MASK_PARTIAL"
        else:
            action = "RELEASE"

        reasons = []
        if keyword_result["keywords_found"]:
            reasons.append(
                f"Nyckelord identifierade: {', '.join(keyword_result['keywords_found'][:5])}"
            )

        return SensitivityAssessment(
            text=text[:500] if len(text) > 500 else text,
            start=0,
            end=len(text),
            level=self.LEVEL_MAP.get(level, SensitivityLevel.MEDIUM),
            primary_category=self.CATEGORY_MAP.get(primary_category, SensitivityCategory.NEUTRAL),
            secondary_categories=[
                self.CATEGORY_MAP.get(cat, SensitivityCategory.NEUTRAL)
                for cat in categories.keys()
                if cat != primary_category
            ],
            affected_persons=[],
            reasons=reasons,
            legal_basis="OSL 26:1",
            recommended_action=self.ACTION_MAP.get(action, MaskingAction.ASSESS),
            confidence=0.6 if keyword_result["keywords_found"] else 0.3,
        )

    def identify_role(
        self,
        text: str,
        person_name: str,
    ) -> tuple[PersonRole, float]:
        """
        Identifiera en persons roll i ärendet.

        Args:
            text: Texten som innehåller personen
            person_name: Personens namn

        Returns:
            Tuple med (PersonRole, konfidens)
        """
        # Nyckelordsbaserad föranalys
        role, confidence = self._keyword_role_analysis(text, person_name)

        if confidence >= 0.8:
            return role, confidence

        # LLM-analys om tillgänglig
        if self.llm_client.is_configured():
            try:
                llm_result = self._llm_identify_role(text, person_name)
                llm_role = llm_result.get("identified_role", "UNKNOWN")
                llm_confidence = llm_result.get("confidence", 0.5)

                role_map = {
                    "REQUESTER": PersonRole.REQUESTER,
                    "REQUESTER_CHILD": PersonRole.REQUESTER_CHILD,
                    "SUBJECT": PersonRole.SUBJECT,
                    "REPORTER": PersonRole.REPORTER,
                    "THIRD_PARTY": PersonRole.THIRD_PARTY,
                    "PROFESSIONAL": PersonRole.PROFESSIONAL,
                    "UNKNOWN": PersonRole.UNKNOWN,
                }

                return role_map.get(llm_role, PersonRole.UNKNOWN), llm_confidence

            except Exception as e:
                logger.warning(f"LLM-rollidentifiering misslyckades: {e}")

        return role, confidence

    def _keyword_role_analysis(
        self,
        text: str,
        person_name: str,
    ) -> tuple[PersonRole, float]:
        """
        Identifiera roll baserat på nyckelord.

        Args:
            text: Texten
            person_name: Personens namn

        Returns:
            Tuple med (roll, konfidens)
        """
        text_lower = text.lower()
        name_lower = person_name.lower()

        role_keywords = self.osl_rules.get("role_detection_keywords", {})

        # Kolla om det är en tjänsteman
        professional_keywords = role_keywords.get("professional_roles", [])
        for kw in professional_keywords:
            if kw.lower() in text_lower:
                # Kolla om personnamnet nämns nära nyckelordet
                if self._name_near_keyword(text_lower, name_lower, kw.lower()):
                    return PersonRole.PROFESSIONAL, 0.85

        # Kolla anmälare
        reporter_keywords = role_keywords.get("reporter_indicators", [])
        for kw in reporter_keywords:
            if kw.lower() in text_lower:
                if self._name_near_keyword(text_lower, name_lower, kw.lower()):
                    return PersonRole.REPORTER, 0.75

        # Kolla tredje man (grannar, vänner etc.)
        third_party_keywords = role_keywords.get("third_party_relations", [])
        for kw in third_party_keywords:
            if kw.lower() in text_lower:
                if self._name_near_keyword(text_lower, name_lower, kw.lower()):
                    return PersonRole.THIRD_PARTY, 0.70

        # Kolla familjerelationer
        family_keywords = role_keywords.get("family_relations", [])
        for kw in family_keywords:
            if kw.lower() in text_lower:
                if self._name_near_keyword(text_lower, name_lower, kw.lower()):
                    # Familjemedlem kan vara tredje man eller beställarens barn
                    return PersonRole.THIRD_PARTY, 0.60

        return PersonRole.UNKNOWN, 0.3

    def _name_near_keyword(
        self,
        text: str,
        name: str,
        keyword: str,
        max_distance: int = 100,
    ) -> bool:
        """
        Kontrollera om namn finns nära nyckelord i texten.

        Args:
            text: Texten att söka i
            name: Namnet att hitta
            keyword: Nyckelordet
            max_distance: Max antal tecken mellan

        Returns:
            True om namn och nyckelord är nära varandra
        """
        name_pos = text.find(name)
        kw_pos = text.find(keyword)

        if name_pos == -1 or kw_pos == -1:
            return False

        return abs(name_pos - kw_pos) <= max_distance

    def _llm_identify_role(self, text: str, person_name: str) -> dict:
        """
        Identifiera roll med LLM.

        Args:
            text: Texten
            person_name: Personens namn

        Returns:
            Dict med LLM:s bedömning
        """
        prompt = ROLE_IDENTIFICATION_PROMPT.format(
            text=text[:self.config.max_section_length],
            person_name=person_name,
        )

        return self.llm_client.chat_json(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SENSITIVITY_SYSTEM_PROMPT,
        )

    def get_document_overview(
        self,
        text: str,
        entities: list[Entity],
    ) -> dict:
        """
        Få en översikt av dokumentet.

        Args:
            text: Dokumentets text
            entities: Identifierade entiteter

        Returns:
            Dict med dokumentöversikt
        """
        # Räkna entitetstyper
        from collections import Counter
        type_counts = Counter(e.type.value for e in entities)

        if self.llm_client.is_configured():
            try:
                prompt = DOCUMENT_OVERVIEW_PROMPT.format(
                    text=text[:3000],
                    ssn_count=type_counts.get("SSN", 0),
                    phone_count=type_counts.get("PHONE", 0),
                    email_count=type_counts.get("EMAIL", 0),
                    date_count=type_counts.get("DATE", 0),
                    person_count=type_counts.get("PERSON", 0),
                )

                return self.llm_client.chat_json(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=SENSITIVITY_SYSTEM_PROMPT,
                )
            except Exception as e:
                logger.warning(f"Kunde inte få dokumentöversikt från LLM: {e}")

        # Fallback
        keyword_result = self._keyword_analysis(text)
        return {
            "document_type": "Socialtjänstakt",
            "overall_sensitivity": keyword_result["highest_level"],
            "key_categories": list(keyword_result["categories"].keys()),
            "entity_counts": dict(type_counts),
        }

    def split_into_sections(self, text: str) -> list[str]:
        """
        Dela upp text i analyserbara sektioner.

        Args:
            text: Hela texten

        Returns:
            Lista med textsektioner
        """
        # Dela på dubbla radbrytningar
        paragraphs = re.split(r'\n\s*\n', text)

        sections = []
        current_section = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_section) + len(para) <= self.config.max_section_length:
                current_section += ("\n\n" if current_section else "") + para
            else:
                if current_section:
                    sections.append(current_section)
                current_section = para

        if current_section:
            sections.append(current_section)

        # Filtrera bort för korta sektioner
        return [s for s in sections if len(s) >= self.config.min_section_length]

    def is_configured(self) -> bool:
        """Kontrollera om analyzer är konfigurerad."""
        return bool(self.osl_rules)
