"""Enhetstester för SensitivityAnalyzer."""

import pytest
from unittest.mock import Mock, patch

from src.analysis.sensitivity_analyzer import (
    SensitivityAnalyzer,
    SensitivityAnalyzerConfig,
)
from src.core.models import (
    Entity,
    EntityType,
    PersonRole,
    SensitivityCategory,
    SensitivityLevel,
    MaskingAction,
)


class TestSensitivityAnalyzerConfig:
    """Tester för konfiguration."""

    def test_default_config(self):
        """Test: Standardkonfiguration."""
        config = SensitivityAnalyzerConfig()

        assert config.max_section_length == 2000
        assert config.min_section_length == 50
        assert config.min_confidence_for_mask == 0.6

    def test_custom_config(self):
        """Test: Anpassad konfiguration."""
        config = SensitivityAnalyzerConfig(
            max_section_length=1000,
            min_confidence_for_mask=0.8,
        )

        assert config.max_section_length == 1000
        assert config.min_confidence_for_mask == 0.8


class TestKeywordAnalysis:
    """Tester för nyckelordsbaserad analys."""

    @pytest.fixture
    def analyzer(self) -> SensitivityAnalyzer:
        """Skapa analyzer utan LLM."""
        config = SensitivityAnalyzerConfig()
        analyzer = SensitivityAnalyzer(config)
        # Tvinga laddning av OSL-regler
        _ = analyzer.osl_rules
        return analyzer

    def test_detect_health_keywords(self, analyzer: SensitivityAnalyzer):
        """Test: Hälsa-nyckelord identifieras."""
        text = "Patienten har diagnos diabetes och får behandling med insulin."

        result = analyzer._keyword_analysis(text)

        assert "HEALTH" in result["categories"]
        assert "diagnos" in result["keywords_found"]
        assert result["highest_level"] == "CRITICAL"

    def test_detect_mental_health_keywords(self, analyzer: SensitivityAnalyzer):
        """Test: Psykisk hälsa-nyckelord identifieras."""
        text = "Klienten har depression och går i terapi hos psykolog."

        result = analyzer._keyword_analysis(text)

        assert "MENTAL_HEALTH" in result["categories"]
        assert result["highest_level"] == "CRITICAL"

    def test_detect_violence_keywords(self, analyzer: SensitivityAnalyzer):
        """Test: Våld-nyckelord identifieras."""
        text = "Kvinnan berättar om misshandel och hot från sin partner."

        result = analyzer._keyword_analysis(text)

        assert "VIOLENCE" in result["categories"]
        assert result["highest_level"] == "CRITICAL"

    def test_detect_economy_keywords(self, analyzer: SensitivityAnalyzer):
        """Test: Ekonomi-nyckelord identifieras."""
        text = "Familjen har skulder hos kronofogden och ansöker om försörjningsstöd."

        result = analyzer._keyword_analysis(text)

        assert "ECONOMY" in result["categories"]
        assert result["highest_level"] == "HIGH"

    def test_no_keywords_detected(self, analyzer: SensitivityAnalyzer):
        """Test: Neutral text utan känsliga nyckelord."""
        text = "Mötet hölls klockan 14:00 i konferensrummet."

        result = analyzer._keyword_analysis(text)

        assert len(result["categories"]) == 0
        assert result["highest_level"] == "LOW"

    def test_multiple_categories(self, analyzer: SensitivityAnalyzer):
        """Test: Flera kategorier i samma text."""
        text = "Personen har missbruksproblem och ekonomiska problem med skulder."

        result = analyzer._keyword_analysis(text)

        assert "ADDICTION" in result["categories"]
        assert "ECONOMY" in result["categories"]


class TestAnalyzeSection:
    """Tester för sektionsanalys."""

    @pytest.fixture
    def analyzer_no_llm(self) -> SensitivityAnalyzer:
        """Skapa analyzer utan LLM."""
        analyzer = SensitivityAnalyzer()
        # Säkerställ att LLM inte är konfigurerad
        analyzer._llm_client = Mock()
        analyzer._llm_client.is_configured.return_value = False
        return analyzer

    def test_analyze_critical_section(self, analyzer_no_llm: SensitivityAnalyzer):
        """Test: Kritisk sektion bedöms korrekt."""
        text = "Klienten har diagnos depression och behandlas på psykiatrisk klinik."

        assessment = analyzer_no_llm.analyze_section(text)

        assert assessment.level in (SensitivityLevel.CRITICAL, SensitivityLevel.HIGH)
        assert assessment.recommended_action == MaskingAction.MASK_COMPLETE

    def test_analyze_neutral_section(self, analyzer_no_llm: SensitivityAnalyzer):
        """Test: Neutral sektion bedöms korrekt."""
        text = "Dokumentet är daterat 2025-01-15 och signerat av handläggaren."

        assessment = analyzer_no_llm.analyze_section(text)

        assert assessment.level == SensitivityLevel.MEDIUM or assessment.level == SensitivityLevel.LOW
        assert assessment.primary_category == SensitivityCategory.NEUTRAL

    def test_assessment_has_required_fields(self, analyzer_no_llm: SensitivityAnalyzer):
        """Test: Bedömningen innehåller alla fält."""
        text = "Personen bor i skyddat boende efter våld i hemmet."

        assessment = analyzer_no_llm.analyze_section(text)

        assert assessment.text
        assert assessment.level is not None
        assert assessment.primary_category is not None
        assert assessment.recommended_action is not None
        assert 0 <= assessment.confidence <= 1


class TestRoleIdentification:
    """Tester för rollidentifiering."""

    @pytest.fixture
    def analyzer(self) -> SensitivityAnalyzer:
        """Skapa analyzer utan LLM."""
        analyzer = SensitivityAnalyzer()
        analyzer._llm_client = Mock()
        analyzer._llm_client.is_configured.return_value = False
        return analyzer

    def test_identify_professional(self, analyzer: SensitivityAnalyzer):
        """Test: Identifiera tjänsteman."""
        text = "Socialsekreterare Anna Andersson har handlagt ärendet."

        role, confidence = analyzer.identify_role(text, "Anna Andersson")

        assert role == PersonRole.PROFESSIONAL
        assert confidence >= 0.7

    def test_identify_reporter(self, analyzer: SensitivityAnalyzer):
        """Test: Identifiera anmälare."""
        text = "Orosanmälan inkom från Erik Eriksson angående barnets situation."

        role, confidence = analyzer.identify_role(text, "Erik Eriksson")

        assert role == PersonRole.REPORTER
        assert confidence >= 0.6

    def test_identify_third_party(self, analyzer: SensitivityAnalyzer):
        """Test: Identifiera tredje man."""
        text = "Granne Lisa Larsson berättade om situationen."

        role, confidence = analyzer.identify_role(text, "Lisa Larsson")

        assert role == PersonRole.THIRD_PARTY
        assert confidence >= 0.6

    def test_unknown_role(self, analyzer: SensitivityAnalyzer):
        """Test: Okänd roll."""
        text = "Kalle nämndes i dokumentet."

        role, confidence = analyzer.identify_role(text, "Kalle")

        # Kan vara UNKNOWN eller ha låg konfidens
        assert confidence < 0.7


class TestTextSplitting:
    """Tester för textuppdelning."""

    @pytest.fixture
    def analyzer(self) -> SensitivityAnalyzer:
        return SensitivityAnalyzer()

    def test_split_short_text(self, analyzer: SensitivityAnalyzer):
        """Test: Kort text delas inte."""
        text = "Detta är en kort text som inte behöver delas."

        sections = analyzer.split_into_sections(text)

        # Kan vara tom om under min_section_length
        assert len(sections) <= 1

    def test_split_paragraphs(self, analyzer: SensitivityAnalyzer):
        """Test: Stycken delas korrekt."""
        text = """Första stycket med tillräckligt mycket text för att överstiga minimum.

        Andra stycket med ännu mer text som också överstiger minimum för att bli en sektion.

        Tredje stycket som innehåller ytterligare information och överstiger minimum."""

        sections = analyzer.split_into_sections(text)

        assert len(sections) >= 1

    def test_split_respects_max_length(self, analyzer: SensitivityAnalyzer):
        """Test: Sektioner delas vid styckebrytningar."""
        paragraph = "Text i stycke. " * 50  # Ca 750 tecken
        text = f"{paragraph}\n\n{paragraph}\n\n{paragraph}"

        sections = analyzer.split_into_sections(text)

        # Ska dela vid styckebrytningar
        assert len(sections) >= 1


class TestOSLRulesLoading:
    """Tester för laddning av OSL-regler."""

    def test_load_default_rules(self):
        """Test: Ladda standardregler."""
        analyzer = SensitivityAnalyzer()
        rules = analyzer.osl_rules

        assert "categories" in rules
        assert "decision_rules" in rules
        assert "person_roles" in rules

    def test_rules_have_categories(self):
        """Test: Regler innehåller kategorier."""
        analyzer = SensitivityAnalyzer()
        rules = analyzer.osl_rules

        categories = rules.get("categories", {})
        assert "HEALTH" in categories
        assert "VIOLENCE" in categories


class TestLevelPriority:
    """Tester för nivåprioritet."""

    @pytest.fixture
    def analyzer(self) -> SensitivityAnalyzer:
        return SensitivityAnalyzer()

    def test_critical_highest(self, analyzer: SensitivityAnalyzer):
        """Test: CRITICAL har högst prioritet."""
        assert analyzer._level_priority("CRITICAL") > analyzer._level_priority("HIGH")
        assert analyzer._level_priority("HIGH") > analyzer._level_priority("MEDIUM")
        assert analyzer._level_priority("MEDIUM") > analyzer._level_priority("LOW")

    def test_unknown_level(self, analyzer: SensitivityAnalyzer):
        """Test: Okänd nivå ger 0."""
        assert analyzer._level_priority("UNKNOWN") == 0


class TestNameNearKeyword:
    """Tester för namn-nyckelords-närhet."""

    @pytest.fixture
    def analyzer(self) -> SensitivityAnalyzer:
        return SensitivityAnalyzer()

    def test_name_near_keyword(self, analyzer: SensitivityAnalyzer):
        """Test: Namn nära nyckelord identifieras."""
        text = "socialsekreterare anna har handlagt ärendet"

        result = analyzer._name_near_keyword(text, "anna", "socialsekreterare")

        assert result is True

    def test_name_far_from_keyword(self, analyzer: SensitivityAnalyzer):
        """Test: Namn långt från nyckelord."""
        text = "anna " + "x" * 200 + " socialsekreterare"

        result = analyzer._name_near_keyword(text, "anna", "socialsekreterare")

        assert result is False

    def test_name_not_in_text(self, analyzer: SensitivityAnalyzer):
        """Test: Namn finns inte i text."""
        text = "socialsekreterare har handlagt ärendet"

        result = analyzer._name_near_keyword(text, "anna", "socialsekreterare")

        assert result is False


class TestIntegration:
    """Integrationstester utan LLM."""

    @pytest.fixture
    def analyzer(self) -> SensitivityAnalyzer:
        analyzer = SensitivityAnalyzer()
        analyzer._llm_client = Mock()
        analyzer._llm_client.is_configured.return_value = False
        return analyzer

    def test_full_section_analysis(self, analyzer: SensitivityAnalyzer):
        """Test: Fullständig sektionsanalys."""
        text = """
        Klienten har en historia av depression och ångest. Hon har tidigare
        behandlats på BUP och går nu i terapi hos psykolog. Familjen har
        ekonomiska problem med skulder hos kronofogden.
        """

        assessment = analyzer.analyze_section(text)

        assert assessment.level in (SensitivityLevel.CRITICAL, SensitivityLevel.HIGH)
        assert assessment.confidence > 0

    def test_sensitive_document_section(self, analyzer: SensitivityAnalyzer):
        """Test: Känslig dokumentsektion."""
        text = """
        Orosanmälan inkom 2025-01-10 angående misstanke om våld i hemmet.
        Barnet berättade att pappa slagit mamma. Modern har ansökt om
        skyddat boende.
        """

        assessment = analyzer.analyze_section(text)

        assert assessment.level == SensitivityLevel.CRITICAL
        assert SensitivityCategory.VIOLENCE in [
            assessment.primary_category
        ] + assessment.secondary_categories
