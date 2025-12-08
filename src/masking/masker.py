"""Maskeringsmodul for att anonymisera kanslig information.

Applicerar maskning baserat pa entitetstyp, roll och kanslighetsniva.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.core.models import (
    Entity,
    EntityType,
    MaskingAction,
    PersonRole,
    SensitivityAssessment,
    SensitivityLevel,
)


class MaskingStyle(str, Enum):
    """Stil for maskning."""

    BRACKETS = "brackets"  # [MASKERAT]
    REDACTED = "redacted"  # ████████
    PLACEHOLDER = "placeholder"  # <PERSON>, <SSN>
    ANONYMIZED = "anonymized"  # Person A, Person B


@dataclass
class MaskingConfig:
    """Konfiguration for maskning."""

    style: MaskingStyle = MaskingStyle.BRACKETS
    show_entity_type: bool = True  # [MASKERAT: PERSON] vs [MASKERAT]
    preserve_length: bool = False  # Behall ursprunglig langd
    anonymize_persons: bool = True  # Anonymisera till Person A, B, etc.

    # Standardatgarder per entitetstyp
    default_actions: dict = field(default_factory=lambda: {
        EntityType.SSN: MaskingAction.MASK_COMPLETE,
        EntityType.PHONE: MaskingAction.MASK_COMPLETE,
        EntityType.EMAIL: MaskingAction.MASK_COMPLETE,
        EntityType.PERSON: MaskingAction.ASSESS,
        EntityType.ADDRESS: MaskingAction.MASK_COMPLETE,
        EntityType.ORGANIZATION: MaskingAction.RELEASE,
        EntityType.LOCATION: MaskingAction.RELEASE,
        EntityType.DATE: MaskingAction.RELEASE,
        EntityType.MISC: MaskingAction.ASSESS,
    })


@dataclass
class MaskingResult:
    """Resultat fran maskning."""

    original_text: str
    masked_text: str
    masked_entities: list[dict] = field(default_factory=list)
    released_entities: list[dict] = field(default_factory=list)
    statistics: dict = field(default_factory=dict)


class EntityMasker:
    """
    Maskerar entiteter i text baserat pa konfiguration och regler.

    Hanterar:
    - Olika maskeringsstilar
    - Rollbaserad maskning
    - Kanslighetsbaserad maskning
    - Anonymisering av personnamn
    """

    def __init__(self, config: Optional[MaskingConfig] = None):
        """
        Initiera masker.

        Args:
            config: Konfiguration for maskning
        """
        self.config = config or MaskingConfig()
        self._person_map: dict[str, str] = {}
        self._person_counter = 0

    def mask_text(
        self,
        text: str,
        entities: list[Entity],
        assessments: Optional[list[SensitivityAssessment]] = None,
        requester_entities: Optional[set[str]] = None,
    ) -> MaskingResult:
        """
        Maskera text baserat pa entiteter och bedomningar.

        Args:
            text: Texten att maskera
            entities: Lista med entiteter att bearbeta
            assessments: Kanslighetsbedlmningar for sektioner
            requester_entities: Entiteter som tillhor bestallaren (ska inte maskeras)

        Returns:
            MaskingResult med maskerad text och statistik
        """
        requester_entities = requester_entities or set()

        # Sortera entiteter efter position (bakifran for att bevara positioner)
        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

        masked_text = text
        masked_entities = []
        released_entities = []

        for entity in sorted_entities:
            action = self._determine_action(entity, assessments, requester_entities)

            if action == MaskingAction.RELEASE:
                released_entities.append({
                    "text": entity.text,
                    "type": entity.type.value,
                    "reason": "Released",
                })
                continue

            if action in (MaskingAction.MASK_COMPLETE, MaskingAction.MASK_PARTIAL):
                replacement = self._create_replacement(entity, action)
                masked_text = (
                    masked_text[:entity.start] +
                    replacement +
                    masked_text[entity.end:]
                )
                masked_entities.append({
                    "original": entity.text,
                    "replacement": replacement,
                    "type": entity.type.value,
                    "action": action.value,
                    "start": entity.start,
                    "end": entity.end,
                })

        # Skapa statistik
        statistics = self._calculate_statistics(masked_entities, released_entities)

        return MaskingResult(
            original_text=text,
            masked_text=masked_text,
            masked_entities=masked_entities,
            released_entities=released_entities,
            statistics=statistics,
        )

    def _determine_action(
        self,
        entity: Entity,
        assessments: Optional[list[SensitivityAssessment]],
        requester_entities: set[str],
    ) -> MaskingAction:
        """
        Bestam vilken atgard som ska vidtas for en entitet.

        Args:
            entity: Entiteten att bedomma
            assessments: Kanslighetsbedlmningar
            requester_entities: Bestellarens entiteter

        Returns:
            MaskingAction
        """
        # Bestallaren far se sina egna uppgifter
        if entity.text in requester_entities:
            return MaskingAction.RELEASE

        # Personnummer maskas alltid
        if entity.type == EntityType.SSN:
            return MaskingAction.MASK_COMPLETE

        # Kontrollera roll
        if entity.role:
            if entity.role == PersonRole.REQUESTER:
                return MaskingAction.RELEASE
            elif entity.role == PersonRole.PROFESSIONAL:
                # Tjansteman: namn OK, personnummer maskeras
                if entity.type == EntityType.SSN:
                    return MaskingAction.MASK_COMPLETE
                return MaskingAction.RELEASE
            elif entity.role in (PersonRole.REPORTER, PersonRole.THIRD_PARTY):
                return MaskingAction.MASK_COMPLETE

        # Kontrollera kanslighetsniva fran sektionens bedomning
        if assessments:
            for assessment in assessments:
                if self._entity_in_assessment(entity, assessment):
                    if assessment.level in (SensitivityLevel.CRITICAL, SensitivityLevel.HIGH):
                        return MaskingAction.MASK_COMPLETE
                    elif assessment.level == SensitivityLevel.MEDIUM:
                        return MaskingAction.MASK_PARTIAL

        # Standardatgard baserat pa entitetstyp
        return self.config.default_actions.get(entity.type, MaskingAction.ASSESS)

    def _entity_in_assessment(
        self,
        entity: Entity,
        assessment: SensitivityAssessment,
    ) -> bool:
        """Kontrollera om entitet ar inom en bedomnings omfang."""
        return (
            entity.start >= assessment.start and
            entity.end <= assessment.end
        )

    def _create_replacement(
        self,
        entity: Entity,
        action: MaskingAction,
    ) -> str:
        """
        Skapa ersattningstext for en entitet.

        Args:
            entity: Entiteten att ersatta
            action: Maskeringsatgard

        Returns:
            Ersattningstext
        """
        if self.config.style == MaskingStyle.BRACKETS:
            return self._create_bracket_replacement(entity, action)
        elif self.config.style == MaskingStyle.REDACTED:
            return self._create_redacted_replacement(entity)
        elif self.config.style == MaskingStyle.PLACEHOLDER:
            return self._create_placeholder_replacement(entity)
        elif self.config.style == MaskingStyle.ANONYMIZED:
            return self._create_anonymized_replacement(entity)
        else:
            return "[MASKERAT]"

    def _create_bracket_replacement(
        self,
        entity: Entity,
        action: MaskingAction,
    ) -> str:
        """Skapa [MASKERAT: TYP] ersattning."""
        if action == MaskingAction.MASK_PARTIAL:
            # Partiell maskning: visa forsta/sista tecken
            text = entity.text
            if len(text) > 4:
                return f"{text[0]}***{text[-1]}"
            else:
                return "***"

        if self.config.show_entity_type:
            type_names = {
                EntityType.SSN: "PERSONNUMMER",
                EntityType.PHONE: "TELEFON",
                EntityType.EMAIL: "E-POST",
                EntityType.PERSON: "PERSON",
                EntityType.ADDRESS: "ADRESS",
                EntityType.ORGANIZATION: "ORGANISATION",
                EntityType.LOCATION: "PLATS",
                EntityType.DATE: "DATUM",
            }
            type_name = type_names.get(entity.type, "UPPGIFT")
            return f"[MASKERAT: {type_name}]"
        else:
            return "[MASKERAT]"

    def _create_redacted_replacement(self, entity: Entity) -> str:
        """Skapa ████ ersattning."""
        if self.config.preserve_length:
            return "█" * len(entity.text)
        else:
            return "████████"

    def _create_placeholder_replacement(self, entity: Entity) -> str:
        """Skapa <TYP> ersattning."""
        type_tags = {
            EntityType.SSN: "<PERSONNUMMER>",
            EntityType.PHONE: "<TELEFON>",
            EntityType.EMAIL: "<E-POST>",
            EntityType.PERSON: "<PERSON>",
            EntityType.ADDRESS: "<ADRESS>",
        }
        return type_tags.get(entity.type, "<MASKERAT>")

    def _create_anonymized_replacement(self, entity: Entity) -> str:
        """Skapa anonymiserad ersattning (Person A, B, etc.)."""
        if entity.type == EntityType.PERSON:
            if entity.text not in self._person_map:
                self._person_counter += 1
                letter = chr(64 + self._person_counter)  # A, B, C...
                if self._person_counter > 26:
                    letter = f"Person {self._person_counter}"
                else:
                    letter = f"Person {letter}"
                self._person_map[entity.text] = letter
            return self._person_map[entity.text]
        else:
            return self._create_bracket_replacement(entity, MaskingAction.MASK_COMPLETE)

    def _calculate_statistics(
        self,
        masked: list[dict],
        released: list[dict],
    ) -> dict:
        """Berakna statistik over maskningen."""
        from collections import Counter

        masked_types = Counter(e["type"] for e in masked)
        released_types = Counter(e["type"] for e in released)

        return {
            "total_entities": len(masked) + len(released),
            "masked_count": len(masked),
            "released_count": len(released),
            "masked_by_type": dict(masked_types),
            "released_by_type": dict(released_types),
            "masking_ratio": len(masked) / max(len(masked) + len(released), 1),
        }

    def reset_person_mapping(self) -> None:
        """Aterstall personmappning (for nytt dokument)."""
        self._person_map = {}
        self._person_counter = 0


class SectionMasker:
    """
    Maskerar hela sektioner baserat pa kanslighetsniva.

    Anvands nar LLM rekommenderar att hela sektioner ska maskeras.
    """

    def __init__(self, config: Optional[MaskingConfig] = None):
        """Initiera sektionsmaskerare."""
        self.config = config or MaskingConfig()

    def mask_section(
        self,
        text: str,
        assessment: SensitivityAssessment,
    ) -> str:
        """
        Maskera en hel sektion baserat pa bedomning.

        Args:
            text: Texten att maskera
            assessment: Kanslighetsbedlmning

        Returns:
            Maskerad text
        """
        if assessment.recommended_action == MaskingAction.RELEASE:
            return text

        if assessment.recommended_action == MaskingAction.MASK_COMPLETE:
            category_name = assessment.primary_category.value
            return f"[SEKTION MASKERAD: {category_name} - {assessment.legal_basis}]"

        if assessment.recommended_action == MaskingAction.MASK_PARTIAL:
            # Behall forsta meningen, maskera resten
            sentences = re.split(r'(?<=[.!?])\s+', text)
            if len(sentences) > 1:
                first_sentence = sentences[0]
                return f"{first_sentence} [RESTERANDE TEXT MASKERAD]"

        return text

    def mask_sections(
        self,
        sections: list[str],
        assessments: list[SensitivityAssessment],
    ) -> list[str]:
        """
        Maskera flera sektioner.

        Args:
            sections: Lista med textsektioner
            assessments: Bedomningar for varje sektion

        Returns:
            Lista med maskerade sektioner
        """
        masked_sections = []

        for i, section in enumerate(sections):
            if i < len(assessments):
                masked = self.mask_section(section, assessments[i])
            else:
                masked = section
            masked_sections.append(masked)

        return masked_sections
