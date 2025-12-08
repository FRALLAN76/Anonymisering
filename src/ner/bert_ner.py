"""BERT-baserad Named Entity Recognition för svenska texter.

Använder KB-BERT från KBLab för att identifiera:
- PERSON (namn)
- LOCATION (platser)
- ORGANIZATION (organisationer)
"""

import logging
from dataclasses import dataclass
from typing import Optional

from src.core.models import Entity, EntityType

logger = logging.getLogger(__name__)


@dataclass
class BertNERConfig:
    """Konfiguration för BERT-baserad NER."""

    model_name: str = "KB/bert-base-swedish-cased-ner"
    device: str = "cpu"  # "cpu" eller "cuda"
    batch_size: int = 8
    max_length: int = 512
    confidence_threshold: float = 0.5
    aggregate_strategy: str = "simple"  # "none", "simple", "first", "average", "max"


class BertNER:
    """
    BERT-baserad NER för svenska texter.

    Använder KB-BERT NER-modell för att identifiera namngivna entiteter
    som PERSON, LOCATION och ORGANIZATION.
    """

    # Mappning från BERT-etiketter till våra EntityType
    LABEL_MAPPING = {
        "PER": EntityType.PERSON,
        "LOC": EntityType.LOCATION,
        "ORG": EntityType.ORGANIZATION,
        "MISC": EntityType.MISC,
    }

    def __init__(self, config: Optional[BertNERConfig] = None):
        """
        Initiera BertNER.

        Args:
            config: Konfiguration för NER
        """
        self.config = config or BertNERConfig()
        self._pipeline = None
        self._model_loaded = False

    def _load_model(self) -> None:
        """Ladda BERT-modellen vid första användning (lazy loading)."""
        if self._model_loaded:
            return

        try:
            from transformers import pipeline

            logger.info(f"Laddar NER-modell: {self.config.model_name}")

            self._pipeline = pipeline(
                "ner",
                model=self.config.model_name,
                device=0 if self.config.device == "cuda" else -1,
                aggregation_strategy=self.config.aggregate_strategy,
            )

            self._model_loaded = True
            logger.info("NER-modell laddad")

        except ImportError:
            raise ImportError(
                "transformers krävs för BERT NER. "
                "Installera med: pip install transformers torch"
            )
        except Exception as e:
            logger.error(f"Kunde inte ladda NER-modell: {e}")
            raise

    def extract_entities(self, text: str) -> list[Entity]:
        """
        Extrahera namngivna entiteter från text.

        Args:
            text: Texten att analysera

        Returns:
            Lista med identifierade entiteter
        """
        self._load_model()

        if not text.strip():
            return []

        entities: list[Entity] = []

        # Dela upp lång text i chunks
        chunks = self._split_text(text, self.config.max_length)

        offset = 0
        for chunk in chunks:
            chunk_entities = self._process_chunk(chunk, offset)
            entities.extend(chunk_entities)
            offset += len(chunk)

        # Filtrera på konfidens och ta bort duplicat
        entities = self._filter_entities(entities)

        return entities

    def _split_text(self, text: str, max_length: int) -> list[str]:
        """
        Dela upp text i hanterbara chunks.

        Args:
            text: Texten att dela upp
            max_length: Max längd per chunk

        Returns:
            Lista med textchunks
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # Försök hitta en bra brytpunkt (rad eller mening)
            end_pos = min(current_pos + max_length, len(text))

            if end_pos < len(text):
                # Hitta senaste radbrytning eller punkt
                break_pos = text.rfind('\n', current_pos, end_pos)
                if break_pos == -1 or break_pos <= current_pos:
                    break_pos = text.rfind('. ', current_pos, end_pos)
                if break_pos == -1 or break_pos <= current_pos:
                    break_pos = text.rfind(' ', current_pos, end_pos)
                if break_pos > current_pos:
                    end_pos = break_pos + 1

            chunks.append(text[current_pos:end_pos])
            current_pos = end_pos

        return chunks

    def _process_chunk(self, chunk: str, offset: int) -> list[Entity]:
        """
        Bearbeta en textchunk och extrahera entiteter.

        Args:
            chunk: Textchunken att bearbeta
            offset: Offset i originaltexten

        Returns:
            Lista med entiteter
        """
        try:
            results = self._pipeline(chunk)
        except Exception as e:
            logger.warning(f"Fel vid bearbetning av chunk: {e}")
            return []

        entities = []
        for result in results:
            # Extrahera entity-typ (ta bort B-/I- prefix om det finns)
            entity_group = result.get("entity_group", result.get("entity", ""))
            if entity_group.startswith(("B-", "I-")):
                entity_group = entity_group[2:]

            # Mappa till vår EntityType
            entity_type = self.LABEL_MAPPING.get(entity_group)
            if entity_type is None:
                continue

            # Beräkna positioner med offset
            start = result.get("start", 0) + offset
            end = result.get("end", 0) + offset

            entities.append(Entity(
                text=result.get("word", ""),
                type=entity_type,
                start=start,
                end=end,
                confidence=result.get("score", 0.0),
            ))

        return entities

    def _filter_entities(self, entities: list[Entity]) -> list[Entity]:
        """
        Filtrera entiteter på konfidens och ta bort duplicat.

        Args:
            entities: Lista med entiteter

        Returns:
            Filtrerad lista
        """
        # Filtrera på konfidens
        filtered = [
            e for e in entities
            if e.confidence >= self.config.confidence_threshold
        ]

        # Sortera på position
        filtered.sort(key=lambda e: e.start)

        # Ta bort överlappande entiteter (behåll den med högst konfidens)
        result: list[Entity] = []
        for entity in filtered:
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

    def extract_persons(self, text: str) -> list[Entity]:
        """
        Extrahera endast personnamn.

        Args:
            text: Texten att analysera

        Returns:
            Lista med person-entiteter
        """
        entities = self.extract_entities(text)
        return [e for e in entities if e.type == EntityType.PERSON]

    def is_model_loaded(self) -> bool:
        """Kontrollera om modellen är laddad."""
        return self._model_loaded

    def get_model_info(self) -> dict:
        """Hämta information om modellen."""
        return {
            "model_name": self.config.model_name,
            "loaded": self._model_loaded,
            "device": self.config.device,
            "confidence_threshold": self.config.confidence_threshold,
        }
