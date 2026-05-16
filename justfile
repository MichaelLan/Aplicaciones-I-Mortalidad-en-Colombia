set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
    @just --list

sync:
    uv sync --dev

run:
    uv run python src/main.py

lint:
    uv run ruff check .
    uv run ty check

format:
    uv run ruff check . --fix
    uv run ruff format .

format-check:
    uv run ruff format --check .

verify:
    uv run prek run --all-files

install-hooks:
    uv run prek install

check: lint format-check verify

clean:
    rm -rf .ruff_cache .pytest_cache .mypy_cache .ty_cache .coverage htmlcov build dist *.egg-info
    find . -type d -name __pycache__ -prune -exec rm -rf {} +
    find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
