include .env

POETRY_EXEC ?= poetry
PACKAGE_NAME = generative_banner

.PHONY: lint
lint:
	ruff format ${PACKAGE_NAME}/
	ruff check --fix --select I ${PACKAGE_NAME}/

.PHONY: run
run:
	gradio ${PACKAGE_NAME}/app.py

.PHONY: install
install:
	${POETRY_EXEC} install
