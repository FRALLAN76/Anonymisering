"""Enhetstester for maskeringsmodul."""

import pytest

from src.masking.masker import (
    EntityMasker,
    SectionMasker,
    MaskingConfig,
    MaskingStyle,
)
from src.core.models import (
    Entity,
    EntityType,
    MaskingAction,
    PersonRole,
    SensitivityAssessment,
    SensitivityCategory,
    SensitivityLevel,
)


class TestMaskingConfig:
    """Tester for konfiguration."""

    def test_default_config(self):
        """Test: Standardkonfiguration."""
        config = MaskingConfig()

        assert config.style == MaskingStyle.BRACKETS
        assert config.show_entity_type is True
        assert EntityType.SSN in config.default_actions

    def test_custom_config(self):
        """Test: Anpassad konfiguration."""
        config = MaskingConfig(
            style=MaskingStyle.REDACTED,
            show_entity_type=False,
        )

        assert config.style == MaskingStyle.REDACTED
        assert config.show_entity_type is False


class TestEntityMasker:
    """Tester for EntityMasker."""

    @pytest.fixture
    def masker(self) -> EntityMasker:
        return EntityMasker()

    def test_mask_ssn(self, masker: EntityMasker):
        """Test: Personnummer maskeras alltid."""
        text = "Personnummer: 199001011234"
        entities = [
            Entity(
                text="199001011234",
                type=EntityType.SSN,
                start=14,
                end=26,
                confidence=0.99,
            )
        ]

        result = masker.mask_text(text, entities)

        assert "199001011234" not in result.masked_text
        assert "[MASKERAT: PERSONNUMMER]" in result.masked_text
        assert len(result.masked_entities) == 1

    def test_mask_phone(self, masker: EntityMasker):
        """Test: Telefonnummer maskeras."""
        text = "Ring: 070-123 45 67"
        entities = [
            Entity(
                text="070-123 45 67",
                type=EntityType.PHONE,
                start=6,
                end=19,
                confidence=0.90,
            )
        ]

        result = masker.mask_text(text, entities)

        assert "070-123 45 67" not in result.masked_text
        assert "[MASKERAT: TELEFON]" in result.masked_text

    def test_mask_email(self, masker: EntityMasker):
        """Test: E-post maskeras."""
        text = "Mail: test@example.com"
        entities = [
            Entity(
                text="test@example.com",
                type=EntityType.EMAIL,
                start=6,
                end=22,
                confidence=0.99,
            )
        ]

        result = masker.mask_text(text, entities)

        assert "test@example.com" not in result.masked_text
        assert "[MASKERAT: E-POST]" in result.masked_text

    def test_release_requester_entity(self, masker: EntityMasker):
        """Test: Bestellarens uppgifter lamnas ut."""
        text = "Klient: Anna Andersson"
        entities = [
            Entity(
                text="Anna Andersson",
                type=EntityType.PERSON,
                start=8,
                end=22,
                confidence=0.95,
            )
        ]

        result = masker.mask_text(
            text, entities, requester_entities={"Anna Andersson"}
        )

        assert "Anna Andersson" in result.masked_text
        assert len(result.released_entities) == 1

    def test_mask_third_party(self, masker: EntityMasker):
        """Test: Tredje mans uppgifter maskeras."""
        text = "Granne: Erik Eriksson"
        entities = [
            Entity(
                text="Erik Eriksson",
                type=EntityType.PERSON,
                start=8,
                end=21,
                confidence=0.95,
                role=PersonRole.THIRD_PARTY,
            )
        ]

        result = masker.mask_text(text, entities)

        assert "Erik Eriksson" not in result.masked_text
        assert "[MASKERAT: PERSON]" in result.masked_text

    def test_release_professional_name(self, masker: EntityMasker):
        """Test: Tjanstemannens namn lamnas ut."""
        text = "Handlaggare: Lisa Larsson"
        entities = [
            Entity(
                text="Lisa Larsson",
                type=EntityType.PERSON,
                start=13,
                end=25,
                confidence=0.95,
                role=PersonRole.PROFESSIONAL,
            )
        ]

        result = masker.mask_text(text, entities)

        assert "Lisa Larsson" in result.masked_text
        assert len(result.released_entities) == 1

    def test_mask_reporter(self, masker: EntityMasker):
        """Test: Anmalarens identitet maskeras."""
        text = "Anmalare: Karin Karlsson"
        entities = [
            Entity(
                text="Karin Karlsson",
                type=EntityType.PERSON,
                start=10,
                end=24,
                confidence=0.95,
                role=PersonRole.REPORTER,
            )
        ]

        result = masker.mask_text(text, entities)

        assert "Karin Karlsson" not in result.masked_text

    def test_multiple_entities(self, masker: EntityMasker):
        """Test: Flera entiteter maskeras korrekt."""
        text = "Person: 199001011234, tel: 070-123 45 67"
        entities = [
            Entity(text="199001011234", type=EntityType.SSN, start=8, end=20, confidence=0.99),
            Entity(text="070-123 45 67", type=EntityType.PHONE, start=27, end=40, confidence=0.90),
        ]

        result = masker.mask_text(text, entities)

        assert "199001011234" not in result.masked_text
        assert "070-123 45 67" not in result.masked_text
        assert len(result.masked_entities) == 2

    def test_statistics(self, masker: EntityMasker):
        """Test: Statistik beraknas korrekt."""
        text = "SSN: 199001011234, Org: Socialstyrelsen"
        entities = [
            Entity(text="199001011234", type=EntityType.SSN, start=5, end=17, confidence=0.99),
            Entity(text="Socialstyrelsen", type=EntityType.ORGANIZATION, start=24, end=39, confidence=0.90),
        ]

        result = masker.mask_text(text, entities)

        assert result.statistics["total_entities"] == 2
        assert result.statistics["masked_count"] == 1
        assert result.statistics["released_count"] == 1


class TestMaskingStyles:
    """Tester for olika maskeringsstilar."""

    def test_brackets_style(self):
        """Test: Brackets-stil."""
        config = MaskingConfig(style=MaskingStyle.BRACKETS)
        masker = EntityMasker(config)

        text = "SSN: 199001011234"
        entities = [Entity(text="199001011234", type=EntityType.SSN, start=5, end=17, confidence=0.99)]

        result = masker.mask_text(text, entities)

        assert "[MASKERAT: PERSONNUMMER]" in result.masked_text

    def test_redacted_style(self):
        """Test: Redacted-stil."""
        config = MaskingConfig(style=MaskingStyle.REDACTED)
        masker = EntityMasker(config)

        text = "SSN: 199001011234"
        entities = [Entity(text="199001011234", type=EntityType.SSN, start=5, end=17, confidence=0.99)]

        result = masker.mask_text(text, entities)

        assert "█" in result.masked_text

    def test_placeholder_style(self):
        """Test: Placeholder-stil."""
        config = MaskingConfig(style=MaskingStyle.PLACEHOLDER)
        masker = EntityMasker(config)

        text = "SSN: 199001011234"
        entities = [Entity(text="199001011234", type=EntityType.SSN, start=5, end=17, confidence=0.99)]

        result = masker.mask_text(text, entities)

        assert "<PERSONNUMMER>" in result.masked_text

    def test_anonymized_style(self):
        """Test: Anonymiserad stil."""
        config = MaskingConfig(style=MaskingStyle.ANONYMIZED)
        masker = EntityMasker(config)

        text = "Anna Andersson och Erik Eriksson"
        entities = [
            Entity(text="Anna Andersson", type=EntityType.PERSON, start=0, end=14, confidence=0.95, role=PersonRole.THIRD_PARTY),
            Entity(text="Erik Eriksson", type=EntityType.PERSON, start=19, end=32, confidence=0.95, role=PersonRole.THIRD_PARTY),
        ]

        result = masker.mask_text(text, entities)

        assert "Person A" in result.masked_text
        assert "Person B" in result.masked_text
        assert "Anna Andersson" not in result.masked_text

    def test_anonymized_same_person(self):
        """Test: Samma person far samma anonymisering."""
        config = MaskingConfig(style=MaskingStyle.ANONYMIZED)
        masker = EntityMasker(config)

        text = "Anna forst, sedan Anna igen"
        entities = [
            Entity(text="Anna", type=EntityType.PERSON, start=0, end=4, confidence=0.95, role=PersonRole.THIRD_PARTY),
            Entity(text="Anna", type=EntityType.PERSON, start=18, end=22, confidence=0.95, role=PersonRole.THIRD_PARTY),
        ]

        result = masker.mask_text(text, entities)

        # Samma person ska ha samma ersattning
        assert result.masked_text.count("Person A") == 2


class TestSectionMasker:
    """Tester for SectionMasker."""

    @pytest.fixture
    def masker(self) -> SectionMasker:
        return SectionMasker()

    def test_release_section(self, masker: SectionMasker):
        """Test: Sektion lamnas ut."""
        text = "Detta ar en neutral text."
        assessment = SensitivityAssessment(
            text=text,
            start=0,
            end=len(text),
            level=SensitivityLevel.LOW,
            primary_category=SensitivityCategory.NEUTRAL,
            recommended_action=MaskingAction.RELEASE,
        )

        result = masker.mask_section(text, assessment)

        assert result == text

    def test_mask_complete_section(self, masker: SectionMasker):
        """Test: Hel sektion maskeras."""
        text = "Kanslig information om halsotillstand."
        assessment = SensitivityAssessment(
            text=text,
            start=0,
            end=len(text),
            level=SensitivityLevel.CRITICAL,
            primary_category=SensitivityCategory.HEALTH,
            recommended_action=MaskingAction.MASK_COMPLETE,
            legal_basis="OSL 26:1",
        )

        result = masker.mask_section(text, assessment)

        assert "[SEKTION MASKERAD:" in result
        assert "HEALTH" in result
        assert "OSL 26:1" in result

    def test_mask_partial_section(self, masker: SectionMasker):
        """Test: Partiell sektionsmaskning."""
        text = "Forsta meningen ar OK. Andra meningen ar kanslig. Tredje ocksa."
        assessment = SensitivityAssessment(
            text=text,
            start=0,
            end=len(text),
            level=SensitivityLevel.MEDIUM,
            primary_category=SensitivityCategory.FAMILY,
            recommended_action=MaskingAction.MASK_PARTIAL,
        )

        result = masker.mask_section(text, assessment)

        assert "Forsta meningen ar OK." in result
        assert "[RESTERANDE TEXT MASKERAD]" in result

    def test_mask_multiple_sections(self, masker: SectionMasker):
        """Test: Flera sektioner maskeras."""
        sections = ["Sektion 1", "Sektion 2", "Sektion 3"]
        assessments = [
            SensitivityAssessment(
                text="Sektion 1", start=0, end=9,
                level=SensitivityLevel.LOW,
                primary_category=SensitivityCategory.NEUTRAL,
                recommended_action=MaskingAction.RELEASE,
            ),
            SensitivityAssessment(
                text="Sektion 2", start=0, end=9,
                level=SensitivityLevel.CRITICAL,
                primary_category=SensitivityCategory.HEALTH,
                recommended_action=MaskingAction.MASK_COMPLETE,
                legal_basis="OSL 26:1",
            ),
            SensitivityAssessment(
                text="Sektion 3", start=0, end=9,
                level=SensitivityLevel.LOW,
                primary_category=SensitivityCategory.NEUTRAL,
                recommended_action=MaskingAction.RELEASE,
            ),
        ]

        results = masker.mask_sections(sections, assessments)

        assert results[0] == "Sektion 1"  # Released
        assert "[SEKTION MASKERAD:" in results[1]  # Masked
        assert results[2] == "Sektion 3"  # Released


class TestPartialMasking:
    """Tester for partiell maskning."""

    def test_partial_mask_long_text(self):
        """Test: Partiell maskning av lang text."""
        masker = EntityMasker()

        entity = Entity(
            text="test@example.com",
            type=EntityType.EMAIL,
            start=0,
            end=16,
            confidence=0.99,
        )

        replacement = masker._create_bracket_replacement(entity, MaskingAction.MASK_PARTIAL)

        # Ska visa forsta och sista tecken
        assert replacement.startswith("t")
        assert replacement.endswith("m")
        assert "***" in replacement

    def test_partial_mask_short_text(self):
        """Test: Partiell maskning av kort text."""
        masker = EntityMasker()

        entity = Entity(
            text="AB",
            type=EntityType.MISC,
            start=0,
            end=2,
            confidence=0.9,
        )

        replacement = masker._create_bracket_replacement(entity, MaskingAction.MASK_PARTIAL)

        assert replacement == "***"


class TestEdgeCases:
    """Tester for kantfall."""

    def test_empty_entities(self):
        """Test: Tom entitetslista."""
        masker = EntityMasker()
        text = "Text utan entiteter."

        result = masker.mask_text(text, [])

        assert result.masked_text == text
        assert len(result.masked_entities) == 0

    def test_overlapping_entities(self):
        """Test: Overlappande entiteter hanteras."""
        masker = EntityMasker()
        text = "0701234567"  # Kan vara bade telefon och SSN

        entities = [
            Entity(text="0701234567", type=EntityType.PHONE, start=0, end=10, confidence=0.90),
        ]

        result = masker.mask_text(text, entities)

        assert "0701234567" not in result.masked_text

    def test_reset_person_mapping(self):
        """Test: Personmappning kan aterstallas."""
        config = MaskingConfig(style=MaskingStyle.ANONYMIZED)
        masker = EntityMasker(config)

        # Forsta dokumentet
        text1 = "Anna Andersson"
        entities1 = [Entity(text="Anna Andersson", type=EntityType.PERSON, start=0, end=14, confidence=0.95, role=PersonRole.THIRD_PARTY)]
        result1 = masker.mask_text(text1, entities1)

        assert "Person A" in result1.masked_text

        # Aterstall
        masker.reset_person_mapping()

        # Andra dokumentet - ska borja om fran A
        text2 = "Erik Eriksson"
        entities2 = [Entity(text="Erik Eriksson", type=EntityType.PERSON, start=0, end=13, confidence=0.95, role=PersonRole.THIRD_PARTY)]
        result2 = masker.mask_text(text2, entities2)

        assert "Person A" in result2.masked_text  # Borjar om fran A
