.PHONY: lint
lint:
	ruff format banner_genai/

.PHONY: run
run:
	gradio banner_genai/app.py
