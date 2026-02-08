.PHONY: test lint format demo install dev clean

test:
	python -m pytest tests/ -v

lint:
	ruff check mcp_toolkit/ tests/
	ruff format --check mcp_toolkit/ tests/

format:
	ruff check --fix mcp_toolkit/ tests/
	ruff format mcp_toolkit/ tests/

demo:
	streamlit run app.py

install:
	pip install -e .

dev:
	pip install -e ".[dev]" -r requirements-dev.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	rm -rf build/ dist/ *.egg-info
