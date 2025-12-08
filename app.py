"""Streamlit GUI för Menprövning.

Webbaserat gränssnitt för AI-assisterad menprövning enligt OSL.

Kör med: streamlit run app.py
"""

import json
import tempfile
import time
from pathlib import Path

import streamlit as st

# Sätt PYTHONPATH
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow.orchestrator import create_workflow
from src.core.models import SensitivityLevel


# === KONFIGURATION ===
DEFAULT_API_KEY = "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"


# Sidkonfiguration
st.set_page_config(
    page_title="Menprövning",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initiera session state
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "source_name" not in st.session_state:
    st.session_state.source_name = None

# CSS för bättre utseende
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .sensitivity-critical {
        background-color: #ff4b4b;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .sensitivity-high {
        background-color: #ffa500;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .sensitivity-medium {
        background-color: #ffcc00;
        color: black;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .sensitivity-low {
        background-color: #00cc66;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .masked-text {
        background-color: #fffde7;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 500px;
        overflow-y: auto;
    }
    .original-text {
        background-color: #f5f5f5;
        border-left: 4px solid #9e9e9e;
        padding: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 500px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)


def get_sensitivity_badge(level: str) -> str:
    """Skapa HTML-badge för känslighetsnivå."""
    level_lower = level.lower()
    level_swedish = {
        "critical": "KRITISK",
        "high": "HÖG",
        "medium": "MEDEL",
        "low": "LÅG",
    }.get(level_lower, level)
    return f'<span class="sensitivity-{level_lower}">{level_swedish}</span>'


def main():
    """Huvudfunktion för Streamlit-appen."""

    # Header
    st.markdown('<p class="main-header">🔒 Menprövning</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">AI-assisterad bedömning enligt OSL kapitel 26</p>',
        unsafe_allow_html=True
    )

    # Sidebar - Konfiguration
    with st.sidebar:
        st.header("⚙️ Inställningar")

        # API-nyckel (hårdkodad som default)
        api_key = st.text_input(
            "OpenRouter API-nyckel",
            value=DEFAULT_API_KEY,
            type="password",
            help="Krävs för LLM-baserad analys"
        )

        # LLM-inställningar
        use_llm = st.checkbox(
            "Använd LLM för analys",
            value=True,
            help="Ger mer exakt analys men tar längre tid"
        )

        # Maskeringsstil
        masking_style = st.selectbox(
            "Maskeringsstil",
            options=["brackets", "redacted", "placeholder", "anonymized"],
            format_func=lambda x: {
                "brackets": "[MASKERAT: TYP]",
                "redacted": "████████",
                "placeholder": "<TYP>",
                "anonymized": "Person A, B, C...",
            }.get(x, x)
        )

        # Beställarens personnummer
        st.divider()
        st.subheader("📋 Partsinsyn")
        requester_ssn = st.text_input(
            "Beställarens personnummer",
            placeholder="ÅÅÅÅMMDD-XXXX",
            help="Om beställaren begär ut sina egna handlingar"
        )

        # Information
        st.divider()
        st.info(
            "**Om verktyget**\n\n"
            "Detta verktyg hjälper till med menprövning enligt "
            "Offentlighets- och sekretesslagen (OSL) kapitel 26.\n\n"
            "⚠️ Verktyget ger förslag - manuell granskning krävs alltid."
        )

        # Rensa resultat-knapp
        if st.session_state.analysis_result is not None:
            st.divider()
            if st.button("🗑️ Rensa resultat", use_container_width=True):
                st.session_state.analysis_result = None
                st.session_state.source_name = None
                st.rerun()

    # Huvudinnehåll
    tab1, tab2 = st.tabs(["📄 Dokumentanalys", "✏️ Textanalys"])

    # Tab 1: Dokumentanalys
    with tab1:
        st.subheader("Ladda upp dokument")

        uploaded_file = st.file_uploader(
            "Välj en PDF-fil",
            type=["pdf"],
            help="Ladda upp en socialtjänstakt för analys"
        )

        if uploaded_file:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ Fil uppladdad: {uploaded_file.name}")
            with col2:
                analyze_button = st.button(
                    "🔍 Analysera",
                    type="primary",
                    use_container_width=True,
                    key="analyze_doc"
                )

            if analyze_button:
                analyze_document(uploaded_file, api_key, use_llm, masking_style, requester_ssn)

    # Tab 2: Textanalys
    with tab2:
        st.subheader("Klistra in text")

        text_input = st.text_area(
            "Text att analysera",
            height=200,
            placeholder="Klistra in text från ett dokument här...",
        )

        if text_input:
            if st.button("🔍 Analysera text", type="primary", key="analyze_text"):
                analyze_text(text_input, api_key, use_llm, masking_style, requester_ssn)

    # Visa sparade resultat
    if st.session_state.analysis_result is not None:
        display_results(st.session_state.analysis_result, st.session_state.source_name)


def analyze_document(uploaded_file, api_key, use_llm, masking_style, requester_ssn):
    """Analysera ett uppladdat dokument."""

    # Spara temporärt
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        with st.spinner("Analyserar dokument... Detta kan ta några minuter."):
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Skapar workflow...")
            progress_bar.progress(10)

            workflow = create_workflow(
                api_key=api_key if use_llm else None,
                use_llm=use_llm and bool(api_key),
                masking_style=masking_style,
            )

            status_text.text("Extraherar text från PDF...")
            progress_bar.progress(20)

            # Kör analys
            result = workflow.process_document(
                document_path=tmp_path,
                requester_ssn=requester_ssn if requester_ssn else None,
            )

            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()

        # Spara resultat i session state
        st.session_state.analysis_result = result
        st.session_state.source_name = uploaded_file.name
        st.rerun()

    finally:
        # Rensa temporär fil
        Path(tmp_path).unlink(missing_ok=True)


def analyze_text(text, api_key, use_llm, masking_style, requester_ssn):
    """Analysera inklistrad text."""

    with st.spinner("Analyserar text..."):
        workflow = create_workflow(
            api_key=api_key if use_llm else None,
            use_llm=use_llm and bool(api_key),
            masking_style=masking_style,
        )

        result = workflow.process_text(
            text=text,
            document_id="text_input",
            requester_ssn=requester_ssn if requester_ssn else None,
        )

    # Spara resultat i session state
    st.session_state.analysis_result = result
    st.session_state.source_name = "Inklistrad text"
    st.rerun()


def display_results(result, source_name):
    """Visa analysresultat."""

    st.divider()
    st.header("📊 Analysresultat")
    st.caption(f"Källa: {source_name}")

    # Översta raden - nyckeltal
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("⏱️ Tid", f"{result.processing_time_ms/1000:.1f}s")

    with col2:
        st.metric("🔍 Entiteter", len(result.entities))

    with col3:
        masked = result.masking_result.statistics.get("masked_count", 0)
        released = result.masking_result.statistics.get("released_count", 0)
        total = masked + released
        ratio = masked / total * 100 if total > 0 else 0
        st.metric("🔒 Maskerade", f"{masked} ({ratio:.0f}%)")

    with col4:
        level = result.overall_sensitivity.value
        st.markdown("**Känslighetsnivå**")
        st.markdown(get_sensitivity_badge(level), unsafe_allow_html=True)

    # Detaljerad statistik
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Entitetstyper")
        entity_stats = result.statistics.get("entities", {}).get("by_type", {})
        if entity_stats:
            for etype, count in sorted(entity_stats.items(), key=lambda x: -x[1]):
                # Översätt entitetstyper till svenska
                etype_swedish = {
                    "PERSON": "Person",
                    "SSN": "Personnummer",
                    "PHONE": "Telefon",
                    "EMAIL": "E-post",
                    "DATE": "Datum",
                    "ADDRESS": "Adress",
                    "ORG": "Organisation",
                    "LOCATION": "Plats",
                }.get(etype, etype)
                st.write(f"• **{etype_swedish}**: {count}")
        else:
            st.write("Inga entiteter hittades")

    with col2:
        st.subheader("📋 Känslighetskategorier")
        if result.assessments:
            from collections import Counter
            categories = Counter(a.primary_category.value for a in result.assessments)
            for cat, count in categories.most_common(5):
                # Översätt kategorier till svenska
                cat_swedish = {
                    "HEALTH": "Hälsa",
                    "MENTAL_HEALTH": "Psykisk hälsa",
                    "ADDICTION": "Missbruk",
                    "VIOLENCE": "Våld",
                    "FAMILY": "Familj",
                    "ECONOMY": "Ekonomi",
                    "HOUSING": "Boende",
                    "SEXUAL": "Sexuell",
                    "CRIMINAL": "Brott",
                    "NEUTRAL": "Neutral",
                }.get(cat, cat)
                st.write(f"• **{cat_swedish}**: {count}")
        else:
            st.write("Inga bedömningar gjordes")

    # Textjämförelse
    st.divider()
    st.subheader("📝 Textjämförelse")

    view_mode = st.radio(
        "Visningsläge",
        ["Sida vid sida", "Endast maskerad", "Endast original"],
        horizontal=True,
        key="view_mode"
    )

    if view_mode == "Sida vid sida":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Original**")
            st.markdown(
                f'<div class="original-text">{_escape_html(result.original_text[:5000])}{"..." if len(result.original_text) > 5000 else ""}</div>',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown("**Maskerad**")
            st.markdown(
                f'<div class="masked-text">{_escape_html(result.masked_text[:5000])}{"..." if len(result.masked_text) > 5000 else ""}</div>',
                unsafe_allow_html=True
            )
    elif view_mode == "Endast maskerad":
        st.markdown(
            f'<div class="masked-text">{_escape_html(result.masked_text)}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="original-text">{_escape_html(result.original_text)}</div>',
            unsafe_allow_html=True
        )

    # Export
    st.divider()
    st.subheader("💾 Exportera")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "📄 Ladda ner maskerad text",
            data=result.masked_text,
            file_name=f"maskerad_{source_name}.txt",
            mime="text/plain",
        )

    with col2:
        # JSON-export
        export_data = {
            "källa": source_name,
            "övergripande_känslighet": result.overall_sensitivity.value,
            "antal_entiteter": len(result.entities),
            "antal_maskerade": result.masking_result.statistics.get("masked_count", 0),
            "bearbetningstid_ms": result.processing_time_ms,
            "maskerade_entiteter": result.masking_result.masked_entities[:50],
        }
        st.download_button(
            "📊 Ladda ner rapport (JSON)",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"rapport_{source_name}.json",
            mime="application/json",
        )

    with col3:
        # Visa maskerade entiteter
        with st.expander("👁️ Visa maskerade entiteter"):
            if result.masking_result.masked_entities:
                for i, entity in enumerate(result.masking_result.masked_entities[:30]):
                    st.write(f"**{i+1}.** `{entity.get('original', '')}` → `{entity.get('replacement', '')}`")
                if len(result.masking_result.masked_entities) > 30:
                    st.caption(f"... och {len(result.masking_result.masked_entities) - 30} till")
            else:
                st.write("Inga entiteter maskerades")


def _escape_html(text: str) -> str:
    """Escape HTML-tecken i text."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


if __name__ == "__main__":
    main()
