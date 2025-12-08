.PHONY: help install dev test test-unit test-int test-val lint format typecheck validate-all validate-ner validate-class validate-llm coverage run clean

POETRY := poetry

# Standardmål
help:
	@echo "Menprövningsverktyg - Utvecklingskommandon"
	@echo ""
	@echo "Setup:"
	@echo "  install       Installera alla dependencies"
	@echo "  dev           Sätt upp utvecklingsmiljö"
	@echo ""
	@echo "Test:"
	@echo "  test          Kör alla tester"
	@echo "  test-unit     Kör enhetstester"
	@echo "  test-int      Kör integrationstester"
	@echo "  test-val      Kör valideringstester"
	@echo "  coverage      Generera coverage-rapport"
	@echo ""
	@echo "Kvalitet:"
	@echo "  lint          Kör linting"
	@echo "  format        Formatera kod"
	@echo "  typecheck     Kör typkontroll"
	@echo ""
	@echo "AI Validering:"
	@echo "  validate-all  Kör alla valideringar"
	@echo "  validate-ner  Validera NER-precision"
	@echo "  validate-class Validera klassificering"
	@echo "  validate-llm  Validera LLM-kvalitet"
	@echo ""
	@echo "Utveckling:"
	@echo "  run           Starta utvecklingsserver"
	@echo "  clean         Rensa temporära filer"

# === SETUP ===

install:
	$(POETRY) install --with dev

dev: install
	$(POETRY) run pre-commit install
	@echo "Utvecklingsmiljö redo!"

# === TESTER ===

test:
	$(POETRY) run pytest tests/ -v

test-unit:
	$(POETRY) run pytest tests/unit -v

test-int:
	$(POETRY) run pytest tests/integration -v

test-val:
	$(POETRY) run pytest tests/validation -v

coverage:
	$(POETRY) run pytest tests/unit \
		--cov=src \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-fail-under=80
	@echo "Coverage rapport: htmlcov/index.html"

# === KVALITET ===

lint:
	$(POETRY) run ruff check src tests

format:
	$(POETRY) run ruff format src tests

typecheck:
	$(POETRY) run mypy src --ignore-missing-imports

quality: lint typecheck
	@echo "Kvalitetskontroll klar!"

# === AI VALIDERING ===

validate-ner:
	$(POETRY) run pytest tests/validation/test_ner_accuracy.py -v \
		--tb=short \
		--junitxml=reports/ner-validation.xml

validate-class:
	$(POETRY) run pytest tests/validation/test_classification_accuracy.py -v \
		--tb=short \
		--junitxml=reports/classification-validation.xml

validate-llm:
	$(POETRY) run pytest tests/validation/test_llm_quality.py -v \
		--tb=short \
		--junitxml=reports/llm-validation.xml

validate-all: validate-ner validate-class validate-llm
	@echo "Alla valideringar klara!"

# === UTVECKLING ===

run:
	$(POETRY) run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

shell:
	$(POETRY) run ipython

# === CLEANUP ===

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml 2>/dev/null || true
	rm -rf reports/*.xml reports/*.html 2>/dev/null || true
	@echo "Temporära filer rensade!"

# === CI ===

ci-local: lint typecheck test-unit coverage
	@echo "Lokal CI klar!"
