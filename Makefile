.PHONY: test lint typecheck check lint-example sarif clean

test:
	python -m pytest

lint:
	python -m ruff check .

typecheck:
	python -m mypy

check: lint typecheck test lint-example

lint-example:
	python -m cds_mildoc lint examples --profile all --fail-on blocker

sarif:
	python -m cds_mildoc lint examples --profile all --format sarif --out cds-mildoc.sarif --fail-on blocker

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info cds-mildoc.sarif
