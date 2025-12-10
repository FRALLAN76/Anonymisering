"""Entity postprocessor för att kombinera och rensa upp NER-resultat.

Kombinerar entiteter från RegexNER och BertNER, hanterar överlapp,
och filtrerar bort falska positiva.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

from src.core.models import Entity, EntityType
from src.llm.client import LLMClient, LLMConfig

logger = logging.getLogger(__name__)


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
        self._llm_client: Optional[LLMClient] = None

    @property
    def llm_client(self) -> LLMClient:
        """Lazy loading av LLM-klient."""
        if self._llm_client is None:
            self._llm_client = LLMClient(LLMConfig())
        return self._llm_client

    def process(
        self,
        regex_entities: list[Entity],
        bert_entities: Optional[list[Entity]] = None,
        text: Optional[str] = None,
        llm_config: Optional[LLMConfig] = None,
    ) -> list[Entity]:
        """
        Bearbeta och kombinera entiteter från olika NER-källor.

        Args:
            regex_entities: Entiteter från RegexNER
            bert_entities: Entiteter från BertNER (valfritt)
            text: Hela texten (för LLM-baserad analys)
            llm_config: LLM-konfiguration för avancerad analys

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

        # Cache för LLM-analys
        self._existing_entities_cache = entities

        # LLM-baserad namnigenkänning (om konfigurerad)
        if text and llm_config and self.llm_client.is_configured():
            llm_entities = self.detect_missed_names_with_llm(text, entities, llm_config)
            if llm_entities:
                # Kombinera och hantera överlapp igen
                all_entities = entities + llm_entities
                entities = self._resolve_overlaps(all_entities)
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

    def expand_person_entities(
        self,
        text: str,
        entities: list[Entity],
    ) -> list[Entity]:
        """
        Hitta ALLA förekomster av identifierade personnamn i texten.

        NER kan missa vissa förekomster av samma namn. Denna metod:
        1. Samlar alla unika personnamn som hittats
        2. Söker globalt efter alla förekomster (case-insensitive)
        3. Hanterar böjningsformer (genitiv: Fredriks, Sveinungs)

        Args:
            text: Hela texten
            entities: Befintliga entiteter

        Returns:
            Utökad lista med entiteter
        """
        # Samla unika personnamn (minst 3 tecken)
        person_names: set[str] = set()
        for e in entities:
            if e.type == EntityType.PERSON and len(e.text) >= 3:
                # Lägg till grundformen
                name = e.text.strip()
                # Hoppa över fragmenterade tokens (##, korta)
                if name.startswith('##') or len(name) < 3:
                    continue
                person_names.add(name)

        if not person_names:
            return entities

        # Skapa positionsset för befintliga entiteter
        existing_positions: set[tuple[int, int]] = {
            (e.start, e.end) for e in entities
        }

        new_entities: list[Entity] = []

        for name in person_names:
            # Skapa mönster för namn och dess böjningsformer
            # Matcha: "Sveinung", "Sveinungs", "Sveinung's", "SVEINUNG"
            escaped_name = re.escape(name)
            pattern = re.compile(
                rf'\b({escaped_name})(s|\'s|´s)?\b',
                re.IGNORECASE
            )

            for match in pattern.finditer(text):
                pos = (match.start(), match.end())

                # Hoppa över om redan täckt av befintlig entitet
                if any(self._overlaps(pos, existing) for existing in existing_positions):
                    continue

                # Lägg till ny entitet
                new_entities.append(Entity(
                    text=match.group(0),
                    type=EntityType.PERSON,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85,  # Hög konfidens - vi vet att namnet är korrekt
                ))
                existing_positions.add(pos)

        # Kombinera och sortera
        all_entities = list(entities) + new_entities
        all_entities.sort(key=lambda e: e.start)

        return all_entities

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

    def detect_missed_names_with_llm(
        self,
        text: str,
        existing_entities: list[Entity],
        llm_config: Optional[LLMConfig] = None,
    ) -> list[Entity]:
        """
        Använd LLM för att hitta namn som NER missat genom kontextanalys.

        Denna metod analyserar texten och hittar namn som:
        - Förekommer i kontext där personnamn förväntas
        - Har stor begynnelsebokstav och följer svenska namnkonventioner
        - Nämns tillsammans med andra identifierade personer
        - Förekommer i meningar om familjerelationer

        Args:
            text: Hela texten att analysera
            existing_entities: Befintliga entiteter från NER
            llm_config: LLM-konfiguration (valfritt)

        Returns:
            Lista med nya person-entiteter som hittats
        """
        if not llm_config or not self.llm_client.is_configured():
            logger.info("LLM inte konfigurerad - hoppar över kontextbaserad namnigenkänning")
            return []

        try:
            # Skapa prompt för LLM-analys
            prompt = self._create_name_detection_prompt(text, existing_entities)

            # Anropa LLM
            result = self.llm_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self._get_name_detection_system_prompt(),
            )

            # Parsa resultat och skapa entiteter
            return self._parse_llm_name_detection_result(result, text, existing_entities)

        except Exception as e:
            logger.warning(f"LLM-baserad namnigenkänning misslyckades: {e}")
            return []

    def _create_name_detection_prompt(
        self,
        text: str,
        existing_entities: list[Entity],
    ) -> str:
        """Skapa prompt för LLM-baserad namnigenkänning."""
        
        # Samla befintliga personnamn
        existing_names = set()
        for entity in existing_entities:
            if entity.type == EntityType.PERSON:
                existing_names.add(entity.text)

        # Skapa prompt
        prompt = f"""
Analysera följande text och identifiera ALLA personnamn som inte redan har hittats av NER-systemet.

**Text att analysera:**
{text[:2000]}...  # (texten är avkortad för analys)

**Personnamn som redan hittats:**
{', '.join(sorted(existing_names)) if existing_names else 'Inga namn hittats än'}

**Instruktioner:**
1. Läs texten noggrant och identifiera ALLA personnamn
2. Fokusera på namn som:
   - Har stor begynnelsebokstav
   - Förekommer i kontext där personer nämns
   - Följer svenska namnkonventioner
   - Nämns tillsammans med andra personer
   - Förekommer i familjerelaterade meningar
3. Ignorera vanliga substantiv, organisationer och platser
4. Var särskilt uppmärksam på ovanliga namn som kan ha missats

**Exempel på namn som kan ha missats:**
- "Sveinung" i "Sveinung och Anna kallade till möte"
- "Eskil" i "Eskil berättade om situationen"
- "Folke" i "Folke och hans familj"

**Svara med JSON i formatet:**
{{
  "missed_names": [
    {{
      "name": "Namn Hittat",
      "reason": "Varför detta troligen är ett personnamn",
      "context": "Relevant textkontext"
    }}
  ]
}}

**Viktigt:** Var mycket noggrann och inkludera även ovanliga namn!
"""
        
        return prompt

    def _get_name_detection_system_prompt(self) -> str:
        """Systemprompt för namnigenkänning."""
        return """
Du är en expert på svensk namngivning och textanalys. Din uppgift är att identifiera personnamn i svenska texter som NER-system kan ha missat.

Du har djup kunskap om:
- Svenska namnkonventioner (förnamn, efternamn, sammansatta namn)
- Ovanliga och äldre svenska namn
- Namn från olika kulturer som förekommer i Sverige
- Hur namn används i sociala sammanhang

Var särskilt uppmärksam på:
1. Ovanliga namn som "Sveinung", "Eskil", "Folke"
2. Namn i genitivform ("Sveinungs situation")
3. Namn som följer efter titlar eller i listor
4. Namn i citat och dialog

Ge alltid välmotiverade svar och inkludera kontext!
"""

    def _parse_llm_name_detection_result(
        self,
        result: dict,
        text: str,
        existing_entities: list[Entity],
    ) -> list[Entity]:
        """Parsa LLM-resultat till entiteter."""
        new_entities = []
        existing_positions = set((e.start, e.end) for e in existing_entities)

        for name_data in result.get("missed_names", []):
            name = name_data.get("name", "")
            if not name or len(name) < 2:
                continue

            # Sök efter namnet i texten (case-insensitive)
            pattern = re.compile(rf'\b({re.escape(name)})\b', re.IGNORECASE)
            
            for match in pattern.finditer(text):
                pos = (match.start(), match.end())
                
                # Hoppa över om redan täckt
                if any(self._overlaps(pos, existing) for existing in existing_positions):
                    continue

                new_entities.append(Entity(
                    text=match.group(1),
                    type=EntityType.PERSON,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.90,  # Hög konfidens från LLM
                ))
                existing_positions.add(pos)

        return new_entities
