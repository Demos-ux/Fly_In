PYTHON = python3
MAIN = main.py
VENV = .venv
VENV_BIN = $(VENV)/bin

.PHONY: install run debug clean lint lint-strict

install:
	@echo "Erstelle virtuelle Umgebung..."
	$(PYTHON) -m venv $(VENV)
	@echo "Installiere uv innerhalb der Umgebung..."
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install uv
	@echo "Installiere Projektabhängigkeiten rasend schnell mit uv..."
	$(VENV_BIN)/uv pip install -e ".[dev]"

run:
	$(VENV_BIN)/uv run $(MAIN)

debug:
	$(VENV_BIN)/uv run python -m pdb $(MAIN)

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache .uv-cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	$(VENV_BIN)/uv run flake8 .
	$(VENV_BIN)/uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(VENV_BIN)/uv run flake8 .
	$(VENV_BIN)/uv run mypy . --strict