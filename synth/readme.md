A standalone directory that should be used in Stage 1 of the pathway to build the synthetic data.
The Dockerfile will spin up a JupyterLab that can be used for this purpose.

The `./synth/portal/` directory is mounted onto the JupyterLab container.
Synthetic data can be saved here.
The query that drives this is shared between `./src/api` and `./synth/portal`, and will need manually copying between those locations.

Move a copy of synth_data.ipynb, query.sql (rename as live.sql), and the HDF fle from the portal to the relevant API folder

## Fakers for Personal Identifiable Information

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
}
```
