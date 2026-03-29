PYTHON ?= python3
PYTHONPATH_SRC = PYTHONPATH=src

.PHONY: dev format lint typecheck test build demo check clean

dev:
	$(PYTHON) -m pip install -e .[dev]

format:
	ruff format .

lint:
	ruff check .

typecheck:
	mypy src tests

test:
	$(PYTHONPATH_SRC) $(PYTHON) -m unittest discover -s tests -v

build:
	rm -rf build
	$(PYTHON) -m build --no-isolation

demo:
	$(PYTHONPATH_SRC) $(PYTHON) -m fsm_agent demo examples/research_workflow.txt --final-goal "Deliver a validated answer to the user" --actions examples/research_workflow_actions.json --json

check: lint typecheck test

clean:
	rm -rf build dist .mypy_cache .ruff_cache .coverage *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
