.PHONY: format lint typecheck test test-integration

CHECK_PATHS = manimux $(wildcard tests)

format:
	uv run ruff format $(CHECK_PATHS)
	uv run ruff check --fix $(CHECK_PATHS)

lint:
	uv run ruff format --check $(CHECK_PATHS)
	uv run ruff check $(CHECK_PATHS)

typecheck:
	uv run mypy manimux

test:
	@test -d tests/unit || { echo "Local unit tests are not installed in this checkout."; exit 1; }
	uv run pytest tests/unit

test-integration:
	@test -d tests/integration || { echo "Local integration tests are not installed in this checkout."; exit 1; }
	uv run pytest tests/integration
