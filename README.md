# Menprövning

AI-assisterat verktyg för menprövning av socialtjänsthandlingar enligt Offentlighets- och sekretesslagen (OSL).

## Översikt

Detta verktyg hjälper handläggare inom socialtjänsten att bedöma vilka uppgifter i allmänna handlingar som ska maskeras vid utlämning, baserat på OSL kapitel 26 (socialtjänstsekretess).

### Funktioner

- **PDF-extraktion** - Extraherar text från PDF-dokument
- **NER (Named Entity Recognition)** - Identifierar känsliga entiteter:
  - Personnummer (svenska format)
  - Telefonnummer
  - E-postadresser
  - Adresser
  - Datum och personnnamn
- **Känslighetsanalys** - LLM-baserad + nyckelordsbaserad bedömning enligt OSL-kategorier
- **Automatisk maskering** - Flera maskeringsstilar
- **Partsinsyn** - Stöd för att undanta beställarens egna uppgifter
- **Webb-GUI** - Streamlit-baserat gränssnitt
- **REST API** - FastAPI för integration

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
pip install pymupdf pydantic requests streamlit fastapi uvicorn

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

**Funktioner i GUI:t:**
- Ladda upp PDF-filer för analys
- Klistra in text direkt
- Konfigurera maskeringsstil
- Ange beställarens personnummer för partsinsyn
- Se resultat med statistik och textjämförelse
- Exportera maskerad text och rapport

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

**Teststatus:** 142 tester passerar

## Teknisk stack

- **Python 3.11+**
- **PyMuPDF** - PDF-extraktion
- **Pydantic** - Datavalidering
- **Requests** - HTTP-klient
- **FastAPI** - REST API
- **Streamlit** - Webb-GUI
- **pytest** - Testramverk

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
