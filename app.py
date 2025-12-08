"""Streamlit GUI for Menprovning.

Webbaserat granssnitt for AI-assisterad menprovning enligt OSL.

Kor med: streamlit run app.py
"""

import os
import tempfile
import time
from pathlib import Path

import streamlit as st

# Satt PYTHONPATH
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow.orchestrator import create_workflow, WorkflowConfig
from src.core.models import SensitivityLevel


# Sidkonfiguration
st.set_page_config(
    page_title="Menprovning",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS for battre utseende
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
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
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
    """Skapa HTML-badge for kanslighetsniva."""
    level_lower = level.lower()
    return f'<span class="sensitivity-{level_lower}">{level}</span>'


def main():
    """Huvudfunktion for Streamlit-appen."""

    # Header
    st.markdown('<p class="main-header">🔒 Menprovning</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">AI-assisterad bedomning enligt OSL kapitel 26</p>',
        unsafe_allow_html=True
    )

    # Sidebar - Konfiguration
    with st.sidebar:
        st.header("⚙️ Konfiguration")

        # API-nyckel
        api_key = st.text_input(
            "OpenRouter API-nyckel",
            value=os.getenv("OPENROUTER_API_KEY", ""),
            type="password",
            help="Kravs for LLM-baserad analys"
        )

        # LLM-installningar
        use_llm = st.checkbox(
            "Anvand LLM for analys",
            value=True,
            help="Ger mer exakt analys men tar langre tid"
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

        # Bestellarens personnummer
        st.divider()
        st.subheader("📋 Partsinsyn")
        requester_ssn = st.text_input(
            "Bestellarens personnummer",
            placeholder="YYYYMMDD-XXXX",
            help="Om bestellaren beggar ut sina egna handlingar"
        )

        # Information
        st.divider()
        st.info(
            "**Om verktyget**\n\n"
            "Detta verktyg hjalper till med menprovning enligt "
            "Offentlighets- och sekretesslagen (OSL) kapitel 26.\n\n"
            "⚠️ Verktyget ger forslag - manuell granskning kravs alltid."
        )

    # Huvudinnehall
    tab1, tab2 = st.tabs(["📄 Dokumentanalys", "✏️ Textanalys"])

    # Tab 1: Dokumentanalys
    with tab1:
        st.subheader("Ladda upp dokument")

        uploaded_file = st.file_uploader(
            "Valj en PDF-fil",
            type=["pdf"],
            help="Ladda upp en socialtjanstakt for analys"
        )

        if uploaded_file:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ Fil uppladdad: {uploaded_file.name}")
            with col2:
                analyze_button = st.button("🔍 Analysera", type="primary", use_container_width=True)

            if analyze_button:
                analyze_document(uploaded_file, api_key, use_llm, masking_style, requester_ssn)

    # Tab 2: Textanalys
    with tab2:
        st.subheader("Klistra in text")

        text_input = st.text_area(
            "Text att analysera",
            height=200,
            placeholder="Klistra in text fran ett dokument har...",
        )

        if text_input:
            if st.button("🔍 Analysera text", type="primary"):
                analyze_text(text_input, api_key, use_llm, masking_style, requester_ssn)


def analyze_document(uploaded_file, api_key, use_llm, masking_style, requester_ssn):
    """Analysera ett uppladdat dokument."""

    # Spara temporart
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        with st.spinner("Analyserar dokument... Detta kan ta ett par minuter."):
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

            status_text.text("Extraherar text fran PDF...")
            progress_bar.progress(20)

            # Kor analys
            start_time = time.time()
            result = workflow.process_document(
                document_path=tmp_path,
                requester_ssn=requester_ssn if requester_ssn else None,
            )

            progress_bar.progress(100)
            status_text.empty()

        # Visa resultat
        display_results(result, uploaded_file.name)

    finally:
        # Rensa temporar fil
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

    display_results(result, "Inklistrad text")


def display_results(result, source_name):
    """Visa analysresultat."""

    st.divider()
    st.header("📊 Analysresultat")

    # Oversta raden - nyckelmattal
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
        st.markdown(f"**Kanslighetsniva**")
        st.markdown(get_sensitivity_badge(level), unsafe_allow_html=True)

    # Detaljerad statistik
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Entitetstyper")
        entity_stats = result.statistics.get("entities", {}).get("by_type", {})
        if entity_stats:
            for etype, count in sorted(entity_stats.items(), key=lambda x: -x[1]):
                st.write(f"• **{etype}**: {count}")
        else:
            st.write("Inga entiteter hittades")

    with col2:
        st.subheader("📋 Kanslighetskategorier")
        if result.assessments:
            from collections import Counter
            categories = Counter(a.primary_category.value for a in result.assessments)
            for cat, count in categories.most_common(5):
                st.write(f"• **{cat}**: {count}")
        else:
            st.write("Inga bedomningar gjordes")

    # Text-jamforelse
    st.divider()
    st.subheader("📝 Textjamforelse")

    view_mode = st.radio(
        "Visningslage",
        ["Sida vid sida", "Endast maskerad", "Endast original"],
        horizontal=True
    )

    if view_mode == "Sida vid sida":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Original**")
            st.markdown(
                f'<div class="original-text">{result.original_text[:5000]}{"..." if len(result.original_text) > 5000 else ""}</div>',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown("**Maskerad**")
            st.markdown(
                f'<div class="masked-text">{result.masked_text[:5000]}{"..." if len(result.masked_text) > 5000 else ""}</div>',
                unsafe_allow_html=True
            )
    elif view_mode == "Endast maskerad":
        st.markdown(
            f'<div class="masked-text">{result.masked_text}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="original-text">{result.original_text}</div>',
            unsafe_allow_html=True
        )

    # Export
    st.divider()
    st.subheader("💾 Export")

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
        import json
        export_data = {
            "source": source_name,
            "overall_sensitivity": result.overall_sensitivity.value,
            "entity_count": len(result.entities),
            "masked_count": result.masking_result.statistics.get("masked_count", 0),
            "processing_time_ms": result.processing_time_ms,
            "masked_entities": result.masking_result.masked_entities[:50],  # Begransat
        }
        st.download_button(
            "📊 Ladda ner rapport (JSON)",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"rapport_{source_name}.json",
            mime="application/json",
        )

    with col3:
        # Visa maskerade entiteter
        if st.button("👁️ Visa maskerade entiteter"):
            st.json(result.masking_result.masked_entities[:20])


if __name__ == "__main__":
    main()
