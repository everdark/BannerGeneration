# Generative Banner

A [Gradio](https://github.com/gradio-app/gradio) app to demonstrate visual banner generation workflow with [Google's text-to-image model](https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview).

---
- [Usage](#usage)
- [Backend requirements](#backend-requirements)
- [How to contribute](#how-to-contribute)
---

## Usage

Create a `.env` file at the root (refer to [`.env.example`](.env.example)).

Install all the dependencies (via [Poetry](https://github.com/python-poetry/poetry)):

```bash
make install
```

Then run the command to launch the app:

```bash
make run
```

## Backend requirements

The app requires access to the following GCP services:

- Gemini API
- Firestore

## How to contribute

Refer to the [contributing guide](./CONTRIBUTING.md) for details.
