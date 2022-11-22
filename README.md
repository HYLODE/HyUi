[![CI](https://github.com/HYLODE/HyUi/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/HYLODE/HyUi/actions/workflows/main.yml)

# Hyperlocal Bed Demand Forecasting (User Interface)

This repository is for Plotly Dash apps within a hospital environment. A
template application would be split into a frontend and a backend with
communication between the two via HTTP, and the project orchestrated by
docker compose.

The application code including the backend API in `./api`, and the frontend written in Dash is kept in `./web`.

The documentation is available [here](https://hylode.github.io/HyUi/).

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


## Development Environments

### Local Machine

Your own laptop etc. without access to personally identifiable information (PII) etc.
You wish to be able to build and run applications with test data.

Read the docs in `./docs/developer/setup.qmd` to get started.


### Live Machine

An NHS machine or similar within sensitive environment with access to PII.
You wish to be able to deploy the actual application.

## Development workflow

### 1. Make synthetic or mock versions of the data

We imagine that the developer has the appropriate permissions to view the raw data including patient identifiable information (either themselves, or in partnership with a colleague). A justification for this position is [here][http://hylode.github.io/hyui/notes/provisioning.html]. Practically, this means early interactive data exploration using the UCLH Datascience Desktop and similar tools, and in turn access to EMAP and Clarity/Caboodle.

This should generate an initial data specification, and this can be used to generate synthetic data. The synthetic data can then be used to drive the rest of the pathway.

### 2. Develop with synthetic data

### 3. Write some tests and quality control

### 4. Update the plot to run live


**Where this documentation refers to the root folder we mean where this README.md is
located.**
