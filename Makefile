.PHONY: help dev api ui test lint install install-dev clean static-pages spaces

help:
	@echo "ModelRank - Available Commands"
	@echo "================================"
	@echo "  make install      Install core dependencies"
	@echo "  make install-dev  Install all dependencies (including dev + optional)"
	@echo "  make api          Start the FastAPI backend (port 8000)"
	@echo "  make ui           Start the Gradio UI (port 7860)"
	@echo "  make dev          Start both API and UI concurrently"
	@echo "  make test         Run all tests"
	@echo "  make lint         Run linter (ruff)"
	@echo "  make static-pages Generate GitHub Pages badge + leaderboard assets"
	@echo "  make clean        Remove cache files"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements-optional.txt

api:
	python main.py api

ui:
	python main.py ui

dev:
	@echo "Starting API and UI in parallel..."
	@(python main.py api &) && python main.py ui

test:
	pytest tests/ -v

lint:
	ruff check . --fix

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	rm -f data/modelrank.db
	@echo "Cleaned up cache files."

seed:
	python scripts/seed_leaderboard.py

format:
	black . --line-length 100

static-pages:
	python scripts/generate_static_assets.py
	@echo "✅ Static assets in static_output/ — deploy to gh-pages or open static_output/index.html"
