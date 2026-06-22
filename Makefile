.PHONY: test format format-python format-prettier check-format

test:
	uv run pytest --cov --cov-report=term-missing

format: format-python format-prettier

format-python:
	uv run ruff format .

format-prettier:
	npx prettier --write .

check-format:
	uv run ruff format --check .
	npx prettier --check .
