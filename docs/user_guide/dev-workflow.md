% Persona = developer reading this who wants to deploy an dash app
% Setting: working on their own lap top with access to UCLH data and machines


## Prepare synthetic data at UCLH

1. Log on to a UCLH machine
2. Open a browser (e.g. Chrome)
3. Log on to the HyUi JupyterLab instance (e.g. [http://uclvlddpragae07:8091/](<>))
4. Either
    - If you're working with a SQL script then follow the steps in **synth_test_data_consults.ipynb**
    - If you're working with a local HTTP endpoint (e.g. HYLODE API for the census [`http://uclvlddpragae07:5006/emap/icu/census/T03/`](<>)) follow the steps in **synth_test_data_census.ipynb**
5. Copy out your synthetic data

See the [Synthetic Data Preparation](synthetic_data.md) docs.

## Set-up local API

make a local API module
create the `__init__.py` with reference to routes
the directory should contain

```
api/mymodule
|
|-- __init__.py         // define project wide variables
|-- mock.h5             // synthetic data create above for mocking
|-- mock.sql            // query to run against mock database
|-- model.py            // pydantic (SQLmodel) to define data
```

add a new route to `config.settings.ModuleNames`

```python
class ModuleNames(str, Enum):
    """
    Class that defines routes for each module
    """

    consults = "consults"
    sitrep = "sitrep"
    mymodule = "mymodule"
```

## Set-up local testing

then run mock.py (and this will insert the mock data into the local sqlite database)
then either `make api` or `uvicorn api.main:app --reload --workers 4 --host 0.0.0.0 --port 8092`
navigate to [http://localhost:8092/docs](<>) to check that it works

then create a module for testing (just duplicate an existing one and adapt)
you will need a local conftest.py to set up the mockdata

## Set-up local Dash app

then create an app in **src/apps/mymodule**
ideally import headers and other attributes (from **src/apps/index.py**) for consistent styling
register the new routes in **src/apps/index.py**