"""Enhetstester för Entity Postprocessor."""

import pytest

from src.ner.postprocessor import EntityPostprocessor, PostprocessorConfig
from src.core.models import Entity, EntityType


class TestPostprocessorConfig:
    """Tester för konfiguration."""

    def test_default_config(self):
        """Test: Standardkonfiguration."""
        config = PostprocessorConfig()

        assert config.min_confidence == 0.3
        assert EntityType.SSN in config.type_priority
        assert len(config.exclude_patterns) > 0

    def test_custom_config(self):
        """Test: Anpassad konfiguration."""
        config = PostprocessorConfig(
            min_confidence=0.5,
            exclude_texts={"TEST"},
        )

        assert config.min_confidence == 0.5
        assert "TEST" in config.exclude_texts


class TestPostprocessorProcess:
    """Tester för process-metoden."""

    @pytest.fixture
    def processor(self) -> EntityPostprocessor:
        return EntityPostprocessor()

    def test_process_empty_lists(self, processor: EntityPostprocessor):
        """Test: Tomma listor."""
        result = processor.process([], None)
        assert result == []

    def test_process_regex_only(self, processor: EntityPostprocessor):
        """Test: Endast regex-entiteter."""
        entities = [
            Entity(text="199001011234", type=EntityType.SSN, start=0, end=12, confidence=0.99),
            Entity(text="test@example.com", type=EntityType.EMAIL, start=20, end=36, confidence=0.99),
        ]

        result = processor.process(entities, None)

        assert len(result) == 2
        assert result[0].start < result[1].start  # Sorterade

    def test_process_combined_sources(self, processor: EntityPostprocessor):
        """Test: Kombinerade källor (regex + bert)."""
        regex_entities = [
            Entity(text="199001011234", type=EntityType.SSN, start=0, end=12, confidence=0.99),
        ]
        bert_entities = [
            Entity(text="Anna Andersson", type=EntityType.PERSON, start=20, end=34, confidence=0.95),
        ]

        result = processor.process(regex_entities, bert_entities)

        assert len(result) == 2
        types = {e.type for e in result}
        assert EntityType.SSN in types
        assert EntityType.PERSON in types

    def test_filter_low_confidence(self, processor: EntityPostprocessor):
        """Test: Entiteter med låg konfidens filtreras bort."""
        entities = [
            Entity(text="A", type=EntityType.PERSON, start=0, end=1, confidence=0.1),
            Entity(text="B", type=EntityType.PERSON, start=5, end=6, confidence=0.9),
        ]

        result = processor.process(entities, None)

        assert len(result) == 1
        assert result[0].text == "B"


class TestPostprocessorOverlaps:
    """Tester för överlapphantering."""

    @pytest.fixture
    def processor(self) -> EntityPostprocessor:
        return EntityPostprocessor()

    def test_ssn_prioritized_over_phone(self, processor: EntityPostprocessor):
        """Test: SSN prioriteras över telefonnummer."""
        entities = [
            Entity(text="0701234567", type=EntityType.PHONE, start=0, end=10, confidence=0.90),
            Entity(text="0701234567", type=EntityType.SSN, start=0, end=10, confidence=0.70),
        ]

        result = processor.process(entities, None)

        assert len(result) == 1
        assert result[0].type == EntityType.SSN

    def test_longer_match_preferred(self, processor: EntityPostprocessor):
        """Test: Längre matchning föredras."""
        entities = [
            Entity(text="Anna", type=EntityType.PERSON, start=0, end=4, confidence=0.9),
            Entity(text="Anna Andersson", type=EntityType.PERSON, start=0, end=14, confidence=0.8),
        ]

        result = processor.process(entities, None)

        assert len(result) == 1
        assert result[0].text == "Anna Andersson"

    def test_non_overlapping_preserved(self, processor: EntityPostprocessor):
        """Test: Icke-överlappande bevaras."""
        entities = [
            Entity(text="A", type=EntityType.PERSON, start=0, end=1, confidence=0.9),
            Entity(text="B", type=EntityType.PERSON, start=10, end=11, confidence=0.9),
        ]

        result = processor.process(entities, None)

        assert len(result) == 2


class TestPostprocessorFalsePositives:
    """Tester för falska positiva."""

    @pytest.fixture
    def processor(self) -> EntityPostprocessor:
        return EntityPostprocessor()

    def test_filter_document_ids(self, processor: EntityPostprocessor):
        """Test: Dokumentnummer filtreras bort."""
        entities = [
            Entity(text="02030355", type=EntityType.PHONE, start=0, end=8, confidence=0.90),
        ]

        result = processor.process(entities, None)

        assert len(result) == 0  # Filtrerat som dokumentnummer

    def test_filter_excluded_texts(self, processor: EntityPostprocessor):
        """Test: Exkluderade texter filtreras bort."""
        entities = [
            Entity(text="SDN", type=EntityType.ORGANIZATION, start=0, end=3, confidence=0.9),
            Entity(text="IFO", type=EntityType.ORGANIZATION, start=5, end=8, confidence=0.9),
        ]

        result = processor.process(entities, None)

        assert len(result) == 0

    def test_valid_phone_not_filtered(self, processor: EntityPostprocessor):
        """Test: Giltiga telefonnummer filtreras inte."""
        entities = [
            Entity(text="070-123 45 67", type=EntityType.PHONE, start=0, end=13, confidence=0.90),
        ]

        result = processor.process(entities, None)

        assert len(result) == 1

    def test_looks_like_document_id(self, processor: EntityPostprocessor):
        """Test: _looks_like_document_id."""
        assert processor._looks_like_document_id("02030355") is True  # Ej giltigt riktnummer
        assert processor._looks_like_document_id("12345678") is True  # Börjar inte med 0
        assert processor._looks_like_document_id("01234567") is True  # Ej giltigt riktnummer
        assert processor._looks_like_document_id("07012345") is False  # 07 = mobil
        assert processor._looks_like_document_id("08123456") is False  # 08 = Stockholm
        assert processor._looks_like_document_id("070-123 45 67") is False  # Format med bindestreck


class TestPostprocessorMergePersons:
    """Tester för sammanslagning av person-entiteter."""

    @pytest.fixture
    def processor(self) -> EntityPostprocessor:
        return EntityPostprocessor()

    def test_merge_adjacent_persons(self, processor: EntityPostprocessor):
        """Test: Angränsande personnamn slås samman."""
        entities = [
            Entity(text="Anna", type=EntityType.PERSON, start=0, end=4, confidence=0.9),
            Entity(text="Andersson", type=EntityType.PERSON, start=5, end=14, confidence=0.9),
        ]

        result = processor.merge_adjacent_persons(entities)

        assert len(result) == 1
        assert "Anna" in result[0].text
        assert "Andersson" in result[0].text

    def test_non_adjacent_not_merged(self, processor: EntityPostprocessor):
        """Test: Icke-angränsande slås inte samman."""
        entities = [
            Entity(text="Anna", type=EntityType.PERSON, start=0, end=4, confidence=0.9),
            Entity(text="Erik", type=EntityType.PERSON, start=20, end=24, confidence=0.9),
        ]

        result = processor.merge_adjacent_persons(entities)

        assert len(result) == 2

    def test_preserve_other_types(self, processor: EntityPostprocessor):
        """Test: Andra entitetstyper bevaras."""
        entities = [
            Entity(text="Anna", type=EntityType.PERSON, start=0, end=4, confidence=0.9),
            Entity(text="Stockholm", type=EntityType.LOCATION, start=10, end=19, confidence=0.9),
            Entity(text="Erik", type=EntityType.PERSON, start=25, end=29, confidence=0.9),
        ]

        result = processor.merge_adjacent_persons(entities)

        assert len(result) == 3
        types = [e.type for e in result]
        assert EntityType.LOCATION in types


class TestPostprocessorStatistics:
    """Tester för statistik."""

    @pytest.fixture
    def processor(self) -> EntityPostprocessor:
        return EntityPostprocessor()

    def test_statistics_empty(self, processor: EntityPostprocessor):
        """Test: Statistik för tom lista."""
        stats = processor.get_statistics([])

        assert stats["total_entities"] == 0
        assert stats["average_confidence"] == 0.0

    def test_statistics_with_entities(self, processor: EntityPostprocessor):
        """Test: Statistik med entiteter."""
        entities = [
            Entity(text="A", type=EntityType.PERSON, start=0, end=1, confidence=0.8),
            Entity(text="B", type=EntityType.PERSON, start=5, end=6, confidence=0.9),
            Entity(text="C", type=EntityType.LOCATION, start=10, end=11, confidence=1.0),
        ]

        stats = processor.get_statistics(entities)

        assert stats["total_entities"] == 3
        assert stats["by_type"]["PERSON"] == 2
        assert stats["by_type"]["LOCATION"] == 1
        assert stats["average_confidence"] == 0.9
        assert stats["unique_texts"] == 3


class TestPostprocessorRealWorld:
    """Tester med verkliga exempel."""

    @pytest.fixture
    def processor(self) -> EntityPostprocessor:
        return EntityPostprocessor()

    def test_social_services_document(self, processor: EntityPostprocessor):
        """Test: Typiskt socialtjänstdokument."""
        regex_entities = [
            Entity(text="18561225-1234", type=EntityType.SSN, start=0, end=13, confidence=0.99),
            Entity(text="070-123 45 67", type=EntityType.PHONE, start=20, end=33, confidence=0.90),
            Entity(text="2025-01-15", type=EntityType.DATE, start=40, end=50, confidence=0.95),
        ]
        bert_entities = [
            Entity(text="Anna Andersson", type=EntityType.PERSON, start=55, end=69, confidence=0.95),
            Entity(text="Göteborg", type=EntityType.LOCATION, start=75, end=83, confidence=0.92),
        ]

        result = processor.process(regex_entities, bert_entities)

        assert len(result) == 5
        types = {e.type for e in result}
        assert EntityType.SSN in types
        assert EntityType.PHONE in types
        assert EntityType.DATE in types
        assert EntityType.PERSON in types
        assert EntityType.LOCATION in types

    def test_document_id_filtered(self, processor: EntityPostprocessor):
        """Test: Dokumentnummer från filnamn filtreras."""
        entities = [
            Entity(text="02030355", type=EntityType.PHONE, start=0, end=8, confidence=0.90),
            Entity(text="02050124", type=EntityType.PHONE, start=20, end=28, confidence=0.90),
            Entity(text="070-123 45 67", type=EntityType.PHONE, start=40, end=53, confidence=0.90),
        ]

        result = processor.process(entities, None)

        # Endast det riktiga telefonnumret ska finnas kvar
        assert len(result) == 1
        assert "070" in result[0].text
