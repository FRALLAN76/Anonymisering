# Menprövning

AI-assisterat verktyg för menprövning av socialtjänsthandlingar enligt Offentlighets- och sekretesslagen (OSL).

## Översikt

Detta verktyg hjälper handläggare inom socialtjänsten att bedöma vilka uppgifter i allmänna handlingar som ska maskeras vid utlämning, baserat på OSL kapitel 26 (socialtjänstsekretess).

### Funktioner

- **PDF-extraktion** - Extraherar text från PDF-dokument
- **Avancerad NER (Named Entity Recognition)** - Identifierar känsliga entiteter:
  - Personnummer (svenska format)
  - Telefonnummer
  - E-postadresser
  - Adresser
  - Datum och personnnamn
  - **Förbättrad svensk namnuppfattning** - Inkluderar ovanliga namn som "Sveinung"
  - **LLM-baserad kontextanalys** - Hittar namn som missats av traditionell NER
- **Känslighetsanalys** - LLM-baserad + nyckelordsbaserad bedömning enligt OSL-kategorier
- **Automatisk maskering** - Flera maskeringsstilar
- **Partsinsyn** - Stöd för att undanta beställarens egna uppgifter
- **Kravställningsdialog** - Chatbaserad dialog för att anpassa maskeringen till beställaren
- **Partsberoendevisualisering** - Interaktivt nätverksdiagram med familjerelationer
- **Webb-GUI** - Streamlit-baserat gränssnitt med LLM-statusindikatorer
- **REST API** - FastAPI för integration

## Nyheter och förbättringar

**Senaste versionen (v2.2) inkluderar:**

### Kravställningsdialog (NYTT!)
- **Chatbaserad kravställning** - Guidad dialog innan analys för att samla in information om beställaren
- **Snabbvalsknappar** - "Den enskilde själv", "Förälder", "Myndighet", "Allmänheten"
- **Dynamisk maskeringsnivå** - Maskeringen anpassas baserat på vem som begär handlingen:
  - **STRICT** (Allmänheten) - Maska allt utom tjänstemän och organisationer
  - **MODERATE** (Myndigheter) - Balanserad maskering
  - **RELAXED** (Partsinsyn) - Utökad insyn för den enskilde/vårdnadshavare
- **Samtyckeshantering** - Om samtycke finns kan mer information lämnas ut
- **LLM-stödd dialog** - Använder samma LLM som analysen för naturlig konversation

### NER-förbättringar
- **Utökade svenska namnlistor** - 100+ vanliga och ovanliga svenska namn
- **LLM-baserad kontextanalys** - Hittar namn som traditionell NER missar
- **Genitivformshantering** - Uppfattar "Sveinungs situation" som personnamn
- **Förbättrad BERT-integration** - Bättre samarbete mellan regex och BERT NER

### Partsanalys
- **Familjerelationsdetektering** - Automatisk identifiering av mammor, pappor, barn, etc.
- **Interaktiv visualisering** - Nätverksdiagram med vis.js
- **Färgkodade relationer** - Olika färger för olika relationstyper
- **Partsberoendemapping** - Visar vem som är relaterad till vem

### GUI-förbättringar
- **LLM-statusindikatorer** - Visar när LLM-analys körs
- **Förbättrad partsvisning** - Bättre tabelllayout och information
- **Bättre felhantering** - Tydligare meddelanden vid problem

### Tekniska förbättringar
- **JSON-serialiseringsfixar** - Korrekt hantering av specialtecken
- **Förbättrad minneshantering** - Bättre rensning av temporära objekt
- **Bättre testtäckning** - Utökade enhetstester

## Installation

### Krav

- Python 3.11+
- pip eller Poetry

### Snabbstart

```bash
# Klona repot
git clone https://github.com/[username]/menprovning.git
cd menprovning

# Skapa virtuell miljö
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# eller: .venv\Scripts\activate  # Windows

# Installera beroenden
pip install pymupdf pydantic requests streamlit fastapi uvicorn python-dotenv pytesseract

# För OCR-funktionalitet (valfritt), installera även Tesseract:
# Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-swe
# macOS: brew install tesseract tesseract-lang

# Kör GUI
streamlit run app.py
```

### Med Poetry (valfritt)

```bash
poetry install
poetry run streamlit run app.py
```

## Användning

### Webb-GUI (Streamlit)

```bash
streamlit run app.py
```

Öppna `http://localhost:8501` i din webbläsare.

**Exempel på partsberoendevisualisering:**

```
Sveinung (morfar)       Mormor Agnes (farmor)
       ↓                     ↓
     Agnes (mamma) ←→ Adrian (barn)
       ↑                     ↑
MIRA BORGNY (socialsekreterare)
```

Visualiseringen visar:
- **Gröna pilar** för förälder-barn relationer
- **Blå pilar** för förfäder-förälder relationer
- **Lila pilar** för direkt förfäder-barnbarn relationer
- **Orange pilar** för andra relationer (släktingar, professionella)

**Funktioner i GUI:t:**
- Ladda upp PDF-filer för analys
- Klistra in text direkt
- Konfigurera maskeringsstil
- **Kravställningsdialog** - Besvara frågor om beställaren innan analys:
  1. Vem begär handlingen? (enskilde, förälder, myndighet, allmänheten)
  2. Vilken relation har beställaren till den ärendet gäller?
  3. Vad är syftet med begäran?
  4. Finns samtycke?
- Se resultat med statistik och textjämförelse
- Exportera maskerad text och rapport
- **LLM-statusindikatorer** - Visar när LLM-analys körs
- **Partsberoendenvisualisering** - Interaktivt nätverk med familjerelationer
- **Förbättrad partsinformation** - Detaljerad tabell med roller och relationer

### REST API

```bash
uvicorn src.api.main:app --reload
```

API:t finns på `http://localhost:8000`.

**Endpoints:**

| Endpoint | Metod | Beskrivning |
|----------|-------|-------------|
| `/` | GET | API-information |
| `/health` | GET | Hälsokontroll |
| `/analyze/text` | POST | Analysera text |
| `/analyze/document` | POST | Analysera PDF |
| `/analyze/quick` | POST | Snabbanalys utan LLM |

**Exempel:**

```bash
curl -X POST "http://localhost:8000/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Klienten Anna Andersson (19850515-1234) har kontakt med socialtjänsten."}'
```

### Programmatisk användning

```python
from src.workflow.orchestrator import create_workflow

# Skapa workflow
workflow = create_workflow(
    api_key="din-openrouter-nyckel",  # Valfritt, för LLM-analys
    use_llm=True,
    masking_style="brackets"
)

# Analysera text
result = workflow.process_text(
    text="Klienten har missbruksproblem.",
    document_id="test",
    requester_ssn=None
)

print(result.masked_text)
# Output: Klienten har [MASKERAT: HÄLSA].
```

## Maskeringsstilar

| Stil | Exempel | Beskrivning |
|------|---------|-------------|
| `brackets` | `[MASKERAT: PERSON]` | Tydlig markering med typ |
| `redacted` | `████████` | Svarta block |
| `placeholder` | `<PERSON>` | XML-liknande taggar |
| `anonymized` | `Person A` | Pseudonymisering |

## OSL-kategorier

Verktyget bedömer uppgifter enligt följande kategorier från OSL 26 kap:

- **HEALTH** - Hälsotillstånd, sjukdomar
- **MENTAL_HEALTH** - Psykisk ohälsa
- **ADDICTION** - Missbruk, beroende
- **VIOLENCE** - Våld, övergrepp
- **FAMILY** - Familjeförhållanden
- **ECONOMY** - Ekonomi, skulder
- **CRIME** - Brottslighet
- **SEXUAL** - Sexuell läggning, könsidentitet
- **CHILD_PROTECTION** - Barnskydd, LVU
- **DISABILITY** - Funktionsnedsättning

## Projektstruktur

```
menprovning/
├── app.py                      # Streamlit GUI
├── src/
│   ├── core/
│   │   ├── models.py           # Datamodeller (Entity, Assessment, etc.)
│   │   └── exceptions.py       # Undantagsklasser
│   ├── ingestion/
│   │   └── pdf_extractor.py    # PDF-extraktion
│   ├── ner/
│   │   ├── regex_ner.py        # Regex-baserad NER
│   │   ├── bert_ner.py         # BERT-baserad NER (valfritt)
│   │   └── postprocessor.py    # Entitetsbearbetning
│   ├── llm/
│   │   ├── client.py           # OpenRouter LLM-klient
│   │   ├── requester_chat.py   # Kravställningsdialog
│   │   └── prompts/
│   │       └── sensitivity.py  # OSL-anpassade prompts
│   ├── analysis/
│   │   └── sensitivity_analyzer.py  # Känslighetsanalys
│   ├── masking/
│   │   └── masker.py           # Textmaskering
│   ├── workflow/
│   │   └── orchestrator.py     # Pipeline-koordinering
│   └── api/
│       └── main.py             # FastAPI REST API
├── test_ner_improvements.py          # Test för NER-förbättringar
├── test_complete_system.py           # Komplett systemtest
├── test_visualization.py             # Test för visualiseringsfunktioner
├── test_complete_workflow.py         # Test för hela workflow med partsdata
└── tests/                      # 142 enhetstester
```

## Konfiguration

### Miljövariabler

| Variabel | Beskrivning | Obligatorisk |
|----------|-------------|--------------|
| `OPENROUTER_API_KEY` | API-nyckel för LLM-analys | Nej (för LLM-stöd) |

### LLM-modell

Standardmodellen är `openai/gpt-4o-mini` via OpenRouter. Kan ändras i `WorkflowConfig`.

## Tester

```bash
# Kör alla tester
PYTHONPATH=. pytest

# Med coverage
PYTHONPATH=. pytest --cov=src --cov-report=html
```

**Teststatus:** 142 enhetstester + 4 integrations tester passerar

## Teknisk stack

- **Python 3.11+**
- **PyMuPDF** - PDF-extraktion
- **Pydantic** - Datavalidering
- **Requests** - HTTP-klient
- **FastAPI** - REST API
- **Streamlit** - Webb-GUI
- **pytest** - Testramverk

## Hantering av ovanliga namn

Verktyget har förbättrats för att bättre hantera ovanliga svenska namn som tidigare kunde missas:

### Exempel på namn som nu uppfattas:

- **Traditionella ovanliga namn:** Sveinung, Eskil, Folke, Gunnar, Holger, Ingvar
- **Äldre svenska namn:** Jarl, Knut, Ragnar, Sten, Torbjörn, Viggo, Yngve
- **Klassiska kvinnonamn:** Aina, Bodil, Dagny, Ebba, Freja, Gertrud, Hilda
- **Internationella namn:** Mohammed, Ali, Fatima, Ahmed, Yasmin, Mustafa

### Teknik för namnigenkänning:

1. **Utökade namnlistor** - 100+ vanliga och ovanliga svenska namn
2. **Regex-mönster** - För efternamn och sammansatta namn
3. **LLM-kontextanalys** - Hittar namn baserat på meningens sammanhang
4. **Genitivformshantering** - Uppfattar "Sveinungs situation" som personnamn
5. **BERT-NER integration** - Djupinlärningsbaserad namnigenkänning

### Exempel på text som nu hanteras korrekt:

```
"Sveinung och Anna kallade till möte"
"Eskils situation är komplex"
"Folke berättade om problemet"
"Sveinungs familj behöver stöd"
```

Allt detta utan att kräva manuell korrigering eller specialkonfiguration.

## Säkerhet

- Verktyget hanterar känsliga personuppgifter
- Använd alltid HTTPS i produktion
- Lagra aldrig API-nycklar i kod
- Rensa temporära filer efter bearbetning
- Följ GDPR och dataskyddsförordningen

## Begränsningar

- **Förslag, inte beslut** - Verktyget ger förslag, manuell granskning krävs alltid
- **Svensk text** - Optimerat för svenska handlingar
- **PDF-kvalitet** - Bättre resultat med text-PDF:er än skannade dokument
- **LLM-beroende** - Bäst resultat med LLM aktiverat

## Licens

Proprietär - Endast för internt bruk.

## Kontakt

För frågor och support, kontakta utvecklingsteamet.

---

**Varning:** Detta verktyg ersätter inte juridisk bedömning. All sekretessprövning ska alltid verifieras av behörig handläggare innan utlämning.
