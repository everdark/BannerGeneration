# Contributing Guides

---
- [Pre-requisites](#pre-requisites)
- [Mnage dependencies](#mnage-dependencies)
- [Style](#style)
- [Development](#development)
  - [Add a new model](#add-a-new-model)
---

## Pre-requisites

For functionality interacting with Google Cloud resources,
make sure to setup your [ADC](https://cloud.google.com/docs/authentication/provide-credentials-adc) if you are working with a local machine.

## Mnage dependencies

[Poetry 2](https://github.com/python-poetry/poetry) is used to manage dependencies.

## Style

We follow the Black style using [Ruff](https://github.com/astral-sh/ruff).
To format the code:

```bash
make lint
```

## Development

### Add a new model

Gemini frequently introduces new models.
To include them as part of the option,
simply update the `ImageModel` enum defined in the `constants.py` module with a new member:

```python
class ImageModel(str, Enum):
    """Existing image model from Google Gemini.

    https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/imagen-api
    """

    IMAGEN_3_FAST = "imagen-3.0-fast-generate-001"
    IMAGEN_3 = "imagen-3.0-generate-001"
    IMAGEN_4_PREVIEW = "imagen-4.0-generate-preview-06-06"
```
