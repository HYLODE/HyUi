# Developing for HyUI


Read this if

- you are able to code in Python
- you already have access to data at UCLH (e.g. EMAP databases or a HYLODE API)
- you want to build a data visualisation using Plotly Dash

Follow these steps

## Setting up your development environment

Install HyUI on your local machine

```shell
git clone https://github.com/HYLODE/HyUi.git
cd HyUi
cp .env.example .env
```

We assume that the majority of the development work will be on your own machine. You will therefore need to set-up your own dev environment. I have been using [conda miniforge](https://github.com/conda-forge/miniforge) because this has the best compatibility with the ARM processor on the Mac. I think it should also work on other machines but I have not tested this.

From within the HyUi directory

```sh
conda env create --file=./dev/steve/environment-short.yml
conda activate hyuiv4
```

Then confirm your set-up is OK

```sh
pytest src/tests/smoke
```

## Running the backend and frontend

Without docker ...

Backend (all routes)

```sh
cd ./src
uvicorn api.main:app --reload --workers 4 --host 0.0.0.0 --port 8092
```

then navigate to [http://localhost:8092/docs]() to view the API documentation

... `app/main.py` hosts the various routes for the different apps


Frontend (per app)

```sh
cd ./src
ENV=dev DOCKER=False python apps/app.py
```
then navigate to [http://localhost:8093]() to view the app


## Apple Silicon notes

See [Hylode HySys](https://github.com/HYLODE/HySys/tree/dev/hylode#5-development)
