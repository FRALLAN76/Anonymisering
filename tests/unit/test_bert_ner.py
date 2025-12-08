"""Enhetstester för BERT-baserad Named Entity Recognition."""

import pytest
from unittest.mock import Mock, patch

from src.ner.bert_ner import BertNER, BertNERConfig
from src.core.models import EntityType


class TestBertNERConfig:
    """Tester för konfiguration."""

    def test_default_config(self):
        """Test: Standardkonfiguration."""
        config = BertNERConfig()

        assert config.model_name == "KB/bert-base-swedish-cased-ner"
        assert config.device == "cpu"
        assert config.batch_size == 8
        assert config.max_length == 512
        assert config.confidence_threshold == 0.5

    def test_custom_config(self):
        """Test: Anpassad konfiguration."""
        config = BertNERConfig(
            model_name="custom/model",
            device="cuda",
            confidence_threshold=0.8,
        )

        assert config.model_name == "custom/model"
        assert config.device == "cuda"
        assert config.confidence_threshold == 0.8


class TestBertNERWithMock:
    """Tester med mockad modell."""

    @pytest.fixture
    def mock_pipeline(self):
        """Skapa en mockad pipeline."""
        mock = Mock()
        mock.return_value = [
            {
                "entity_group": "PER",
                "word": "Anna Andersson",
                "start": 0,
                "end": 14,
                "score": 0.95,
            },
            {
                "entity_group": "LOC",
                "word": "Stockholm",
                "start": 20,
                "end": 29,
                "score": 0.92,
            },
        ]
        return mock

    @pytest.fixture
    def ner_with_mock(self, mock_pipeline):
        """Skapa NER med mockad pipeline."""
        ner = BertNER()
        ner._pipeline = mock_pipeline
        ner._model_loaded = True
        return ner

    def test_extract_entities_person(self, ner_with_mock):
        """Test: Extrahera person-entiteter."""
        text = "Anna Andersson bor i Stockholm"

        entities = ner_with_mock.extract_entities(text)

        person_entities = [e for e in entities if e.type == EntityType.PERSON]
        assert len(person_entities) >= 1
        assert person_entities[0].text == "Anna Andersson"
        assert person_entities[0].confidence >= 0.9

    def test_extract_entities_location(self, ner_with_mock):
        """Test: Extrahera plats-entiteter."""
        text = "Anna Andersson bor i Stockholm"

        entities = ner_with_mock.extract_entities(text)

        location_entities = [e for e in entities if e.type == EntityType.LOCATION]
        assert len(location_entities) >= 1
        assert location_entities[0].text == "Stockholm"

    def test_extract_persons_method(self, ner_with_mock):
        """Test: extract_persons metoden."""
        text = "Anna Andersson bor i Stockholm"

        persons = ner_with_mock.extract_persons(text)

        assert len(persons) >= 1
        assert all(p.type == EntityType.PERSON for p in persons)

    def test_empty_text(self, ner_with_mock):
        """Test: Tom text."""
        entities = ner_with_mock.extract_entities("")
        assert entities == []

        entities = ner_with_mock.extract_entities("   ")
        assert entities == []

    def test_model_info(self, ner_with_mock):
        """Test: Modellinfo."""
        info = ner_with_mock.get_model_info()

        assert "model_name" in info
        assert "loaded" in info
        assert info["loaded"] is True

    def test_is_model_loaded(self, ner_with_mock):
        """Test: Kontrollera om modellen är laddad."""
        assert ner_with_mock.is_model_loaded() is True


class TestBertNERTextSplitting:
    """Tester för textuppdelning."""

    @pytest.fixture
    def ner(self):
        """Skapa NER utan att ladda modellen."""
        ner = BertNER()
        return ner

    def test_split_short_text(self, ner):
        """Test: Kort text delas inte."""
        text = "Detta är en kort text."
        chunks = ner._split_text(text, max_length=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_split_long_text(self, ner):
        """Test: Lång text delas vid lämpliga brytpunkter."""
        text = "Första meningen. Andra meningen. " * 20
        chunks = ner._split_text(text, max_length=100)

        assert len(chunks) > 1
        # Alla chunks ska vara max 100 tecken (eller strax över om ingen bra brytpunkt finns)
        for chunk in chunks:
            assert len(chunk) <= 105

    def test_split_preserves_content(self, ner):
        """Test: Textuppdelning bevarar allt innehåll."""
        text = "En text med flera ord och meningar. " * 10
        chunks = ner._split_text(text, max_length=50)

        # Sammanfoga ska ge tillbaka originalet
        result = "".join(chunks)
        assert result == text


class TestBertNERFiltering:
    """Tester för filtrering av entiteter."""

    @pytest.fixture
    def ner(self):
        """Skapa NER utan att ladda modellen."""
        config = BertNERConfig(confidence_threshold=0.7)
        ner = BertNER(config)
        return ner

    def test_filter_low_confidence(self, ner):
        """Test: Entiteter med låg konfidens filtreras bort."""
        from src.core.models import Entity

        entities = [
            Entity(text="A", type=EntityType.PERSON, start=0, end=1, confidence=0.5),
            Entity(text="B", type=EntityType.PERSON, start=5, end=6, confidence=0.9),
            Entity(text="C", type=EntityType.PERSON, start=10, end=11, confidence=0.6),
        ]

        filtered = ner._filter_entities(entities)

        assert len(filtered) == 1
        assert filtered[0].text == "B"

    def test_filter_overlapping_entities(self, ner):
        """Test: Överlappande entiteter filtreras (behåll högst konfidens)."""
        from src.core.models import Entity

        entities = [
            Entity(text="AB", type=EntityType.PERSON, start=0, end=5, confidence=0.8),
            Entity(text="BC", type=EntityType.PERSON, start=3, end=8, confidence=0.9),
        ]

        filtered = ner._filter_entities(entities)

        # Första tas med (sorterad), andra filtreras pga överlapp
        assert len(filtered) == 1


class TestBertNERLabelMapping:
    """Tester för etikettmappning."""

    def test_label_mapping_exists(self):
        """Test: Alla förväntade etiketter finns."""
        assert "PER" in BertNER.LABEL_MAPPING
        assert "LOC" in BertNER.LABEL_MAPPING
        assert "ORG" in BertNER.LABEL_MAPPING

    def test_label_mapping_correct_types(self):
        """Test: Etiketter mappar till rätt EntityType."""
        assert BertNER.LABEL_MAPPING["PER"] == EntityType.PERSON
        assert BertNER.LABEL_MAPPING["LOC"] == EntityType.LOCATION
        assert BertNER.LABEL_MAPPING["ORG"] == EntityType.ORGANIZATION


class TestBertNEROverlap:
    """Tester för överlappskontroll."""

    @pytest.fixture
    def ner(self):
        return BertNER()

    def test_overlapping_positions(self, ner):
        """Test: Överlappande positioner identifieras."""
        assert ner._overlaps((0, 10), (5, 15)) is True
        assert ner._overlaps((5, 15), (0, 10)) is True

    def test_non_overlapping_positions(self, ner):
        """Test: Icke-överlappande positioner."""
        assert ner._overlaps((0, 5), (5, 10)) is False
        assert ner._overlaps((0, 5), (10, 15)) is False

    def test_containing_positions(self, ner):
        """Test: En position innehåller en annan."""
        assert ner._overlaps((0, 20), (5, 10)) is True
        assert ner._overlaps((5, 10), (0, 20)) is True


# Integration test med riktig modell (markeras som slow)
@pytest.mark.slow
class TestBertNERIntegration:
    """Integrationstester med riktig BERT-modell."""

    @pytest.fixture
    def ner(self):
        """Skapa NER med riktig modell."""
        try:
            return BertNER()
        except ImportError:
            pytest.skip("transformers inte installerat")

    def test_real_model_extract_person(self, ner):
        """Test: Extrahera person med riktig modell."""
        text = "Anna Svensson träffade Erik Johansson i Malmö."

        entities = ner.extract_entities(text)

        person_names = [e.text for e in entities if e.type == EntityType.PERSON]
        # Förvänta minst ett personnamn
        assert len(person_names) >= 1

    def test_real_model_extract_location(self, ner):
        """Test: Extrahera plats med riktig modell."""
        text = "Mötet hölls i Göteborg och Stockholm."

        entities = ner.extract_entities(text)

        locations = [e.text for e in entities if e.type == EntityType.LOCATION]
        # Förvänta minst en plats
        assert len(locations) >= 1
