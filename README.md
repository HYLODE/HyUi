[![CI](https://github.com/HYLODE/HyUi/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/HYLODE/HyUi/actions/workflows/main.yml)

# Hyperlocal Bed Demand Forecasting (User Interface)

User interface for the HYLODE project Much of the project structure is based
on the[`govcookiecutter` template project][govcookiecutter] but is adapted
for the development of Plotly Dash apps within a hospital environment. A
template application would be split into a frontend and a backend with
communication between the two via HTTP, and the project orchestrated by
docker-compose.

This file (`./readme.md`) is at the root of the project, but the application
code including the backend is in `./src/api/app1`, and the application itself is
kept in `./src/apps/app1`. An annotated figure of the directory structure is shown
below.

The documentation is available [here](https://hylode.github.io/HyUi/).


## Project structure

```
.
|
|-- readme.md           // this file and the project root
|-- Makefile            // standard project commands to be run from the shell
|-- config files        // e.g. requirements.txt, .gitignore
|-- env.example         // an example version of .env
|-- docker-compose.yml  // orchestrate front/backend
|-- src
    |-- frontend
        |-- Dockerfile
        |-- dash_app.py
    |-- backend
        |-- Dockerfile
        |-- query.sql   // SQL used to drive the backend API
|-- synth               // Synthetic data generation for testing
    |-- work
|-- tests
|-- docs                // A Quarto driven documentation site
|-- data
|-- outputs
|-- notebooks           // jupyter notebooks etc
|-- try                 // ideas playground
|

```


## Development environments

### Local machine

Your own laptop etc. without access to personally identifiable information (PII) etc.
You wish to be able to build and run applications with test data.


### Live machine

An NHS machine or similar within sensitive environment with access to PII.
You wish to be able to deploy the actual application.

## Development workflow

### 1. Make synthetic version of the data

We imagine that the developer has the appropriate permissions to view the raw data including patient identifiable information (either themselves, or in partnership with a colleague). A justification for this position is [here][http://hylode.github.io/hyui/notes/provisioning.html]. Practically, this means early interactive data exploration using the UCLH Datascience Desktop and similar tools, and in turn access to EMAP and Clarity/Caboodle.

This should generate an initial data specification, and this can be used to generate synthetic data. The synthetic data can then be used to drive the rest of the pathway.

### 2. Develop with synthetic data

### 3. Write some tests and quality control

### 4. Update the plot to run live


**Where this documentation refers to the root folder we mean where this README.md is
located.**

## Getting started

To start using this project, [first make sure your system meets its
requirements](#requirements).

To be added.

## Contributing

[If you want to help us build, and improve `hyui`, view our
contributing guidelines][contributing].

## Acknowledgements

[This project structure is based on the `govcookiecutter` template
project][govcookiecutter].

[contributing]: ./docs/contributor_guide/CONTRIBUTING.md
[govcookiecutter]: https://github.com/best-practice-and-impact/govcookiecutter
[docs-loading-environment-variables]: ./docs/developer/loading_environment_variables.md
[docs-loading-environment-variables-secrets]: ./docs/developer/loading_environment_variables.md#storing-secrets-and-credentials
[provisioning]: ./docs/notes/provisioning_data.md
