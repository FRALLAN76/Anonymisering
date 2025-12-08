"""Enhetstester för Named Entity Recognition."""

import pytest

from src.ner.regex_ner import RegexNER, RegexNERConfig
from src.core.models import EntityType


class TestRegexNER:
    """Tester för RegexNER."""

    @pytest.fixture
    def ner(self) -> RegexNER:
        """Skapa en NER-instans."""
        return RegexNER()

    # === PERSONNUMMER ===

    def test_extract_ssn_with_dash(self, ner: RegexNER):
        """Test: Personnummer med bindestreck."""
        text = "Personnummer: 199001011234"
        entities = ner.extract_entities(text)

        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        assert len(ssn_entities) == 1
        assert "199001011234" in ssn_entities[0].text

    def test_extract_ssn_yymmdd_format(self, ner: RegexNER):
        """Test: Personnummer i YYMMDD-XXXX format."""
        text = "Klient: 900101-1234"
        entities = ner.extract_entities(text)

        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        assert len(ssn_entities) == 1
        assert "900101-1234" in ssn_entities[0].text

    def test_extract_ssn_yyyymmdd_format(self, ner: RegexNER):
        """Test: Personnummer i YYYYMMDD-XXXX format."""
        text = "Ärendebärare: 19900101-1234"
        entities = ner.extract_entities(text)

        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        assert len(ssn_entities) == 1

    def test_extract_multiple_ssn(self, ner: RegexNER):
        """Test: Flera personnummer i samma text."""
        text = """
        Registerledare: 18561225-1234
        Ärendebärare: 18091331-1234
        """
        entities = ner.extract_entities(text)

        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        assert len(ssn_entities) == 2

    def test_ssn_validation_valid(self, ner: RegexNER):
        """Test: Validering av giltigt personnummer."""
        # 811218-9876 är ett giltigt test-personnummer (Luhn)
        result = ner._validate_ssn("811218", "9876")
        assert result is True

    def test_ssn_high_confidence_for_valid(self, ner: RegexNER):
        """Test: Hög konfidens för validerade personnummer."""
        text = "Person: 811218-9876"
        entities = ner.extract_entities(text)

        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        assert len(ssn_entities) == 1
        assert ssn_entities[0].confidence >= 0.7

    # === TELEFONNUMMER ===

    def test_extract_mobile_phone(self, ner: RegexNER):
        """Test: Mobilnummer."""
        text = "Telefon: 070-123 45 67"
        entities = ner.extract_entities(text)

        phone_entities = [e for e in entities if e.type == EntityType.PHONE]
        assert len(phone_entities) == 1
        assert "070" in phone_entities[0].text

    def test_extract_mobile_phone_no_spaces(self, ner: RegexNER):
        """Test: Mobilnummer utan mellanslag."""
        text = "Ring: 0701234567"
        entities = ner.extract_entities(text)

        phone_entities = [e for e in entities if e.type == EntityType.PHONE]
        assert len(phone_entities) >= 1

    def test_extract_landline_phone(self, ner: RegexNER):
        """Test: Fast telefonnummer."""
        text = "Kontor: 031-123 45 67"
        entities = ner.extract_entities(text)

        phone_entities = [e for e in entities if e.type == EntityType.PHONE]
        assert len(phone_entities) >= 1

    def test_extract_international_phone(self, ner: RegexNER):
        """Test: Internationellt nummer."""
        text = "Kontakt: +46 70 123 45 67"
        entities = ner.extract_entities(text)

        phone_entities = [e for e in entities if e.type == EntityType.PHONE]
        assert len(phone_entities) >= 1

    # === E-POST ===

    def test_extract_email(self, ner: RegexNER):
        """Test: E-postadress."""
        text = "E-post: anna.svensson@example.com"
        entities = ner.extract_entities(text)

        email_entities = [e for e in entities if e.type == EntityType.EMAIL]
        assert len(email_entities) == 1
        assert email_entities[0].text == "anna.svensson@example.com"

    def test_extract_email_with_subdomain(self, ner: RegexNER):
        """Test: E-post med subdomän."""
        text = "Mail: user@mail.goteborg.se"
        entities = ner.extract_entities(text)

        email_entities = [e for e in entities if e.type == EntityType.EMAIL]
        assert len(email_entities) == 1

    def test_extract_multiple_emails(self, ner: RegexNER):
        """Test: Flera e-postadresser."""
        text = """
        Kontakt: person1@example.com
        Kopia: person2@test.se
        """
        entities = ner.extract_entities(text)

        email_entities = [e for e in entities if e.type == EntityType.EMAIL]
        assert len(email_entities) == 2

    # === DATUM ===

    def test_extract_date_iso(self, ner: RegexNER):
        """Test: Datum i ISO-format."""
        text = "Datum: 2025-01-15"
        entities = ner.extract_entities(text)

        date_entities = [e for e in entities if e.type == EntityType.DATE]
        assert len(date_entities) == 1
        assert date_entities[0].text == "2025-01-15"

    def test_extract_date_swedish(self, ner: RegexNER):
        """Test: Datum på svenska."""
        text = "Möte: 15 januari 2025"
        entities = ner.extract_entities(text)

        date_entities = [e for e in entities if e.type == EntityType.DATE]
        assert len(date_entities) == 1

    # === KOMBINERAT ===

    def test_extract_all_types(self, ner: RegexNER):
        """Test: Alla entitetstyper i samma text."""
        text = """
        Ärende gällande 199001011234.
        Kontakt: 070-123 45 67 eller anna@example.com
        Datum: 2025-01-15
        """
        entities = ner.extract_entities(text)

        types = {e.type for e in entities}
        assert EntityType.SSN in types
        assert EntityType.PHONE in types
        assert EntityType.EMAIL in types
        assert EntityType.DATE in types

    def test_entities_are_sorted_by_position(self, ner: RegexNER):
        """Test: Entiteter sorteras efter position."""
        text = "070-111 22 33 och 199001011234"
        entities = ner.extract_entities(text)

        positions = [e.start for e in entities]
        assert positions == sorted(positions)

    def test_overlapping_entities_handled(self, ner: RegexNER):
        """Test: Överlappande entiteter hanteras."""
        # Ett personnummer ska inte också matcha som telefonnummer
        text = "Personnummer: 199001011234"
        entities = ner.extract_entities(text)

        # Ska bara finnas en entitet för samma text
        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        assert len(ssn_entities) == 1

    def test_no_false_positives_in_normal_text(self, ner: RegexNER):
        """Test: Ingen felaktig matchning i vanlig text."""
        text = "Detta är en vanlig mening utan känsliga uppgifter."
        entities = ner.extract_entities(text)

        # Ska inte hitta något
        assert len(entities) == 0

    # === KONFIGURATION ===

    def test_disable_ssn_extraction(self):
        """Test: Inaktivera SSN-extraktion."""
        config = RegexNERConfig(extract_ssn=False)
        ner = RegexNER(config)

        text = "Person: 199001011234"
        entities = ner.extract_entities(text)

        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        assert len(ssn_entities) == 0

    def test_disable_phone_extraction(self):
        """Test: Inaktivera telefon-extraktion."""
        config = RegexNERConfig(extract_phone=False)
        ner = RegexNER(config)

        text = "Ring: 070-123 45 67"
        entities = ner.extract_entities(text)

        phone_entities = [e for e in entities if e.type == EntityType.PHONE]
        assert len(phone_entities) == 0

    def test_disable_ssn_validation(self):
        """Test: Inaktivera SSN-validering."""
        config = RegexNERConfig(validate_ssn=False)
        ner = RegexNER(config)

        text = "Person: 000000-0000"  # Ogiltigt personnummer
        entities = ner.extract_entities(text)

        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        assert len(ssn_entities) == 1
        # Ska ha hög konfidens även utan validering
        assert ssn_entities[0].confidence == 0.99

    # === POSITION OCH OFFSET ===

    def test_entity_positions_are_correct(self, ner: RegexNER):
        """Test: Entitetspositioner är korrekta."""
        text = "Start: 199001011234 slut"
        entities = ner.extract_entities(text)

        ssn_entity = [e for e in entities if e.type == EntityType.SSN][0]

        # Verifiera att positionen är korrekt
        assert text[ssn_entity.start:ssn_entity.end] == ssn_entity.text

    def test_extract_ssn_only_method(self, ner: RegexNER):
        """Test: extract_ssn_only metoden."""
        text = "Person: 199001011234, tel: 070-123 45 67"
        entities = ner.extract_ssn_only(text)

        assert len(entities) == 1
        assert entities[0].type == EntityType.SSN


class TestRegexNERConfig:
    """Tester för konfiguration."""

    def test_default_config(self):
        """Test: Standardkonfiguration."""
        config = RegexNERConfig()

        assert config.extract_ssn is True
        assert config.extract_phone is True
        assert config.extract_email is True
        assert config.extract_dates is True
        assert config.validate_ssn is True

    def test_custom_config(self):
        """Test: Anpassad konfiguration."""
        config = RegexNERConfig(
            extract_ssn=True,
            extract_phone=False,
            extract_email=False,
            extract_dates=False,
        )

        assert config.extract_ssn is True
        assert config.extract_phone is False


class TestRealWorldExamples:
    """Tester med verkliga exempel från socialtjänstakter."""

    @pytest.fixture
    def ner(self) -> RegexNER:
        return RegexNER()

    def test_typical_social_services_header(self, ner: RegexNER):
        """Test: Typisk ärendehuvud från socialtjänsten."""
        text = """
        Akt
        Arkivbildare: SDN GUNNARED
        Registerledare: 18561225-1234
        Ärendebärare: 18091331-1234
        Uppläggningsdatum: 2016-01-12
        """
        entities = ner.extract_entities(text)

        ssn_entities = [e for e in entities if e.type == EntityType.SSN]
        date_entities = [e for e in entities if e.type == EntityType.DATE]

        assert len(ssn_entities) == 2
        assert len(date_entities) == 1

    def test_contact_information_section(self, ner: RegexNER):
        """Test: Kontaktinformationssektion."""
        text = """
        Kontaktuppgifter:
        Telefon: 0707-720707
        E-post: handlaggare@goteborg.se
        """
        entities = ner.extract_entities(text)

        phone_entities = [e for e in entities if e.type == EntityType.PHONE]
        email_entities = [e for e in entities if e.type == EntityType.EMAIL]

        assert len(phone_entities) >= 1
        assert len(email_entities) == 1

    def test_journal_entry(self, ner: RegexNER):
        """Test: Journalanteckning."""
        text = """
        2025-05-09 -- Aktualisering
        Inkommen anmälan gällande familjen på Ebbe Lieberathsgatan 93.
        Kontaktuppgift: 1234-556789
        """
        entities = ner.extract_entities(text)

        date_entities = [e for e in entities if e.type == EntityType.DATE]
        assert len(date_entities) >= 1
