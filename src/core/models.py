"""Pydantic-modeller för menprövningsverktyget."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    """Typer av entiteter som kan identifieras."""

    PERSON = "PERSON"
    SSN = "SSN"  # Personnummer
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    ADDRESS = "ADDRESS"
    ORGANIZATION = "ORG"
    LOCATION = "LOCATION"
    DATE = "DATE"
    MISC = "MISC"


class PersonRole(str, Enum):
    """Roller som en person kan ha i ett ärende."""

    REQUESTER = "REQUESTER"  # Beställaren
    REQUESTER_CHILD = "REQUESTER_CHILD"  # Beställarens barn
    SUBJECT = "SUBJECT"  # Den ärendet handlar om
    REPORTER = "REPORTER"  # Anmälare
    THIRD_PARTY = "THIRD_PARTY"  # Tredje man
    PROFESSIONAL = "PROFESSIONAL"  # Tjänsteman
    UNKNOWN = "UNKNOWN"


class RequesterType(str, Enum):
    """Typ av beställare - påverkar vad som lämnas ut."""

    SUBJECT_SELF = "SUBJECT_SELF"  # Ärendet handlar om beställaren själv
    PARENT_1 = "PARENT_1"  # Förälder 1 (t.ex. mamma)
    PARENT_2 = "PARENT_2"  # Förälder 2 (t.ex. pappa)
    CHILD_OVER_15 = "CHILD_OVER_15"  # Barn över 15 år
    LEGAL_GUARDIAN = "LEGAL_GUARDIAN"  # Vårdnadshavare
    OTHER_PARTY = "OTHER_PARTY"  # Annan part i ärendet
    AUTHORITY = "AUTHORITY"  # Annan myndighet
    PUBLIC = "PUBLIC"  # Allmänheten (strängast sekretess)


class SensitivityLevel(str, Enum):
    """Känslighetsnivåer enligt OSL."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SensitivityCategory(str, Enum):
    """Kategorier av känslig information."""

    HEALTH = "HEALTH"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    ADDICTION = "ADDICTION"
    VIOLENCE = "VIOLENCE"
    FAMILY = "FAMILY"
    ECONOMY = "ECONOMY"
    HOUSING = "HOUSING"
    SEXUAL = "SEXUAL"
    CRIMINAL = "CRIMINAL"
    NEUTRAL = "NEUTRAL"


class MaskingAction(str, Enum):
    """Åtgärder för maskning."""

    RELEASE = "RELEASE"  # Lämna ut
    MASK_PARTIAL = "MASK_PARTIAL"  # Delvis maskning
    MASK_COMPLETE = "MASK_COMPLETE"  # Fullständig maskning
    ASSESS = "ASSESS"  # Kräver manuell bedömning


class Entity(BaseModel):
    """En identifierad entitet i text."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(..., description="Entitetens text")
    type: EntityType = Field(..., description="Typ av entitet")
    start: int = Field(..., ge=0, description="Startposition i texten")
    end: int = Field(..., ge=0, description="Slutposition i texten")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Konfidens 0-1")
    role: Optional[PersonRole] = Field(default=None, description="Roll om PERSON")
    belongs_to: Optional[str] = Field(default=None, description="ID på tillhörande person")


class DocumentParty(BaseModel):
    """En identifierad part i dokumentet."""

    party_id: str = Field(..., description="Unikt ID för parten")
    name: Optional[str] = Field(default=None, description="Namn om identifierat")
    ssn: Optional[str] = Field(default=None, description="Personnummer om identifierat")
    role: PersonRole = Field(..., description="Roll i ärendet")
    relation: Optional[str] = Field(default=None, description="Relation (mamma, pappa, barn)")
    is_minor: Optional[bool] = Field(default=None, description="Är minderårig")
    aliases: list[str] = Field(default_factory=list, description="Alternativa benämningar")
    mentioned_positions: list[tuple[int, int]] = Field(
        default_factory=list, description="Positioner där parten nämns"
    )


class SensitiveStatement(BaseModel):
    """En känslig uppgift och vem den tillhör."""

    text: str = Field(..., description="Textavsnittet")
    start: int = Field(..., ge=0, description="Startposition")
    end: int = Field(..., ge=0, description="Slutposition")
    owner_party_id: str = Field(..., description="Part som uppgiften tillhör/gäller")
    disclosed_by_party_id: Optional[str] = Field(
        default=None, description="Part som avslöjade uppgiften (om annan)"
    )
    category: SensitivityCategory = Field(..., description="Typ av känslig uppgift")
    level: SensitivityLevel = Field(..., description="Känslighetsnivå")
    protect_from: list[str] = Field(
        default_factory=list, description="Part-IDs som INTE ska se detta"
    )


class PageContent(BaseModel):
    """Innehåll från en dokumentsida."""

    page_number: int = Field(..., ge=1, description="Sidnummer")
    text: str = Field(..., description="Extraherad text")
    extraction_method: str = Field(default="native", description="native eller ocr")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraktionskonfidens")


class ExtractedDocument(BaseModel):
    """Ett extraherat dokument."""

    source_path: str = Field(..., description="Sökväg till källfilen")
    pages: list[PageContent] = Field(default_factory=list, description="Sidinnehåll")
    total_pages: int = Field(..., ge=0, description="Totalt antal sidor")
    full_text: str = Field(..., description="All text kombinerad")
    extraction_method: str = Field(default="native", description="Övergripande metod")
    metadata: dict = Field(default_factory=dict, description="Dokumentmetadata")


class SensitivityAssessment(BaseModel):
    """Känslighetsbedömning för ett textavsnitt."""

    text: str = Field(..., description="Det bedömda textavsnittet")
    start: int = Field(..., ge=0, description="Startposition")
    end: int = Field(..., ge=0, description="Slutposition")
    level: SensitivityLevel = Field(..., description="Känslighetsnivå")
    primary_category: SensitivityCategory = Field(..., description="Primär kategori")
    secondary_categories: list[SensitivityCategory] = Field(
        default_factory=list, description="Sekundära kategorier"
    )
    affected_persons: list[str] = Field(
        default_factory=list, description="Berörda personer (entitets-ID)"
    )
    reasons: list[str] = Field(default_factory=list, description="Motiveringar")
    legal_basis: str = Field(default="OSL 26:1", description="Lagstöd")
    recommended_action: MaskingAction = Field(..., description="Rekommenderad åtgärd")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Bedömningskonfidens")


class AnalysisResult(BaseModel):
    """Komplett analysresultat för ett dokument."""

    document_id: str = Field(..., description="Dokument-ID")
    source_path: str = Field(..., description="Källfil")
    entities: list[Entity] = Field(default_factory=list, description="Identifierade entiteter")
    assessments: list[SensitivityAssessment] = Field(
        default_factory=list, description="Känslighetsbedömningar"
    )
    overall_sensitivity: SensitivityLevel = Field(..., description="Övergripande känslighetsnivå")
    sections_to_mask: list[int] = Field(
        default_factory=list, description="Sektioner som ska maskeras"
    )
    processing_time_ms: float = Field(default=0.0, description="Bearbetningstid i ms")
    model_versions: dict = Field(default_factory=dict, description="Använda modellversioner")
