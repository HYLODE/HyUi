# `hyui`

User interface for the HYLODE project[This project structure is based on the
`govcookiecutter` template project][govcookiecutter] but is adapted to work
with applications rather than just data science workflows. A template
application would be split into a frontend and a backend with communication
between the two via HTTP, and the project orchestrated by docker-compose.


## Frontend vs Backend

### Backend
This is a Python FastApi server that is exposed on port 8094 when running `docker-compose up -d` from the project root, or `uvicorn main:app` when running from `src/api/` locally.

### Frontend
This is a Plotly Dash app served on port 8095.

### Orchestrating front and back end

```bash
docker-compose down
docker-compose up -d --build && docker-compose logs -f
```


## Project structure

```
.
|
|-- readme.md           // this file and the project root
|-- Makefile            // standard project commands to be run from the shell
|-- config files        // e.g. requirements.txt, .gitignore
|-- .secrets            // e.g. .secrets etc excluded from version control
|-- secrets.example     // an example version of .secrets above
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
|-- docs
|-- data
|-- outputs
|-- notebooks           // jupyter notebooks etc
|-- try                 // ideas playground


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

We imagine that the developer has the appropriate permissions to view the raw data including patient identifiable information (either themselves, or in partnership with a colleague). A justification for this position is [here][provisioning]. Practically, this means early interactive data exploration using the UCLH Datascience Desktop and similar tools, and in turn access to EMAP and Clarity/Caboodle.

This should generate an initial data specification, and this can be used to generate synthetic data. The synthetic data can then be used to drive the rest of the pathway.

### 2. Develop with synthetic data
### 3. Write some tests and quality control
### 4. Update the plot to run live
### 5. Allow inspection over the last months
### 6. Split by specialty






```{warning}
Where this documentation refers to the root folder we mean where this README.md is
located.
```

## Getting started

To start using this project, [first make sure your system meets its
requirements](#requirements).

To be added.

### Requirements

```{note} Requirements for contributors
[Contributors have some additional requirements][contributing]!
```

- Python 3.6.1+ installed
- a `.secrets` file with the [required secrets and
  credentials](#required-secrets-and-credentials)
- [load environment variables][docs-loading-environment-variables] from `.envrc`

To install the Python requirements, open your terminal and enter:

```shell
pip install -r requirements.txt
```

## Required secrets and credentials

To run this project, [you need a `.secrets` file with secrets/credentials as
environmental variables][docs-loading-environment-variables-secrets]. The
secrets/credentials should have the following environment variable name(s):

| Secret/credential | Environment variable name | Description                                |
|-------------------|---------------------------|--------------------------------------------|
| Secret 1          | `SECRET_VARIABLE_1`       | Plain English description of Secret 1.     |
| Credential 1      | `CREDENTIAL_VARIABLE_1`   | Plain English description of Credential 1. |

Once you've added, [load these environment variables using
`.envrc`][docs-loading-environment-variables].

## Licence

Unless stated otherwise, the codebase is released under the MIT License. This covers
both the codebase and any sample code in the documentation. The documentation is ©
Crown copyright and available under the terms of the Open Government 3.0 licence.

## Contributing

[If you want to help us build, and improve `hyui`, view our
contributing guidelines][contributing].

## Acknowledgements

[This project structure is based on the `govcookiecutter` template
project][govcookiecutter].

[contributing]: ./docs/contributor_guide/CONTRIBUTING.md
[govcookiecutter]: https://github.com/best-practice-and-impact/govcookiecutter
[docs-loading-environment-variables]: ./docs/user_guide/loading_environment_variables.md
[docs-loading-environment-variables-secrets]: ./docs/user_guide/loading_environment_variables.md#storing-secrets-and-credentials
[provisioning]: .docs/notes/provisioning_data.md
