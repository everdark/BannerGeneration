# Contributing Guides

---
- [Pre-requisites](#pre-requisites)
- [Mnage dependencies](#mnage-dependencies)
- [Style](#style)
---

## Pre-requisites

For functionality interacting with Google Cloud resources,
make sure to setup your [ADC](https://cloud.google.com/docs/authentication/provide-credentials-adc) if you are working with a local machine.

## Mnage dependencies

[Poetry](https://github.com/python-poetry/poetry) is used to manage dependencies.

If your autenthication to the private Python repositories failed,
run:

```bash
make auth
```

to refresh your token.

## Style

We follow the Black style using [Ruff](https://github.com/astral-sh/ruff).
To format the code:

```bash
make lint
```
