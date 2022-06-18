% Persona = developer reading this who wants to deploy an dash app
% Setting: working on their own lap top with access to UCLH data and machines

# Developing for HyUI

Read this if

- you are able to code in Python
- you already have access to data at UCLH (e.g. EMAP databases or a HYLODE API)
- you want to build a data visualisation using Plotly Dash

Follow these steps

## Install HyUI locally

Install HyUI on your local machine

```shell
git clone https://github.com/HYLODE/HyUi.git
cd HyUi
cp .env.example .env
```

## Prepare synthetic data at UCLH

1. Log on to a UCLH machine
2. Open a browser (e.g. Chrome)
3. Log on to the HyUi JupyterLab instance (e.g. [http://uclvlddpragae07:8091/](<>))
4. Either
    - If you're working with a SQL script then follow the steps in **synth_test_data_consults.ipynb**
    - If you're working with a local HTTP endpoint (e.g. HYLODE API for the census [`http://uclvlddpragae07:5006/emap/icu/census/T03/`](<>)) follow the steps in **synth_test_data_census.ipynb**
5. Copy out your synthetic data

See the [Synthetic Data Preparation](synthetic_data.md) docs.
