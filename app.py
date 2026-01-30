"""Streamlit GUI för Menprövning.

Webbaserat gränssnitt för AI-assisterad menprövning enligt OSL.

Kör med: streamlit run app.py
"""

import json
import os
import tempfile
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Ladda miljövariabler från .env
load_dotenv()

# Sätt PYTHONPATH
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow.orchestrator import create_workflow
from src.core.models import SensitivityLevel, DocumentParty, RequesterContext, RequesterType, RelationType
from src.llm.requester_chat import RequesterChatSession


# === KONFIGURATION ===
# OpenRouter API-nyckel läses från .env-fil (säkrare än hårdkodning)
# Skapa .env-fil med: OPENROUTER_API_KEY=din-nyckel-här
DEFAULT_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


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
if "use_llm" not in st.session_state:
    st.session_state.use_llm = False
if "api_key" not in st.session_state:
    st.session_state.api_key = None
# Kravställningsdialog state
if "requester_context" not in st.session_state:
    st.session_state.requester_context = None
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "show_requester_dialog" not in st.session_state:
    st.session_state.show_requester_dialog = False
if "pending_file" not in st.session_state:
    st.session_state.pending_file = None
if "pending_text" not in st.session_state:
    st.session_state.pending_text = None

# CSS för bättre utseende - optimerad för större textvisning
st.markdown("""
<style>
    /* Använd mer av skärmen */
    .block-container {
        max-width: 95% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
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
    /* Synkroniserade textpaneler */
    .sync-scroll-container {
        display: flex;
        gap: 1rem;
        width: 100%;
    }
    .sync-panel {
        flex: 1;
        height: 70vh;
        overflow-y: auto;
        padding: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .sync-panel-original {
        background-color: #f5f5f5;
        border-left: 4px solid #9e9e9e;
    }
    .sync-panel-masked {
        background-color: #fffde7;
        border-left: 4px solid #ffc107;
    }
    .masked-text {
        background-color: #fffde7;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
        height: 70vh;
        overflow-y: auto;
    }
    .original-text {
        background-color: #f5f5f5;
        border-left: 4px solid #9e9e9e;
        padding: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
        height: 70vh;
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
            value=True,  # Aktiverad med giltig API-nyckel
            help="Ger mer exakt analys men kräver API-nyckel och tar längre tid"
        )

        # Visa LLM-status
        if use_llm and api_key:
            st.success("✅ LLM är aktiverat och redo för analys")
        elif use_llm and not api_key:
            st.warning("⚠️ LLM är aktiverat men ingen API-nyckel är konfigurerad")
        else:
            st.info("ℹ️ LLM är avstängt - endast regelbaserad analys kommer att användas")

        # Analysalternativ
        analyze_all = st.checkbox(
            "Analysera hela dokumentet",
            value=True,
            help="Om avmarkerad analyseras max 50 sektioner (snabbare)"
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

    # Huvudinnehåll - Visa kravställningsdialog eller vanliga tabbar
    if st.session_state.show_requester_dialog:
        display_requester_dialog(api_key, use_llm, masking_style, analyze_all)
    else:
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
                        "🔍 Starta kravställning",
                        type="primary",
                        use_container_width=True,
                        key="analyze_doc"
                    )

                if analyze_button:
                    # Spara filen och starta kravställningsdialog
                    st.session_state.pending_file = uploaded_file.getvalue()
                    st.session_state.source_name = uploaded_file.name
                    start_requester_dialog(api_key)
                    st.rerun()

        # Tab 2: Textanalys
        with tab2:
            st.subheader("Klistra in text")

            text_input = st.text_area(
                "Text att analysera",
                height=200,
                placeholder="Klistra in text från ett dokument här...",
            )

            if text_input:
                if st.button("🔍 Starta kravställning", type="primary", key="analyze_text"):
                    # Spara texten och starta kravställningsdialog
                    st.session_state.pending_text = text_input
                    st.session_state.source_name = "Inklistrad text"
                    start_requester_dialog(api_key)
                    st.rerun()

    # Visa sparade resultat
    if st.session_state.analysis_result is not None:
        display_results(st.session_state.analysis_result, st.session_state.source_name)


def start_requester_dialog(api_key: str):
    """Starta kravställningsdialogen."""
    st.session_state.chat_session = RequesterChatSession(api_key=api_key if api_key else None)
    st.session_state.chat_messages = []
    st.session_state.show_requester_dialog = True
    st.session_state.requester_context = None

    # Lägg till första meddelandet
    initial_msg = st.session_state.chat_session.start()
    st.session_state.chat_messages.append({"role": "assistant", "content": initial_msg})


def display_requester_dialog(api_key, use_llm, masking_style, analyze_all):
    """Visa kravställningsdialogen som en chatt."""
    st.subheader("💬 Kravställning")
    st.caption("Svara på frågorna för att anpassa menprövningen till beställaren.")

    # Visa chatthistorik
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            if msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg["content"])

    # Kolla om dialogen är klar
    if st.session_state.chat_session and st.session_state.chat_session.is_complete:
        st.success("✅ Kravställning klar!")
        st.session_state.requester_context = st.session_state.chat_session.get_context()

        # Visa sammanfattning
        ctx = st.session_state.requester_context
        if ctx:
            with st.expander("📋 Kravställning - sammanfattning", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Beställartyp:** {_translate_requester_type(ctx.requester_type)}")
                    st.markdown(f"**Relation:** {_translate_relation_type(ctx.relation_type)}")
                with col2:
                    st.markdown(f"**Syfte:** {ctx.purpose or 'Ej angivet'}")
                    st.markdown(f"**Maskeringsnivå:** {_translate_strictness(ctx.get_masking_strictness())}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Starta analys", type="primary", use_container_width=True):
                run_analysis_with_context(api_key, use_llm, masking_style, analyze_all)
        with col2:
            if st.button("🔄 Börja om", use_container_width=True):
                reset_requester_dialog()
                st.rerun()
    else:
        # Fritext-input
        user_input = st.chat_input("Skriv ditt svar...")
        if user_input:
            process_chat_input(user_input)

        # Avbryt-knapp
        st.markdown("---")
        if st.button("❌ Avbryt", type="secondary"):
            reset_requester_dialog()
            st.rerun()


def process_chat_input(user_input: str):
    """Bearbeta användarens chattinput."""
    if not st.session_state.chat_session:
        return

    # Lägg till användarens meddelande
    st.session_state.chat_messages.append({"role": "user", "content": user_input})

    # Få svar från chattsessionen
    response = st.session_state.chat_session.chat(user_input)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})

    st.rerun()


def reset_requester_dialog():
    """Återställ kravställningsdialogen."""
    st.session_state.show_requester_dialog = False
    st.session_state.chat_session = None
    st.session_state.chat_messages = []
    st.session_state.requester_context = None
    st.session_state.pending_file = None
    st.session_state.pending_text = None


def run_analysis_with_context(api_key, use_llm, masking_style, analyze_all):
    """Kör analysen med kravställningskontext."""
    ctx = st.session_state.requester_context

    # Hämta personnummer från kontext om tillgängligt
    requester_ssn = ctx.requester_ssn if ctx else None

    if st.session_state.pending_file:
        # Skapa temporär fil
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(st.session_state.pending_file)
            tmp_path = tmp.name

        try:
            analyze_document_with_context(
                tmp_path,
                api_key,
                use_llm,
                masking_style,
                requester_ssn,
                analyze_all,
                ctx
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    elif st.session_state.pending_text:
        analyze_text_with_context(
            st.session_state.pending_text,
            api_key,
            use_llm,
            masking_style,
            requester_ssn,
            analyze_all,
            ctx
        )

    # Återställ dialog-state
    st.session_state.show_requester_dialog = False
    st.session_state.pending_file = None
    st.session_state.pending_text = None


def analyze_document_with_context(tmp_path, api_key, use_llm, masking_style, requester_ssn, analyze_all, ctx):
    """Analysera dokument med kravställningskontext."""
    with st.spinner("Analyserar dokument... Detta kan ta några minuter."):
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Skapar workflow med kravställning...")
        progress_bar.progress(10)

        workflow = create_workflow(
            api_key=api_key if use_llm else None,
            use_llm=use_llm and bool(api_key),
            masking_style=masking_style,
            analyze_all_sections=analyze_all,
            requester_context=ctx,  # Skicka med kontext
        )

        status_text.text("Extraherar text från PDF...")
        progress_bar.progress(20)

        result = workflow.process_document(
            document_path=tmp_path,
            requester_ssn=requester_ssn,
            requester_context=ctx,
        )

        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()

    st.session_state.analysis_result = result
    st.session_state.use_llm = use_llm
    st.session_state.api_key = api_key
    st.rerun()


def analyze_text_with_context(text, api_key, use_llm, masking_style, requester_ssn, analyze_all, ctx):
    """Analysera text med kravställningskontext."""
    with st.spinner("Analyserar text..."):
        workflow = create_workflow(
            api_key=api_key if use_llm else None,
            use_llm=use_llm and bool(api_key),
            masking_style=masking_style,
            analyze_all_sections=analyze_all,
            requester_context=ctx,
        )

        result = workflow.process_text(
            text=text,
            document_id="text_input",
            requester_ssn=requester_ssn,
            requester_context=ctx,
        )

    st.session_state.analysis_result = result
    st.session_state.use_llm = use_llm
    st.session_state.api_key = api_key
    st.rerun()


def _translate_requester_type(req_type: RequesterType) -> str:
    """Översätt RequesterType till svenska."""
    translations = {
        RequesterType.SUBJECT_SELF: "Den enskilde själv",
        RequesterType.PARENT_1: "Förälder",
        RequesterType.PARENT_2: "Förälder",
        RequesterType.CHILD_OVER_15: "Barn över 15 år",
        RequesterType.LEGAL_GUARDIAN: "Vårdnadshavare",
        RequesterType.OTHER_PARTY: "Annan part",
        RequesterType.AUTHORITY: "Myndighet",
        RequesterType.PUBLIC: "Allmänheten",
    }
    return translations.get(req_type, str(req_type))


def _translate_relation_type(rel_type: RelationType) -> str:
    """Översätt RelationType till svenska."""
    translations = {
        RelationType.SELF: "Ärendet gäller beställaren själv",
        RelationType.PARENT: "Förälder till den ärendet gäller",
        RelationType.CHILD: "Barn till den ärendet gäller",
        RelationType.SPOUSE: "Make/maka/sambo",
        RelationType.SIBLING: "Syskon",
        RelationType.OTHER_RELATIVE: "Annan släkting",
        RelationType.LEGAL_REPRESENTATIVE: "Juridiskt ombud",
        RelationType.AUTHORITY_REPRESENTATIVE: "Myndighetsperson",
        RelationType.NO_RELATION: "Ingen direkt relation",
    }
    return translations.get(rel_type, str(rel_type))


def _translate_strictness(strictness: str) -> str:
    """Översätt maskeringsnivå till svenska."""
    translations = {
        "STRICT": "🔒 Strikt (allmänheten)",
        "MODERATE": "🔓 Måttlig (viss partsinsyn)",
        "RELAXED": "✅ Utökad partsinsyn",
    }
    return translations.get(strictness, strictness)


def analyze_document(uploaded_file, api_key, use_llm, masking_style, requester_ssn, analyze_all=True):
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
            llm_status = st.empty()

            status_text.text("Skapar workflow...")
            progress_bar.progress(10)

            workflow = create_workflow(
                api_key=api_key if use_llm else None,
                use_llm=use_llm and bool(api_key),
                masking_style=masking_style,
                analyze_all_sections=analyze_all,
            )

            status_text.text("Extraherar text från PDF...")
            progress_bar.progress(20)

            # Kör analys
            result = workflow.process_document(
                document_path=tmp_path,
                requester_ssn=requester_ssn if requester_ssn else None,
            )

            # Visa LLM-status om LLM användes
            if use_llm and api_key:
                llm_status.success("✅ LLM-analys slutförd")
            else:
                llm_status.info("ℹ️ Regelbaserad analys slutförd")

            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()

        # Spara resultat i session state
        st.session_state.analysis_result = result
        st.session_state.source_name = uploaded_file.name
        st.session_state.use_llm = use_llm
        st.session_state.api_key = api_key
        st.rerun()

    finally:
        # Rensa temporär fil
        Path(tmp_path).unlink(missing_ok=True)


def analyze_text(text, api_key, use_llm, masking_style, requester_ssn, analyze_all=True):
    """Analysera inklistrad text."""

    with st.spinner("Analyserar text..."):
        workflow = create_workflow(
            api_key=api_key if use_llm else None,
            use_llm=use_llm and bool(api_key),
            masking_style=masking_style,
            analyze_all_sections=analyze_all,
        )

        result = workflow.process_text(
            text=text,
            document_id="text_input",
            requester_ssn=requester_ssn if requester_ssn else None,
        )

        # Visa LLM-status om LLM användes
        if use_llm and api_key:
            st.success("✅ LLM-analys slutförd")
        else:
            st.info("ℹ️ Regelbaserad analys slutförd")

    # Spara resultat i session state
    st.session_state.analysis_result = result
    st.session_state.source_name = "Inklistrad text"
    st.session_state.use_llm = use_llm
    st.session_state.api_key = api_key
    st.rerun()


def display_results(result, source_name):
    """Visa analysresultat."""

    st.divider()
    st.header("📊 Analysresultat")
    st.caption(f"Källa: {source_name}")

    # Översta raden - nyckeltal
    col1, col2, col3, col4, col5 = st.columns(5)

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

    with col5:
        # Visa analysmetod
        if st.session_state.use_llm and st.session_state.api_key:
            st.markdown("**Analysmetod**")
            st.markdown('<span style="color: #4CAF50; font-weight: bold;">🤖 LLM</span>', unsafe_allow_html=True)
        else:
            st.markdown("**Analysmetod**")
            st.markdown('<span style="color: #2196F3; font-weight: bold;">📊 Regelbaserad</span>', unsafe_allow_html=True)

    # Visa analysomfattning
    sections_analyzed = result.statistics.get("assessments", {}).get("total", len(result.assessments))
    doc_chars = result.statistics.get("document", {}).get("characters", len(result.original_text))
    st.info(f"📊 **Analysstatistik:** {sections_analyzed} sektioner analyserade | {doc_chars:,} tecken | Hela dokumentet maskerades (NER på 100%)")

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
        ["Sida vid sida (synkad)", "Endast maskerad", "Endast original"],
        horizontal=True,
        key="view_mode"
    )

    if view_mode == "Sida vid sida (synkad)":
        # Synkroniserad scrollning med isolerad HTML-komponent
        import streamlit.components.v1 as components

        original_html = _escape_html(result.original_text)
        masked_html = _escape_html(result.masked_text)

        # Komplett HTML med inbyggd JavaScript och toggle
        sync_component = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
                .container {{ display: flex; gap: 1rem; height: calc(100vh - 50px); }}
                .panel-wrapper {{ flex: 1; display: flex; flex-direction: column; }}
                .panel-header {{
                    font-weight: bold;
                    padding: 0.5rem;
                    background: #f0f0f0;
                    border-bottom: 1px solid #ddd;
                }}
                .panel {{
                    flex: 1;
                    overflow-y: auto;
                    padding: 1rem;
                    font-family: monospace;
                    font-size: 13px;
                    line-height: 1.6;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                .panel-original {{ background: #f5f5f5; border-left: 4px solid #9e9e9e; }}
                .panel-masked {{ background: #fffde7; border-left: 4px solid #ffc107; }}
                .controls {{
                    padding: 0.5rem;
                    background: #e3f2fd;
                    border-bottom: 1px solid #90caf9;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }}
                .controls label {{ cursor: pointer; user-select: none; }}
                .sync-indicator {{
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    margin-left: 0.5rem;
                }}
                .sync-on {{ background: #4caf50; }}
                .sync-off {{ background: #9e9e9e; }}
            </style>
        </head>
        <body>
            <div class="controls">
                <label>
                    <input type="checkbox" id="syncToggle" checked>
                    🔗 Synkroniserad scrollning
                </label>
                <span id="syncIndicator" class="sync-indicator sync-on"></span>
            </div>
            <div class="container">
                <div class="panel-wrapper">
                    <div class="panel-header">Original</div>
                    <div id="panel1" class="panel panel-original">{original_html}</div>
                </div>
                <div class="panel-wrapper">
                    <div class="panel-header">Maskerad</div>
                    <div id="panel2" class="panel panel-masked">{masked_html}</div>
                </div>
            </div>
            <script>
                const panel1 = document.getElementById('panel1');
                const panel2 = document.getElementById('panel2');
                const toggle = document.getElementById('syncToggle');
                const indicator = document.getElementById('syncIndicator');
                let isSyncing = false;
                let syncEnabled = true;

                function syncScroll(source, target) {{
                    if (!syncEnabled || isSyncing) return;
                    isSyncing = true;
                    const maxScroll = source.scrollHeight - source.clientHeight;
                    if (maxScroll > 0) {{
                        const ratio = source.scrollTop / maxScroll;
                        target.scrollTop = ratio * (target.scrollHeight - target.clientHeight);
                    }}
                    requestAnimationFrame(() => {{ isSyncing = false; }});
                }}

                panel1.addEventListener('scroll', () => syncScroll(panel1, panel2));
                panel2.addEventListener('scroll', () => syncScroll(panel2, panel1));

                toggle.addEventListener('change', (e) => {{
                    syncEnabled = e.target.checked;
                    indicator.className = 'sync-indicator ' + (syncEnabled ? 'sync-on' : 'sync-off');
                }});
            </script>
        </body>
        </html>
        """

        components.html(sync_component, height=700, scrolling=False)

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

    # Rensa filnamn (ta bort .pdf etc.)
    clean_name = Path(source_name).stem if source_name else "dokument"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "📄 Ladda ner maskerad text",
            data=result.masked_text,
            file_name=f"maskerad_{clean_name}.txt",
            mime="text/plain",
        )

    with col2:
        # JSON-export med fullständig statistik
        from collections import Counter
        entity_types = Counter(e.type.value for e in result.entities)
        category_counts = Counter(a.primary_category.value for a in result.assessments) if result.assessments else {}

        masked = result.masking_result.statistics.get("masked_count", 0)
        released = result.masking_result.statistics.get("released_count", 0)
        total = masked + released

        # Konvertera DocumentParty-objekt till dict för export
        def party_to_dict(party):
            return {
                "party_id": party.party_id,
                "namn": party.name,
                "roll": party.role,
                "relation": party.relation,
                "är_minderårig": party.is_minor,
                "aliaser": party.aliases,
            }
        
        export_data = {
            "metadata": {
                "källa": source_name,
                "exporterad": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "analysresultat": {
                "övergripande_känslighet": result.overall_sensitivity.value,
                "bearbetningstid_sekunder": round(result.processing_time_ms / 1000, 1),
                "antal_tecken": len(result.original_text),
                "antal_sektioner_analyserade": len(result.assessments),
            },
            "entiteter": {
                "totalt": len(result.entities),
                "per_typ": dict(entity_types),
            },
            "maskering": {
                "antal_maskerade": masked,
                "antal_släppta": released,
                "maskerings_procent": round(masked / total * 100, 1) if total > 0 else 0,
            },
            "känslighetskategorier": dict(category_counts),
            "maskerade_entiteter": [
                {
                    "original": e.get("original", ""),
                    "ersättning": e.get("replacement", ""),
                    "typ": e.get("type", ""),
                }
                for e in result.masking_result.masked_entities[:100]
            ],
        }
        
        # Lägg till partsinformation om tillgängligt
        if hasattr(result, 'parties') and result.parties:
            export_data["parter"] = {
                "totalt": len(result.parties),
                "detaljer": [party_to_dict(party) for party in result.parties],
            }
        st.download_button(
            "📊 Ladda ner rapport (JSON)",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"rapport_{clean_name}.json",
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

        # Visualisering av partsberoenden (om tillgängligt)
        if hasattr(result, 'parties') and result.parties:
            st.divider()
            st.subheader("👥 Partsberoenden och relationer")
            
            # Kontrollera om det finns tillräckligt med parter för att visa ett nätverk
            
            # Alltid visa nätverk om det finns parter (även om inga relationer hittades)
            if len(result.parties) >= 1:
                # Skapa ett interaktivt nätverksdiagram med vis.js
                import streamlit.components.v1 as components
                
                # Generera noder och länkar för visualisering
                nodes = []
                edges = []
                
                # Färgkoder för olika roller
                role_colors = {
                    "SUBJECT": "#FF6B6B",      # Röd för huvudperson
                    "REQUESTER": "#4ECDC4",     # Turkos för beställare
                    "REQUESTER_CHILD": "#45B7D1", # Ljusblå för beställarens barn
                    "REPORTER": "#FFA07A",      # Orange för anmälare
                    "THIRD_PARTY": "#98D8C8",   # Grön för tredje man
                    "PROFESSIONAL": "#A5A5A5",  # Grå för tjänstemän
                    "UNKNOWN": "#D4D4D4",       # Ljusgrå för okända
                }
                
                # Skapa noder
                for party in result.parties:
                    role_color = role_colors.get(party.role, "#D4D4D4")
                    
                    # Rollnamn på svenska
                    role_swedish = {
                        "SUBJECT": "Huvudperson",
                        "REQUESTER": "Beställare",
                        "REQUESTER_CHILD": "Beställarens barn",
                        "REPORTER": "Anmälare",
                        "THIRD_PARTY": "Tredje man",
                        "PROFESSIONAL": "Tjänsteman",
                        "UNKNOWN": "Okänd",
                    }.get(party.role, party.role)
                    
                    nodes.append({
                        "id": party.party_id,
                        "label": party.name or f"Part {party.party_id}",
                        "title": f"{party.name or f'Part {party.party_id}'}\nRoll: {role_swedish}\nRelation: {party.relation or 'Okänd'}",
                        "color": role_color,
                        "shape": "circle" if party.is_minor else "dot",
                        "size": 25 if party.is_minor else 20,
                    })
                
                # Skapa länkar baserat på relationer
                # Förbättrad logik för att skapa meningsfulla relationer
                relation_map = {
                    "mamma": "barn",
                    "pappa": "barn", 
                    "morfar": "barnbarn",
                    "farmor": "barnbarn",
                    "barn": "förälder",
                    "granne": "granne",
                }
                
                # Förbättrad relationslogik: Skapa meningsfulla familjerelationer
                # Istället för att koppla alla parter med relationer till alla andra,
                # skapar vi logiska familjestrukturer
                
                # Först, identifiera potentiella föräldrar och barn
                parents = []
                children = []
                others = []
                
                for party in result.parties:
                    if party.relation in ["mamma", "pappa", "förälder"]:
                        parents.append(party)
                    elif party.relation in ["barn", "son", "dotter"]:
                        children.append(party)
                    elif party.relation in ["morfar", "farmor", "farfar", "mormor"]:
                        others.append(party)  # Förfäder
                    else:
                        others.append(party)
                
                # Skapa familjerelationer
                # 1. Föräldrar -> Barn
                for parent in parents:
                    for child in children:
                        edges.append({
                            "from": parent.party_id,
                            "to": child.party_id,
                            "label": parent.relation or "förälder",
                            "arrows": "to",
                            "color": {
                                "color": "#4CAF50",  # Grön för familjerelationer
                                "highlight": "#2E7D32",
                            },
                            "smooth": {"enabled": True},
                            "dashes": False,
                        })
                        
                        # Omvänd relation
                        reverse_relation = relation_map.get(parent.relation.lower(), "barn")
                        edges.append({
                            "from": child.party_id,
                            "to": parent.party_id,
                            "label": reverse_relation,
                            "arrows": "to",
                            "color": {
                                "color": "#4CAF50",
                                "highlight": "#2E7D32",
                            },
                            "smooth": {"enabled": True},
                            "dashes": True,
                        })
                
                # 2. Förfäder -> Föräldrar (och barnbarn)
                for elder in others:
                    if elder.relation in ["morfar", "farmor", "farfar", "mormor"]:
                        # Koppla förfäder till föräldrar
                        for parent in parents:
                            edges.append({
                                "from": elder.party_id,
                                "to": parent.party_id,
                                "label": elder.relation,
                                "arrows": "to",
                                "color": {
                                    "color": "#2196F3",  # Blå för förfäder
                                    "highlight": "#0B7FDA",
                                },
                                "smooth": {"enabled": True},
                                "dashes": False,
                            })
                            
                            # Omvänd relation
                            reverse_relation = relation_map.get(elder.relation.lower(), "barnbarn")
                            edges.append({
                                "from": parent.party_id,
                                "to": elder.party_id,
                                "label": reverse_relation,
                                "arrows": "to",
                                "color": {
                                    "color": "#2196F3",
                                    "highlight": "#0B7FDA",
                                },
                                "smooth": {"enabled": True},
                                "dashes": True,
                            })
                        
                        # Koppla förfäder direkt till barnbarn också
                        for child in children:
                            edges.append({
                                "from": elder.party_id,
                                "to": child.party_id,
                                "label": "morfar" if "mor" in elder.relation.lower() else "farfar",
                                "arrows": "to",
                                "color": {
                                    "color": "#9C27B0",  # Lila för direkt förfäder-barnbarn relation
                                    "highlight": "#7B1FA2",
                                },
                                "smooth": {"enabled": True},
                                "dashes": False,
                            })
                
                # 3. Specifika relationer (grannar, etc.)
                for party in result.parties:
                    if party.relation in ["granne", "släkting", "vän"]:
                        # Koppla till huvudperson (första parten som antas vara huvudperson)
                        if result.parties:
                            main_party = result.parties[0]  # Antagande: första parten är huvudperson
                            if main_party.party_id != party.party_id:
                                edges.append({
                                    "from": party.party_id,
                                    "to": main_party.party_id,
                                    "label": party.relation,
                                    "arrows": "to",
                                    "color": {
                                        "color": "#FF9800",  # Orange för andra relationer
                                        "highlight": "#F57C00",
                                    },
                                    "smooth": {"enabled": True},
                                    "dashes": False,
                                })
                                
                                # Omvänd relation
                                edges.append({
                                    "from": main_party.party_id,
                                    "to": party.party_id,
                                    "label": party.relation,
                                    "arrows": "to",
                                    "color": {
                                        "color": "#FF9800",
                                        "highlight": "#F57C00",
                                    },
                                    "smooth": {"enabled": True},
                                    "dashes": True,
                                })
                                break  # Endast en relation per part för att undvika för många länkar
            
            # HTML för nätverksvisualisering
            network_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Partsberoenden</title>
                <!-- Load vis.js from CDN -->
                <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
                <style type="text/css">
                    #network {{
                        width: 100%;
                        height: 500px;
                        border: 1px solid lightgray;
                        border-radius: 5px;
                    }}
                    /* Ensure container is visible */
                    body, html {{
                        margin: 0;
                        padding: 0;
                        height: 100%;
                        overflow: hidden;
                    }}
                </style>
            </head>
            <body>
                <div id="network"></div>
                <script type="text/javascript">
                    // Debug: Log when script starts
                    console.log("Starting network visualization...");
                    
                    try {{
                        const nodes = new vis.DataSet({json.dumps(nodes, ensure_ascii=False)});
                        const edges = new vis.DataSet({json.dumps(edges, ensure_ascii=False)});
                        
                        console.log("Nodes loaded:", nodes.length);
                        console.log("Edges loaded:", edges.length);
                        
                        const container = document.getElementById("network");
                        if (!container) {{
                            console.error("Container element not found!");
                        }} else {{
                            console.log("Container found:", container);
                        }}
                        
                        const data = {{ nodes: nodes, edges: edges }};
                        
                        // Simplified options for better compatibility
                        const options = {{
                            nodes: {{
                                font: {{ size: 14, face: "Arial" }},
                                borderWidth: 2,
                                shadow: true,
                            }},
                            edges: {{
                                font: {{ size: 12, align: "middle" }},
                                arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
                                smooth: {{ enabled: true }},
                            }},
                            physics: {{
                                enabled: true,
                                barnesHut: {{
                                    gravitationalConstant: -80000,
                                    centralGravity: 0.3,
                                    springLength: 200,
                                    springConstant: 0.04,
                                    damping: 0.09,
                                    avoidOverlap: 0.1,
                                }},
                                minVelocity: 0.75,
                            }},
                            interaction: {{ hover: true, tooltipDelay: 200 }},
                        }};
                        
                        // Create network with timeout to ensure DOM is ready
                        setTimeout(function() {{
                            const network = new vis.Network(container, data, options);
                            console.log("Network created:", network);
                            
                            network.on("click", function(params) {{
                                console.log("Network clicked:", params);
                            }});
                            
                            // Fit network to container
                            network.fit();
                            network.redraw();
                        }}, 100);
                        
                    }} catch (error) {{
                        console.error("Error creating network:", error);
                    }}
                </script>
            </body>
            </html>
            """
            
            # Add debug information
            st.caption(f"🔍 Visualisering av {len(result.parties)} parter med {len(edges)} relationer")
            
            # Show fallback message if no edges
            if len(edges) == 0 and len(result.parties) > 1:
                st.warning("⚠️ Inga relationer kunde fastställas mellan parterna. Visar ändå nätverksstruktur.")
            
            components.html(network_html, height=550)
            
            # Add troubleshooting help
            with st.expander("❓ Felsökning av visualisering"):
                st.markdown("""
                **Om visualiseringen är tom, prova:**
                
                1. **Kontrollera internetanslutning** - vis.js laddas från CDN
                2. **Öppna browserkonsolen** (F12) för felmeddelanden
                3. **Uppdatera sidan** - Ibland hjälper det
                4. **Prova annan webbläsare** - Chrome/Firefox rekommenderas
                
                **Teknisk information:**
                - Noder: {len(nodes)}
                - Kanter: {len(edges)}
                - Parter: {len(result.parties)}
                - Parter med relationer: {sum(1 for p in result.parties if p.relation)}
                """)
        else:
            st.info("📊 Inga parter identifierades i dokumentet.")

        # Visa partsinformation i tabellform
        with st.expander("📋 Detaljerad partsinformation"):
                for party in result.parties:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        role_swedish = {
                            "SUBJECT": "Huvudperson",
                            "REQUESTER": "Beställare", 
                            "REQUESTER_CHILD": "Beställarens barn",
                            "REPORTER": "Anmälare",
                            "THIRD_PARTY": "Tredje man",
                            "PROFESSIONAL": "Tjänsteman",
                            "UNKNOWN": "Okänd",
                        }.get(party.role, party.role)
                        
                        col1.markdown(f"**{party.name or f'Part {party.party_id}'}**")
                        col2.markdown(f"👤 {role_swedish}")
                        col3.markdown(f"🔗 {party.relation or 'Okänd relation'}")
                        
                        if party.aliases:
                            st.caption(f"Aliaser: {', '.join(party.aliases)}")
                        if party.is_minor:
                            st.caption("⚠️ Minderårig")


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
