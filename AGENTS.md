# Menprövningsverktyg - Agent Instructions

## Project Overview

This is an AI-assisted tool for **menprövning** (privacy assessment) of social services documents according to the Swedish Public Access and Secrecy Act (OSL), Chapter 26. The tool helps social workers assess which information in public documents should be redacted before disclosure.

## Architecture

```
src/
├── core/           # Data models (Entity, Assessment, etc.)
├── ingestion/      # PDF extraction (PyMuPDF, Tesseract OCR)
├── ner/            # Named Entity Recognition (regex + BERT)
├── llm/            # OpenRouter LLM client, chat dialogs
├── analysis/       # Sensitivity analysis per OSL categories
├── masking/        # Text redaction with multiple styles
├── workflow/       # Pipeline orchestration
└── api/            # FastAPI REST API

app.py              # Streamlit GUI
tests/              # Unit and validation tests
docs/               # Legal handbook and rules
```

## Key Domain Concepts

| Swedish Term | English | Description |
|--------------|---------|-------------|
| **Menprövning** | Privacy assessment | Evaluating what can be disclosed |
| **OSL** | Public Access and Secrecy Act | Swedish law governing document secrecy |
| **Omvänt skaderekvisit** | Reversed burden of proof | Presumption of secrecy (OSL 26) |
| **Tredje man** | Third party | Person mentioned but not the requester |
| **Den enskilde** | The individual | Person the case concerns |
| **Partsinsyn** | Party access | Right to access one's own records |

## Code Conventions

### Language Policy
- **Code** (variables, functions, classes): English
- **Comments and docstrings**: Swedish (domain-specific terminology)
- **User-facing text**: Swedish

### Technical Standards
- **Formatting**: ruff (black-compatible)
- **Type checking**: Strict typing with mypy
- **Data validation**: Pydantic models
- **Testing**: pytest with >=80% coverage target

### Example
```python
def calculate_sensitivity_score(entity: Entity) -> float:
    """
    Beräknar känslighetsnivå för en entitet enligt OSL 26.
    
    Args:
        entity: Entitet att bedöma
        
    Returns:
        Känslighetsnivå mellan 0.0 och 1.0
    """
    # Personnummer har alltid högsta känslighet
    if entity.type == EntityType.SSN:
        return 1.0
    ...
```

## Commands

```bash
# Development
make dev              # Set up development environment
streamlit run app.py  # Run GUI
uvicorn src.api.main:app --reload  # Run API

# Testing
make test             # Run all tests
make test-unit        # Run unit tests only
make validate-all     # Validate AI components
PYTHONPATH=. pytest --cov=src  # With coverage

# Quality
make lint             # Run linting
```

## Dependencies

Core dependencies (install with pip):
```bash
pip install pymupdf pydantic requests streamlit fastapi uvicorn python-dotenv pytesseract
```

Optional for OCR:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-swe
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | For LLM features | API key for LLM analysis |

## Important Files

| File | Purpose |
|------|---------|
| `docs/MENPROVNING_HANDBOK.md` | Legal rules for AI analysis |
| `docs/OSL_RULES.json` | Machine-readable rule structure |
| `validation/gold_standard/` | Annotated test data |
| `testfilAi.pdf` | Reference test document |

## Security Rules

**CRITICAL - Never violate these:**

1. **Never log sensitive data**: No personnummer, names, or sensitive information in logs
2. **Test data only**: Use synthetic or anonymized data for testing
3. **Production isolation**: Production data stays in secure environment
4. **When in doubt, redact**: The legal principle is "presumption of secrecy"

## OSL Sensitivity Categories

The tool classifies text according to these categories from OSL Chapter 26:

| Category | Swedish | Sensitivity |
|----------|---------|-------------|
| `HEALTH` | Hälsotillstånd | CRITICAL |
| `MENTAL_HEALTH` | Psykisk ohälsa | CRITICAL |
| `ADDICTION` | Missbruk/beroende | CRITICAL |
| `VIOLENCE` | Våld/övergrepp | CRITICAL |
| `FAMILY` | Familjeförhållanden | HIGH |
| `ECONOMY` | Ekonomi/skulder | HIGH |
| `CRIME` | Brottslighet | HIGH |
| `SEXUAL` | Sexuell läggning | CRITICAL |
| `CHILD_PROTECTION` | Barnskydd/LVU | CRITICAL |
| `DISABILITY` | Funktionsnedsättning | CRITICAL |

## Quality Thresholds

| Metric | Target |
|--------|--------|
| Test coverage | >= 80% |
| NER F1 score | >= 87% |
| Classification accuracy | >= 85% |

## Workflow

1. **PDF Extraction**: Extract text from PDF (PyMuPDF, fallback to OCR)
2. **NER**: Identify sensitive entities (regex + BERT + LLM context)
3. **Sensitivity Analysis**: Classify text by OSL categories
4. **Party Analysis**: Identify relationships between persons
5. **Masking**: Apply appropriate redaction based on requester context
6. **Output**: Masked text + detailed report

## Masking Styles

| Style | Example | Use Case |
|-------|---------|----------|
| `brackets` | `[MASKERAT: PERSON]` | Clear marking with type |
| `redacted` | `████████` | Traditional redaction |
| `placeholder` | `<PERSON>` | XML-like tags |
| `anonymized` | `Person A` | Pseudonymization |

## Common Tasks

### Adding a new entity type
1. Update `src/core/models.py` - add to `EntityType` enum
2. Update `src/ner/regex_ner.py` - add regex pattern
3. Update `src/analysis/sensitivity_analyzer.py` - add classification rules
4. Add tests in `tests/unit/`

### Adding a new sensitivity category
1. Update `docs/OSL_RULES.json` - add category definition
2. Update `src/core/models.py` - add to `SensitivityCategory` enum
3. Update `src/llm/prompts/sensitivity.py` - update LLM prompt
4. Add validation cases in `validation/gold_standard/`

### Modifying the requester dialog
1. Update `src/llm/requester_chat.py` - modify dialog flow
2. Update `src/core/models.py` - adjust `RequesterContext` if needed
3. Update `app.py` - adjust UI components

## Troubleshooting

### OCR not working
- Ensure Tesseract is installed: `which tesseract`
- Install Swedish language: `sudo apt-get install tesseract-ocr-swe`

### LLM errors
- Check API key: `echo $OPENROUTER_API_KEY`
- Verify connectivity to OpenRouter
- Check rate limits

### NER missing names
- Add to name lists in `src/ner/regex_ner.py`
- Enable LLM context analysis for better detection

## Legal Disclaimer

This tool provides **suggestions only**. All privacy assessments must be verified by qualified personnel before any document disclosure. The tool does not replace legal judgment.
