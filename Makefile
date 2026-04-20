.PHONY: install test eval clean

install:
	python -m venv .venv
	.venv/bin/pip install -e .[dev]

test:
	.venv/bin/pytest -v

eval:
	.venv/bin/python -m harness.run --all

clean:
	rm -rf .eval_cache/ .pytest_cache/ __pycache__/ harness/__pycache__/ tests/__pycache__/
