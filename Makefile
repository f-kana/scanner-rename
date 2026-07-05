.PHONY: test format format-python format-prettier check-format upgrade-cc setup-bell

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

upgrade-cc:
	npm update -g @anthropic-ai/claude-code
	claude --version

setup-bell:
	@tty > ~/.claude_bell_tty && echo "Bell TTY registered: $$(cat ~/.claude_bell_tty)" || echo "Error: not running in a terminal"
