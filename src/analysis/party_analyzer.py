"""Partsanalys för menprövning.

Identifierar parter i dokument och avgör vem som ska se vad.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from src.core.models import (
    DocumentParty,
    Entity,
    EntityType,
    PersonRole,
    RequesterType,
    SensitiveStatement,
    SensitivityCategory,
    SensitivityLevel,
)
from src.llm.client import LLMClient, LLMConfig
from src.llm.prompts import (
    SENSITIVITY_SYSTEM_PROMPT,
    IDENTIFY_PARTIES_PROMPT,
    OWNERSHIP_ANALYSIS_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class PartyAnalyzerConfig:
    """Konfiguration för partsanalys."""

    llm_config: Optional[LLMConfig] = None
    max_text_for_party_id: int = 5000


class PartyAnalyzer:
    """
    Analyserar dokument för att identifiera parter och deras relationer.

    Hanterar:
    - Identifiering av alla parter (mamma, pappa, barn, etc.)
    - Koppling av entiteter till parter
    - Analys av vem känslig info "tillhör"
    - Beslut om vad som ska maskeras beroende på beställare
    """

    # Mappning från LLM-roller till PersonRole
    ROLE_MAP = {
        "SUBJECT": PersonRole.SUBJECT,
        "PARENT_1": PersonRole.REQUESTER,  # Behandla som potentiell beställare
        "PARENT_2": PersonRole.THIRD_PARTY,
        "CHILD": PersonRole.REQUESTER_CHILD,
        "REPORTER": PersonRole.REPORTER,
        "PROFESSIONAL": PersonRole.PROFESSIONAL,
        "THIRD_PARTY": PersonRole.THIRD_PARTY,
    }

    def __init__(self, config: Optional[PartyAnalyzerConfig] = None):
        """Initiera partsanalysator."""
        self.config = config or PartyAnalyzerConfig()
        self._llm_client: Optional[LLMClient] = None

    @property
    def llm_client(self) -> LLMClient:
        """Lazy loading av LLM-klient."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self.config.llm_config)
        return self._llm_client

    def identify_parties(
        self,
        text: str,
        entities: list[Entity],
    ) -> list[DocumentParty]:
        """
        Identifiera alla parter i ett dokument.

        Args:
            text: Dokumenttexten
            entities: Identifierade entiteter

        Returns:
            Lista med identifierade parter
        """
        # Samla unika personnamn
        person_names = list(set(
            e.text for e in entities
            if e.type == EntityType.PERSON and len(e.text) >= 2
        ))

        if not self.llm_client.is_configured():
            # Fallback utan LLM - skapa grundläggande parter
            return self._create_basic_parties(person_names, entities)

        try:
            # Använd LLM för att identifiera parter och relationer
            prompt = IDENTIFY_PARTIES_PROMPT.format(
                text=text[:self.config.max_text_for_party_id],
                person_names=", ".join(person_names[:20]),
            )

            result = self.llm_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=SENSITIVITY_SYSTEM_PROMPT,
            )

            return self._parse_party_result(result, entities)

        except Exception as e:
            logger.warning(f"Partsidentifiering misslyckades: {e}")
            return self._create_basic_parties(person_names, entities)

    def _parse_party_result(
        self,
        result: dict,
        entities: list[Entity],
    ) -> list[DocumentParty]:
        """Parsa LLM-resultat till DocumentParty-objekt."""
        parties = []

        for party_data in result.get("parties", []):
            party_id = party_data.get("party_id", f"P{len(parties)+1}")
            names = party_data.get("names", [])
            role_str = party_data.get("role", "UNKNOWN")
            role = self.ROLE_MAP.get(role_str, PersonRole.UNKNOWN)

            # Hitta positioner där partens namn nämns
            positions = []
            for name in names:
                for entity in entities:
                    if entity.type == EntityType.PERSON and entity.text.lower() == name.lower():
                        positions.append((entity.start, entity.end))

            party = DocumentParty(
                party_id=party_id,
                name=names[0] if names else None,
                role=role,
                relation=party_data.get("relation"),
                is_minor=party_data.get("is_minor"),
                aliases=names[1:] if len(names) > 1 else [],
                mentioned_positions=positions,
            )
            parties.append(party)

        return parties

    def _create_basic_parties(
        self,
        person_names: list[str],
        entities: list[Entity],
    ) -> list[DocumentParty]:
        """Skapa grundläggande parter utan LLM."""
        parties = []

        for i, name in enumerate(person_names[:10]):  # Max 10 parter
            # Hitta positioner
            positions = [
                (e.start, e.end) for e in entities
                if e.type == EntityType.PERSON and e.text == name
            ]

            # Försök gissa relation baserat på namn
            relation = None
            name_lower = name.lower()
            
            # Förbättrad namngissning för vanliga relationer
            if any(word in name_lower for word in ["mamma", "mamma", "mor"]):
                relation = "mamma"
            elif any(word in name_lower for word in ["pappa", "far", "fader", "papa"]):
                relation = "pappa"
            elif any(word in name_lower for word in ["morfar", "farmor", "farfar", "mormor"]):
                relation = "morfar" if "mor" in name_lower else "farfar"
            elif any(word in name_lower for word in ["barn", "son", "dotter", "pojke", "flicka"]):
                relation = "barn"
            elif any(word in name_lower for word in ["släkting", "kusin", "faster", "farbror", "moster", "morbror"]):
                relation = "släkting"
            elif any(word in name_lower for word in ["granne", "granne"]):
                relation = "granne"
            elif any(word in name_lower for word in ["vän", "kompis"]):
                relation = "vän"
            
            # Försök analysera kontext för att hitta relationer
            # (endast om vi har tillgång till texten via entiteter)
            if positions and entities:
                relation = self._infer_relation_from_context(
                    name, positions, entities
                ) or relation
            
            party = DocumentParty(
                party_id=f"P{i+1}",
                name=name,
                role=PersonRole.UNKNOWN,
                relation=relation,  # Lägg till relation
                mentioned_positions=positions,
            )
            parties.append(party)

        return parties

    def _infer_relation_from_context(
        self,
        name: str,
        positions: list[tuple[int, int]],
        entities: list[Entity],
    ) -> Optional[str]:
        """
        Försök att inferera relationer från textkontext.
        
        Analyserar texten runt namnet för att hitta ledtrådar
        om relationen (t.ex. "Sveinung och hans mamma", "barnet med pappa").
        """
        if not positions:
            return None
        
        # För enkelhetens skull, returnera None för nu
        # En fullständig implementation skulle analysera texten
        # runt varje förekomst av namnet
        return None

    def analyze_ownership(
        self,
        text: str,
        parties: list[DocumentParty],
        category: SensitivityCategory,
    ) -> Optional[SensitiveStatement]:
        """
        Analysera vem en känslig uppgift tillhör.

        Args:
            text: Det känsliga textavsnittet
            parties: Identifierade parter
            category: Känslighetskategori

        Returns:
            SensitiveStatement med ägarskap och skydd
        """
        if not self.llm_client.is_configured() or not parties:
            return None

        try:
            # Formatera parter för prompten
            parties_str = "\n".join([
                f"- {p.party_id}: {p.name} ({p.relation or p.role.value})"
                for p in parties
            ])

            prompt = OWNERSHIP_ANALYSIS_PROMPT.format(
                text=text[:500],
                parties=parties_str,
                category=category.value,
            )

            result = self.llm_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=SENSITIVITY_SYSTEM_PROMPT,
            )

            owner_id = result.get("information_concerns", "")
            disclosed_by = result.get("disclosed_by")
            protect_from = result.get("protect_from_parties", [])

            return SensitiveStatement(
                text=text[:500],
                start=0,
                end=len(text),
                owner_party_id=owner_id,
                disclosed_by_party_id=disclosed_by,
                category=category,
                level=SensitivityLevel.HIGH,  # Default
                protect_from=protect_from,
            )

        except Exception as e:
            logger.warning(f"Ägarskapsanalys misslyckades: {e}")
            return None

    def get_masking_rules(
        self,
        requester_type: RequesterType,
        requester_party_id: Optional[str],
        parties: list[DocumentParty],
    ) -> dict[str, str]:
        """
        Få maskeringsregler baserat på vem som begär ut.

        Args:
            requester_type: Typ av beställare
            requester_party_id: Part-ID om beställaren är part i ärendet
            parties: Alla parter

        Returns:
            Dict med party_id -> åtgärd (RELEASE/MASK)
        """
        rules = {}

        for party in parties:
            if party.party_id == requester_party_id:
                # Beställarens egen info - visa
                rules[party.party_id] = "RELEASE_OWN"
            elif requester_type == RequesterType.PUBLIC:
                # Allmänheten - maskera allt
                rules[party.party_id] = "MASK_COMPLETE"
            elif requester_type == RequesterType.AUTHORITY:
                # Myndighet - visa mer men inte allt
                rules[party.party_id] = "RELEASE_AUTHORITY"
            elif party.role == PersonRole.REPORTER:
                # Anmälare - alltid skydda
                rules[party.party_id] = "MASK_COMPLETE"
            elif party.role == PersonRole.PROFESSIONAL:
                # Tjänstemän - namn OK
                rules[party.party_id] = "RELEASE"
            else:
                # Andra parter - maskera
                rules[party.party_id] = "MASK_COMPLETE"

        return rules

    def should_mask_for_requester(
        self,
        statement: SensitiveStatement,
        requester_type: RequesterType,
        requester_party_id: Optional[str],
    ) -> tuple[bool, str]:
        """
        Avgör om en känslig uppgift ska maskeras för beställaren.

        Args:
            statement: Den känsliga uppgiften
            requester_type: Typ av beställare
            requester_party_id: Beställarens part-ID

        Returns:
            Tuple med (ska_maskeras, anledning)
        """
        # Allmänheten får aldrig se känslig info
        if requester_type == RequesterType.PUBLIC:
            return True, "Sekretess mot allmänheten (OSL 26:1)"

        # Beställarens egen info - visa
        if statement.owner_party_id == requester_party_id:
            return False, "Beställarens egen uppgift (partsinsyn)"

        # Explicit skyddad från beställaren
        if requester_party_id and requester_party_id in statement.protect_from:
            return True, "Uppgiften ska skyddas från denna part"

        # Info som annan part berättat om sig själv
        if statement.disclosed_by_party_id and statement.disclosed_by_party_id != requester_party_id:
            if statement.owner_party_id == statement.disclosed_by_party_id:
                return True, "Info som annan part berättat om sig själv (OSL 26:1)"

        # Default för andra parters info
        if statement.owner_party_id != requester_party_id:
            return True, "Uppgift om annan person (OSL 26:1)"

        return False, "Partsinsyn medger utlämnande"
