.PHONY: test

test:
	uv run pytest --cov --cov-report=term-missing
