.PHONY: install fmt lint type test cov check

install:
	uv sync --locked
	uv run pre-commit install

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run lint-imports

type:
	uv run mypy

test:
	uv run pytest

cov:
	uv run pytest --cov --cov-report=term-missing

check: lint type cov
