# Menprövningsverktyg - Projektinstruktioner

## Projektöversikt
AI-stött verktyg för menprövning enligt OSL kapitel 26 (socialtjänstsekretess).

## Kommandon
```bash
make dev          # Sätt upp utvecklingsmiljö
make test         # Kör alla tester
make test-unit    # Kör enhetstester
make validate-all # Validera AI-komponenter
make lint         # Kör linting
```

## Kodkonventioner
- **Språk i kod:** Engelska (variabelnamn, funktioner, klasser)
- **Språk i kommentarer/docstrings:** Svenska (domänspecifik terminologi)
- **Formattering:** ruff (black-kompatibel)
- **Typning:** Strikt typing med mypy
- **Modeller:** Pydantic för datavalidering

## Viktiga filer
- `docs/MENPROVNING_HANDBOK.md` - Juridiska regler för AI-analys
- `docs/OSL_RULES.json` - Maskinläsbar regelstruktur
- `validation/gold_standard/` - Annoterad testdata
- `testfilAi.pdf` - Referens-testakt för validering

## Domänterminologi
- **Menprövning:** Sekretessbedömning vid utlämnande av handlingar
- **OSL:** Offentlighets- och sekretesslagen
- **Omvänt skaderekvisit:** Presumtion för sekretess (OSL 26 kap)
- **Tredje man:** Person som nämns i akt men inte är part
- **Enskild:** Den person som ärendet gäller

## Testning
- Enhetstester: `tests/unit/`
- Valideringstester: `tests/validation/`
- Gold standard: Manuellt annoterade dokument för AI-validering
- Krav: Coverage >=80%, NER F1 >=87%, Klassificering >=85%

## Säkerhet
- ALDRIG logga personnummer, namn eller känsliga uppgifter
- Testdata ska vara syntetisk eller anonymiserad
- Produktionsdata stannar i säker miljö
