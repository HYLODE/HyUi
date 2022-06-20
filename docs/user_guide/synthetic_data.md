## Synthetic data preparation

Be careful!
We will use the tooling provided by the [Synthetic Data Lab](https://sdv.dev) from a JupyterLab in a browser on a hospital machine. You will need access to the GAE to run this.

### Scenarios

#### Scenario 1 (data via SQL)

Ensure that your database credentials are stored in the `./.secrets` file.
From the GAE commandline, navigate to the `synth` directory (`cd ./synth`), then use the Makefile commands as follows

1. `make mock1build` to build a docker image with JupyterLab and sdv pre-installed.
2. `make mock2run` to spin up JupyterLab (e.g. Working from GAE07 this will be at [](http://UCLVLDDPRAGAE07:8091) but the URL server will depend on the GAE).
3. `make mock3copyin` This will copy the example notebook `synth_test_data.ipynb` into the `./synth/portal` directory that is attached to the JupyterNotebook. Now open the example notebook `synth_test_data.ipynb` using JupyterLab and work through the steps. Create your SQL query and save as `query_live.sql` file must return a *SELECT* statement. Save just the synthesised mock data to `mock.h5`, and the query (`query_live.sql`). Be **careful** and ensure that you specify 'fakers' for all direct identifiers. We recommend the four eyes approach wherein a second person reviews your work before an export.
4. `make mock4copyout` to copy just the query and the synthetic data. Do not copy the notebook out of the `portal` directory unless you are sure you have stripped all personally identifiable data (i.e. clear all cells before saving).
5. `make mock5stop` to stop the JupyterLab instance and clear up

#### Scenario 2 (data via an http `get` request)

This is similar to the steps above but does not depend on the query or database credentials. You are likely to need to use the Python requests library to get the data that will be used by [sdv](https://sdv.dev).

### Fakers for Personal Identifiable Information

Without forcing this specification, then SDV treats columns as 'categories' and shuffles / re-arranges but the original data will appear.

Define fields that contain PII and need faking (see the sketchy documentation [here](https://sdv.dev/SDV/developer_guides/sdv/metadata.html?highlight=pii#categorical-fields-data-anonymization) and the [Faker Documentation](https://faker.readthedocs.io/en/master/providers.html) for a full list of providers. Here is a brief example that specifies Fakers for [name](https://faker.readthedocs.io/en/master/providers/faker.providers.person.html#faker.providers.person.Provider.name) and [date of birth](https://faker.readthedocs.io/en/master/providers/faker.providers.date_time.html#faker.providers.date_time.Provider.date_of_birth). Note that you must pass arguments to a faker as a list.
NB: sdv also doesn't always recognise the columns correctly. Here we specify data_of_birth explicitly as a date whilst working on the larger task of defining columns that contain PII. See [field details](https://sdv.dev/SDV/developer_guides/sdv/metadata.html#field-details)

Example specification to force faking for PII fields within the data

```python
fields = {
    'dob': {
        'type': 'datetime',
        'format': '%Y-%m-%d',
        'pii': True,
        # the 'pii_category' key defines the Faker function name (method)
        'pii_category': "date_of_birth",
    },
    'admission_age_years': {
        'type': 'numerical',
        'pii': True,
        'pii_category': ['random_number', 2 ]
    },
    'name': {
        'type': 'categorical',
        'pii': True,
        'pii_category': 'name'
    },
    'mrn': {
        'type': 'categorical',
        'pii': True,
        'pii_category': ['random_number', 8 ]
    },
    'csn': {
        'type': 'categorical',
        'pii': True,
        'pii_category': ['numerify', '10########' ]
    },
    'postcode': {
        'type': 'categorical',
        'pii': True,
        'pii_category': 'postcode',
        'pii_locales': ['en_GB'],
    },
}
```
