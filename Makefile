.PHONY: lint
lint:
	ruff format banner_genai/
	ruff check --fix --select I banner_genai/

.PHONY: run
run:
	gradio banner_genai/app.py
