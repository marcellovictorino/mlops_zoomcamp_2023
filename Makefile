# .DEFAULT_GOAL := coverage_test
.ONESHELL := 1

LINE_LENGTH := 88
POETRY_VERSION := 1.2

# Re-enabling mypy as there is a workaround for ABC abstract classes
# Use `type: ignore[misc]` on the dataclass decorator (https://stackoverflow.com/questions/70999513/conflict-between-mix-ins-for-abstract-dataclasses/70999704#70999704)
MYPY := MYPYPATH=stubs poetry run mypy --ignore-missing-imports --strict --implicit-reexport --check-untyped-defs --no-implicit-optional --allow-untyped-calls

# check out Flake8errors to be ignored: https://flake8.pycqa.org/en/latest/user/error-codes.html
FLAKE8 := poetry run flake8 --max-line-length $(LINE_LENGTH) --max-complexity=18 --ignore=E501,W503,E402

ISORT := poetry run isort --profile black
BLACK := poetry run black --line-length $(LINE_LENGTH)
PYTEST := poetry run pytest -vvv tests
PYTESTCOV := poetry run pytest --cov --cov-report term-missing
COVREPORT := poetry run coverage html && poetry run coverage-badge -o coverage.svg -f
BUILD := poetry build
EXPORT := poetry export -f requirements.txt --output requirements.txt
# Local setup, ensures correct poetry version and pre-commit installation
# LOCAL_SETUP := pip install -U pip && pip install -U poetry==$(POETRY_VERSION) && poetry config virtualenvs.in-project true && poetry shell && poetry install && pre-commit install && pre-commit install --hook-type commit-msg
MLFLOW_SERVE := poetry run mlflow ui --backend-store-uri=sqlite:///mlflow.db

MODULES := $(shell find . -mindepth 2 -maxdepth 2 -type f -name __init__.py -not -path "*/tests/*" | xargs -n1 dirname)

mlflow_serve:
	$(MLFLOW_SERVE)

all: lint format coverage_test

mypy:
	$(MYPY) $(MODULES)

flake8:
	$(FLAKE8) $(MODULES)

lint: mypy flake8
	$(ISORT) --check --diff $(MODULES)
	$(BLACK) --check --diff $(MODULES)

format:
	$(ISORT) $(MODULES)
	$(BLACK) $(MODULES)

test:
	$(PYTEST)

coverage_test:
	${PYTESTCOV} ||	${COVREPORT}
	${COVREPORT}

build:
	$(BUILD)

export:
	$(EXPORT)

local_setup:
	$(LOCAL_SETUP)

.PHONY: all mypy flake8 lint format test coverage_test build export local_setup