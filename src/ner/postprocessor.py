"""Entity postprocessor för att kombinera och rensa upp NER-resultat.

Kombinerar entiteter från RegexNER och BertNER, hanterar överlapp,
och filtrerar bort falska positiva.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from src.core.models import Entity, EntityType


@dataclass
class PostprocessorConfig:
    """Konfiguration för entity postprocessor."""

    # Prioritetsordning för entitetstyper vid överlapp
    type_priority: list[EntityType] = field(default_factory=lambda: [
        EntityType.SSN,
        EntityType.EMAIL,
        EntityType.PHONE,
        EntityType.PERSON,
        EntityType.ORGANIZATION,
        EntityType.LOCATION,
        EntityType.ADDRESS,
        EntityType.DATE,
        EntityType.MISC,
    ])

    # Minsta konfidens för att behålla entitet
    min_confidence: float = 0.3

    # Filtrera bort entiteter som matchar dessa mönster
    exclude_patterns: list[str] = field(default_factory=lambda: [
        r'^\d{8}\.pdf$',  # Dokumentnummer som ser ut som telefon
        r'^\d+\s*kr$',  # Belopp
        r'^\d{1,2}:\d{2}$',  # Tider
    ])

    # Entiteter som ska filtreras bort
    exclude_texts: set[str] = field(default_factory=lambda: {
        "SDN",  # Stadsdelsnämnd
        "IFO",  # Individ- och familjeomsorg
    })


class EntityPostprocessor:
    """
    Postprocessor för att kombinera och rensa upp NER-resultat.

    Hanterar:
    - Sammanslagning av entiteter från flera NER-system
    - Överlappande entiteter
    - Falska positiva
    - Normalisering av entitetstyper
    """

    def __init__(self, config: Optional[PostprocessorConfig] = None):
        """
        Initiera postprocessor.

        Args:
            config: Konfiguration
        """
        self.config = config or PostprocessorConfig()
        self._exclude_patterns = [
            re.compile(p) for p in self.config.exclude_patterns
        ]

    def process(
        self,
        regex_entities: list[Entity],
        bert_entities: Optional[list[Entity]] = None,
    ) -> list[Entity]:
        """
        Bearbeta och kombinera entiteter från olika NER-källor.

        Args:
            regex_entities: Entiteter från RegexNER
            bert_entities: Entiteter från BertNER (valfritt)

        Returns:
            Lista med bearbetade entiteter
        """
        # Kombinera alla entiteter
        all_entities = list(regex_entities)
        if bert_entities:
            all_entities.extend(bert_entities)

        # Filtrera på konfidens
        entities = [
            e for e in all_entities
            if e.confidence >= self.config.min_confidence
        ]

        # Filtrera bort falska positiva
        entities = self._filter_false_positives(entities)

        # Hantera överlapp
        entities = self._resolve_overlaps(entities)

        # Sortera på position
        entities.sort(key=lambda e: e.start)

        return entities

    def _filter_false_positives(self, entities: list[Entity]) -> list[Entity]:
        """
        Filtrera bort falska positiva.

        Args:
            entities: Lista med entiteter

        Returns:
            Filtrerad lista
        """
        result = []

        for entity in entities:
            # Kolla mot exkluderade texter
            if entity.text.strip() in self.config.exclude_texts:
                continue

            # Kolla mot exkluderade mönster
            if any(p.match(entity.text) for p in self._exclude_patterns):
                continue

            # Filtrera telefonnummer som troligen är dokumentnummer
            if entity.type == EntityType.PHONE:
                if self._looks_like_document_id(entity.text):
                    continue

            result.append(entity)

        return result

    def _looks_like_document_id(self, text: str) -> bool:
        """
        Kontrollera om text ser ut som ett dokumentnummer.

        Args:
            text: Texten att kontrollera

        Returns:
            True om det troligen är ett dokumentnummer
        """
        # Rensa bort formatering
        digits = re.sub(r'[-\s]', '', text)

        # 8-siffriga nummer är ofta dokumentnummer
        if len(digits) == 8 and digits.isdigit():
            # Svenska riktnummer börjar med 0 + specifika siffror
            # Giltiga: 07x (mobil), 08 (Stockholm), 031, 040, etc.
            # 02x, 03x (utom 031), 04x (utom 040), etc. är INTE giltiga riktnummer
            valid_area_prefixes = {'07', '08', '031', '040', '046'}
            starts_with_valid = any(
                digits.startswith(prefix) for prefix in valid_area_prefixes
            )
            if not starts_with_valid:
                return True

        return False

    def _resolve_overlaps(self, entities: list[Entity]) -> list[Entity]:
        """
        Hantera överlappande entiteter.

        Prioriterar:
        1. Entitetstyp enligt type_priority
        2. Längre matchningar
        3. Högre konfidens

        Args:
            entities: Lista med entiteter

        Returns:
            Lista utan överlapp
        """
        if not entities:
            return []

        # Skapa prioritetsmappning
        type_priority_map = {
            t: i for i, t in enumerate(self.config.type_priority)
        }
        default_priority = len(self.config.type_priority)

        # Sorteringsfunktion
        def sort_key(e: Entity) -> tuple:
            type_prio = type_priority_map.get(e.type, default_priority)
            length = -(e.end - e.start)  # Negativ för längre först
            confidence = -e.confidence  # Negativ för högre först
            return (type_prio, length, confidence)

        sorted_entities = sorted(entities, key=sort_key)
        result: list[Entity] = []

        for entity in sorted_entities:
            # Kolla överlapp med redan valda entiteter
            overlaps = False
            for existing in result:
                if self._overlaps(
                    (entity.start, entity.end),
                    (existing.start, existing.end)
                ):
                    overlaps = True
                    break

            if not overlaps:
                result.append(entity)

        return result

    def _overlaps(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> bool:
        """Kontrollera om två positioner överlappar."""
        return not (pos1[1] <= pos2[0] or pos2[1] <= pos1[0])

    def merge_adjacent_persons(self, entities: list[Entity]) -> list[Entity]:
        """
        Slå samman angränsande person-entiteter.

        Hanterar fall där BERT delar upp "Anna Andersson" i två entiteter.

        Args:
            entities: Lista med entiteter

        Returns:
            Lista med sammanslagna entiteter
        """
        result: list[Entity] = []
        person_buffer: list[Entity] = []

        for entity in sorted(entities, key=lambda e: e.start):
            if entity.type == EntityType.PERSON:
                if person_buffer:
                    last = person_buffer[-1]
                    # Kolla om entiteterna är angränsande (max 1 tecken mellanrum)
                    if entity.start - last.end <= 1:
                        person_buffer.append(entity)
                        continue
                    else:
                        # Inte angränsande - spara buffern
                        result.append(self._merge_persons(person_buffer))
                        person_buffer = [entity]
                else:
                    person_buffer = [entity]
            else:
                # Inte PERSON - töm buffern först
                if person_buffer:
                    result.append(self._merge_persons(person_buffer))
                    person_buffer = []
                result.append(entity)

        # Töm eventuell kvarvarande buffer
        if person_buffer:
            result.append(self._merge_persons(person_buffer))

        return result

    def _merge_persons(self, persons: list[Entity]) -> Entity:
        """
        Slå samman en lista med person-entiteter till en.

        Args:
            persons: Lista med person-entiteter

        Returns:
            En sammanslagen entitet
        """
        if len(persons) == 1:
            return persons[0]

        # Kombinera text och positioner
        combined_text = " ".join(p.text for p in persons)
        min_start = min(p.start for p in persons)
        max_end = max(p.end for p in persons)
        avg_confidence = sum(p.confidence for p in persons) / len(persons)

        return Entity(
            text=combined_text,
            type=EntityType.PERSON,
            start=min_start,
            end=max_end,
            confidence=avg_confidence,
        )

    def get_statistics(self, entities: list[Entity]) -> dict:
        """
        Beräkna statistik för entiteter.

        Args:
            entities: Lista med entiteter

        Returns:
            Statistik-dict
        """
        from collections import Counter

        type_counts = Counter(e.type.value for e in entities)
        avg_confidence = (
            sum(e.confidence for e in entities) / len(entities)
            if entities else 0.0
        )

        return {
            "total_entities": len(entities),
            "by_type": dict(type_counts),
            "average_confidence": round(avg_confidence, 3),
            "unique_texts": len(set(e.text for e in entities)),
        }
