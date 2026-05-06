.PHONY: test lint-example sarif clean

test:
	python -m pytest

lint-example:
	python -m cds_mildoc lint examples --profile all --fail-on blocker

sarif:
	python -m cds_mildoc lint examples --profile all --format sarif --out cds-mildoc.sarif --fail-on blocker

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info cds-mildoc.sarif
