[![CI](https://github.com/HYLODE/HyUi/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/HYLODE/HyUi/actions/workflows/main.yml)

## Welcome to [HYLODE](https://hylode.org)!

This repository is for Plotly Dash apps within a hospital environment. A
template application would be split into a frontend and a backend with
communication between the two via HTTP, and the project orchestrated by
docker compose.

The application code including the backend API in `./api`, and the frontend written in Dash is kept in `./web`.

Documentation is available [here](https://hylode.org/developer/setup.html).

## Project Structure

```
.
|
|-- README.md           // This file and the project root.
|-- config files        // E.g. .gitignore.
|-- env.example         // An example version of .env.
|-- compose.yml         // Orchestrate front/backend.
|-- api                 // The FastAPI backend code.
|-- web                 // The Plotly Dash frontend code.
|-- models              // The Pydantic models shared between web and api.
|-- synth               // Synthetic data generation for testing.
|-- docs                // A Quarto driven documentation site.
|
```

**Where this documentation refers to the root folder we mean where this README.md is
located.**
