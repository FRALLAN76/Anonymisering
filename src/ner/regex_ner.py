"""Regex-baserad Named Entity Recognition för svenska entiteter."""

import re
from dataclasses import dataclass
from typing import Optional

from src.core.models import Entity, EntityType


@dataclass
class RegexNERConfig:
    """Konfiguration för regex-baserad NER."""

    extract_ssn: bool = True
    extract_phone: bool = True
    extract_email: bool = True
    extract_dates: bool = True
    extract_names: bool = True  # Svenska namn via listor
    validate_ssn: bool = True  # Kontrollera Luhn-algoritmen


class RegexNER:
    """
    Regex-baserad NER för strukturerade svenska entiteter.

    Hittar:
    - Personnummer (SSN)
    - Telefonnummer
    - E-postadresser
    - Datum
    - Svenska namn (förnamn + efternamn via listor/mönster)
    """

    # Svenska personnummer: YYMMDD-XXXX eller YYYYMMDD-XXXX
    # Månader 01-12, dagar 01-31 (eller +60 för samordningsnummer)
    SSN_PATTERNS = [
        # YYYYMMDD-XXXX (med bindestreck, 18xx/19xx/20xx)
        re.compile(r'\b((?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]|[6-9]\d))[-](\d{4})\b'),
        # YYYYMMDD-XXXX (med bindestreck, permissivt för ogiltiga datum)
        re.compile(r'\b(\d{8})[-](\d{4})\b'),
        # YYMMDD-XXXX (med bindestreck) - mer permissivt format
        re.compile(r'\b(\d{6})[-](\d{4})\b'),
        # YYYYMMDDXXXX (utan bindestreck, 12 siffror)
        re.compile(r'\b((?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]|[6-9]\d))(\d{4})\b'),
        # YYMMDDXXXX (utan bindestreck, 10 siffror - strikt datumvalidering)
        re.compile(r'\b(\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]|[6-9]\d))(\d{4})\b'),
    ]

    # Svenska telefonnummer - omfattande mönster
    PHONE_PATTERNS = [
        # === MOBIL ===
        # 070-123 45 67, 070 123 45 67
        re.compile(r'\b(07\d[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})\b'),
        # 0701234567
        re.compile(r'\b(07\d{8})\b'),
        # 070-1234567
        re.compile(r'\b(07\d[-\s]?\d{7})\b'),
        # +46 70 123 45 67, +4670-1234567
        re.compile(r'(\+46[-\s]?7\d[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})'),
        re.compile(r'(\+46[-\s]?7\d[-\s]?\d{7})'),

        # === STOCKHOLM (08) ===
        re.compile(r'\b(08[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})\b'),
        re.compile(r'\b(08[-\s]?\d{6,8})\b'),
        re.compile(r'(\+46[-\s]?8[-\s]?\d{6,8})'),

        # === GÖTEBORG (031) ===
        re.compile(r'\b(031[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2,3})\b'),
        re.compile(r'\b(031[-\s]?\d{6,8})\b'),
        re.compile(r'(\+46[-\s]?31[-\s]?\d{6,8})'),

        # === MALMÖ (040) ===
        re.compile(r'\b(040[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2})\b'),
        re.compile(r'\b(040[-\s]?\d{6,8})\b'),

        # === ÖVRIGA RIKTNUMMER ===
        # 0XX-XXX XX XX (treställigt riktnummer)
        re.compile(r'\b(0\d{2}[-\s]?\d{2,3}[-\s]?\d{2}[-\s]?\d{2})\b'),
        # 0X-XXX XX XX (tvåställigt riktnummer)
        re.compile(r'\b(0\d[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})\b'),
        # 0XXX-XXXXXX
        re.compile(r'\b(0\d{3}[-\s]?\d{6})\b'),

        # === INTERNATIONELLT ===
        re.compile(r'(\+46[-\s]?\d{1,3}[-\s]?\d{6,8})'),

        # === SPECIELLA FORMAT ===
        # 031-36 78 361 (Göteborg med extra siffra)
        re.compile(r'\b(\d{3}[-]\d{2}[-\s]?\d{2}[-\s]?\d{2,3})\b'),
        # XXXX-XXXXXX
        re.compile(r'\b(\d{4}[-]\d{6})\b'),
    ]

    # Svenska förnamn (vanliga)
    SWEDISH_FIRST_NAMES = {
        'Anna', 'Lars', 'Erik', 'Maria', 'Johan', 'Emma', 'Oscar', 'Patrik',
        'Fredrik', 'Christina', 'Magnus', 'Susanne', 'Anders', 'Helena', 'Per',
        'Margareta', 'Stefan', 'Birgitta', 'Mikael', 'Elisabeth', 'Jonas', 'Eva',
        'David', 'Ingrid', 'Daniel', 'Marie', 'Thomas', 'Linda', 'Marcus', 'Karin',
        'Mattias', 'Sara', 'Andreas', 'Lena', 'Peter', 'Annika', 'Christer',
        'Monica', 'Martin', 'Inger', 'Robert', 'Åsa', 'Nils', 'Gunilla', 'Kristina',
        'Ulf', 'Ulrika', 'Carl', 'Björn', 'Sven', 'Astrid', 'Gustav', 'Mats',
        'Lisa', 'Alexander', 'Jenny', 'Henrik', 'Malin', 'Niklas', 'Elin', 'Jan',
        'Kerstin', 'Håkan', 'Barbro', 'Bengt', 'Marianne', 'Karl', 'Ingela',
        'Göran', 'Ann', 'Lennart', 'Carina', 'Leif', 'Camilla', 'Tommy', 'Sofia',
        'Kenneth', 'Jessica', 'Roger', 'Caroline', 'Tomas', 'Katarina', 'Rolf',
        'Louise', 'Hans', 'Sandra', 'Claes', 'Rebecca', 'Bo', 'Johanna', 'Arne',
        'Therese', 'Kjell', 'Victoria', 'Jan-Erik', 'Ann-Christin', 'Per-Olof',
        'Ann-Marie', 'Karl-Erik', 'Eva-Lena', 'Jan-Olof', 'Ann-Sofie',
        # Fler moderna namn
        'William', 'Alice', 'Liam', 'Elsa', 'Noah', 'Maja', 'Lucas', 'Ella',
        'Oliver', 'Wilma', 'Hugo', 'Ebba', 'Axel', 'Alma', 'Leo', 'Olivia',
    }

    # Mönster för svenska efternamn
    SURNAME_PATTERNS = [
        # -son, -sen, -sson (Andersson, Johansson, etc.)
        re.compile(r'\b([A-ZÅÄÖ][a-zåäö]+(?:ss?on|sen))\b'),
        # -berg, -ström, -lund, -dahl, -gren, -qvist, -mark, -vall, -holm
        re.compile(r'\b([A-ZÅÄÖ][a-zåäö]+(?:berg|ström|lund|dahl|gren|qvist|quist|kvist|mark|vall|holm|blad|bäck|borg|stedt|felt|feldt|ling|löf|löv))\b'),
    ]

    # E-postadresser
    EMAIL_PATTERN = re.compile(
        r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    )

    # Svenska datum
    DATE_PATTERNS = [
        # YYYY-MM-DD
        re.compile(r'\b(\d{4}-\d{2}-\d{2})\b'),
        # DD/MM/YYYY eller DD-MM-YYYY
        re.compile(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b'),
        # "15 januari 2025" etc
        re.compile(
            r'\b(\d{1,2}\s+(?:januari|februari|mars|april|maj|juni|'
            r'juli|augusti|september|oktober|november|december)\s+\d{4})\b',
            re.IGNORECASE
        ),
    ]

    def __init__(self, config: Optional[RegexNERConfig] = None):
        """
        Initiera RegexNER.

        Args:
            config: Konfiguration för NER
        """
        self.config = config or RegexNERConfig()

    def extract_entities(self, text: str) -> list[Entity]:
        """
        Extrahera alla entiteter från text.

        Args:
            text: Texten att analysera

        Returns:
            Lista med identifierade entiteter
        """
        entities: list[Entity] = []

        if self.config.extract_ssn:
            entities.extend(self._extract_ssn(text))

        if self.config.extract_phone:
            entities.extend(self._extract_phones(text))

        if self.config.extract_email:
            entities.extend(self._extract_emails(text))

        if self.config.extract_dates:
            entities.extend(self._extract_dates(text))

        if self.config.extract_names:
            entities.extend(self._extract_names(text))

        # Sortera efter position och ta bort överlappande
        entities = self._remove_overlapping(entities)
        entities.sort(key=lambda e: e.start)

        return entities

    def _extract_ssn(self, text: str) -> list[Entity]:
        """Extrahera svenska personnummer."""
        entities = []
        found_positions: set[tuple[int, int]] = set()

        for pattern in self.SSN_PATTERNS:
            for match in pattern.finditer(text):
                pos = (match.start(), match.end())

                # Undvik duplicerade matchningar
                if any(self._overlaps(pos, existing) for existing in found_positions):
                    continue

                full_match = match.group(0)
                date_part = match.group(1)
                check_part = match.group(2)

                # Filtrera bort telefonnummer (07x, 08x utan bindestreck)
                if '-' not in full_match and full_match.startswith(('07', '08', '046')):
                    continue

                # Validera om konfigurerat
                confidence = 0.99
                if self.config.validate_ssn:
                    if not self._validate_ssn(date_part, check_part):
                        confidence = 0.7  # Lägre konfidens om validering misslyckas

                found_positions.add(pos)
                entities.append(Entity(
                    text=full_match,
                    type=EntityType.SSN,
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence,
                ))

        return entities

    def _validate_ssn(self, date_part: str, check_part: str) -> bool:
        """
        Validera personnummer med Luhn-algoritmen.

        Args:
            date_part: Datumdelen (YYMMDD eller YYYYMMDD)
            check_part: Kontrollsiffrorna (XXXX)

        Returns:
            True om personnumret är giltigt
        """
        # Normalisera till 10 siffror
        if len(date_part) == 8:
            date_part = date_part[2:]  # Ta bort århundrade

        digits = date_part + check_part

        if len(digits) != 10 or not digits.isdigit():
            return False

        # Luhn-algoritmen
        total = 0
        for i, digit in enumerate(digits[:-1]):
            d = int(digit)
            if i % 2 == 0:
                d *= 2
                if d > 9:
                    d -= 9
            total += d

        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(digits[-1])

    def _extract_phones(self, text: str) -> list[Entity]:
        """Extrahera telefonnummer."""
        entities = []
        found_positions: set[tuple[int, int]] = set()

        for pattern in self.PHONE_PATTERNS:
            for match in pattern.finditer(text):
                pos = (match.start(), match.end())

                # Undvik duplicerade matchningar
                if any(self._overlaps(pos, existing) for existing in found_positions):
                    continue

                phone = match.group(1)

                # Filtrera bort saker som ser ut som personnummer
                if self._looks_like_ssn(phone, text, match.start()):
                    continue

                found_positions.add(pos)
                entities.append(Entity(
                    text=phone,
                    type=EntityType.PHONE,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.90,
                ))

        return entities

    def _looks_like_ssn(self, text: str, full_text: str, position: int) -> bool:
        """Kontrollera om en sträng troligen är ett personnummer."""
        # Telefonnummer börjar ofta med 07 eller +46 - inte personnummer
        if text.startswith('07') or text.startswith('+46'):
            return False

        # Fast telefon: 0XX-XXX... eller 08-XXX... (riktnummer + mellanslag/bindestreck)
        if re.match(r'^0\d{1,3}[-\s]', text):
            return False

        # Ta bort formatering
        digits = re.sub(r'[-\s/]', '', text)

        # Personnummer har exakt 10 eller 12 siffror
        if len(digits) in (10, 12) and digits.isdigit():
            # Om det börjar med 0 följt av riktnummer-mönster, troligen telefon
            if digits.startswith('0') and len(digits) == 10:
                # Riktnummer börjar med 0 + 1-3 siffror, personnummer börjar inte med 0
                return False

            # Kolla om det ser ut som ett giltigt datum
            if len(digits) == 10:
                month = int(digits[2:4])
                day = int(digits[4:6])
            else:  # 12 siffror
                month = int(digits[4:6])
                day = int(digits[6:8])

            # Rimlig månad och dag
            if 1 <= month <= 12 and 1 <= day <= 31:
                return True

        return False

    def _extract_emails(self, text: str) -> list[Entity]:
        """Extrahera e-postadresser."""
        entities = []

        for match in self.EMAIL_PATTERN.finditer(text):
            entities.append(Entity(
                text=match.group(1),
                type=EntityType.EMAIL,
                start=match.start(),
                end=match.end(),
                confidence=0.99,
            ))

        return entities

    def _extract_dates(self, text: str) -> list[Entity]:
        """Extrahera datum."""
        entities = []
        found_positions: set[tuple[int, int]] = set()

        for pattern in self.DATE_PATTERNS:
            for match in pattern.finditer(text):
                pos = (match.start(), match.end())

                if any(self._overlaps(pos, existing) for existing in found_positions):
                    continue

                found_positions.add(pos)
                entities.append(Entity(
                    text=match.group(1),
                    type=EntityType.DATE,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95,
                ))

        return entities

    def _extract_names(self, text: str) -> list[Entity]:
        """
        Extrahera svenska namn via förnamnslistor och efternamnsmönster.

        Detta är ett komplement till BERT NER för att fånga vanliga
        svenska namn som BERT kan missa.
        """
        entities = []
        found_positions: set[tuple[int, int]] = set()

        # Extrahera förnamn från lista
        for name in self.SWEDISH_FIRST_NAMES:
            # Case-insensitive sökning men matcha hela ord
            pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                pos = (match.start(), match.end())

                if any(self._overlaps(pos, existing) for existing in found_positions):
                    continue

                # Kontrollera att det faktiskt är ett namn (stor bokstav i original)
                matched_text = match.group()
                if not matched_text[0].isupper():
                    continue

                found_positions.add(pos)
                entities.append(Entity(
                    text=matched_text,
                    type=EntityType.PERSON,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85,  # Något lägre konfidens än BERT
                ))

        # Extrahera efternamn via mönster
        for pattern in self.SURNAME_PATTERNS:
            for match in pattern.finditer(text):
                pos = (match.start(), match.end())

                if any(self._overlaps(pos, existing) for existing in found_positions):
                    continue

                surname = match.group(1)

                # Filtrera bort vanliga ord som matchar mönstret
                if surname.lower() in {'person', 'saken', 'taken', 'broken'}:
                    continue

                found_positions.add(pos)
                entities.append(Entity(
                    text=surname,
                    type=EntityType.PERSON,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.80,  # Efternamn har lägre konfidens
                ))

        return entities

    def _overlaps(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> bool:
        """Kontrollera om två positioner överlappar."""
        return not (pos1[1] <= pos2[0] or pos2[1] <= pos1[0])

    def _remove_overlapping(self, entities: list[Entity]) -> list[Entity]:
        """
        Ta bort överlappande entiteter, behåll den med högst konfidens.

        SSN har högst prioritet, sedan längre matchningar.
        """
        if not entities:
            return []

        # Sortera: SSN först, sedan efter längd (längre först), sedan konfidens
        def sort_key(e: Entity) -> tuple:
            type_priority = 0 if e.type == EntityType.SSN else 1
            return (type_priority, -(e.end - e.start), -e.confidence)

        sorted_entities = sorted(entities, key=sort_key)
        result: list[Entity] = []

        for entity in sorted_entities:
            # Kolla om den överlappar med någon redan vald entitet
            overlaps = False
            for existing in result:
                if self._overlaps((entity.start, entity.end), (existing.start, existing.end)):
                    overlaps = True
                    break

            if not overlaps:
                result.append(entity)

        return result

    def extract_ssn_only(self, text: str) -> list[Entity]:
        """
        Extrahera endast personnummer.

        Args:
            text: Texten att analysera

        Returns:
            Lista med personnummer-entiteter
        """
        return self._extract_ssn(text)
