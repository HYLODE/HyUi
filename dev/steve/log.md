# Running notes log

## 2022-06-12t12:33:47
trying to reconfigure structure for better docker
using tests to check progress


## 2022-06-09t00:39:45#
working on playwright testing
try to read these ...
https://headlesstesting.com/blog/playwright-pytest
https://github.com/AutomationPanda/playwright-python-tutorial
https://blog.testproject.io/2019/07/16/behavior-driven-python-tests-using-pytest-bdd/

## 2022-06-08t23:29:33#
switched to using gunicorn for serving production
so docker-compose is production only
and make now provides short cuts to dev versions

## 2022-06-08t16:50:41
trying to get github actions to work
some progress but local development would be preferable
trying this
https://github.com/nektos/act
```sh
cd ./ # project root
brew install act # first run only
act -j lint_etc --container-architecture linux/amd64
```
- first run choose the medium size config image
- set up .actrc file to manage local architecture (in .gitignore to avoid it misbehaving on different machines with different architectures)

```sh
# sample .actrc file at ./.actrc
--container-architecture linux/amd64
````



## 2022-06-08t00:12:22
more than one route now works with different models
not checked this before as only ever had one model
not sure why the factory approach didn't work

found this when looking for fastapi factory
no good for problem above but the structure here looks useful
https://github.com/rednafi/fastapi-nano
and this
https://github.com/gaganpreet/fastapi-starter

## 2022-06-07t18:00:44
pinned requirements files
updated docker to bullseye
now need to work on CI

see advice on best docker builds for python here
https://pythonspeed.com/articles/alpine-docker-python/


why aren't my pre-commit checks working
https://pre-commit.com
but this works
```
pre-commit run --all-files
```

You need to install the pre-commit file
```sh
pre-commit install
```

## 2022-06-07t10:52:57
trying to setup multipage app
but layout not built correctly _unless_ you start the app directly
e.g.
python index.py is OK
but
python apps/index.py is not OK
so perhaps something is missing from the pythonpath
and this means that your whole structure will fall apart since you assume that you're working from ./src
but now you have to work from ./src/apps
but this is odd b/c it worked ok for dashRep
@RESUME: https://stackoverflow.com/questions/59903698/multi-page-dash-app-callbacks-not-registering
fixed by using the @callback decorator? fr dash 2.0

## 2022-06-06t23:29:29
produced fake data as per sitrep
been back through the SDV documentation and worked out how to force 'faking' for PII

Notes in the exemplar notebooks

Define fields that contain PII and need faking (see the sketchy documentation [here](https://sdv.dev/SDV/developer_guides/sdv/metadata.html?highlight=pii#categorical-fields-data-anonymization) and the [Faker Documentation](https://faker.readthedocs.io/en/master/providers.html) for a full list of providers. Here is a brief example that specifies Fakers for [name](https://faker.readthedocs.io/en/master/providers/faker.providers.person.html#faker.providers.person.Provider.name) and [date of birth](https://faker.readthedocs.io/en/master/providers/faker.providers.date_time.html#faker.providers.date_time.Provider.date_of_birth). Note that you must pass arguments to a faker as a list. NB: sdv also doesn't always recognise the columns correctly. Here we specify data_of_birth explicitly as a date whilst working on the larger task of defining columns that contain PII. See [field details](https://sdv.dev/SDV/developer_guides/sdv/metadata.html#field-details)

## 2022-05-29t23:20:32

mock.py not generates mock data for each API module
stores it all in the same sqlite database though

## 2022-05-29t00:30:49

started to set up multipage app framework
separate modules for each possible api that will be exposed
prob next step it to build a landing page that redirects to the necessary module
and then build a genuinely distinct app


## 2022-05-27t23:30:00
Tidied plot
added table
single callback to load data that then feeds both table and plot

## 2022-05-27t11:03:10
set up validation of the JSON data
https://python.plainenglish.io/data-validation-building-data-validating-classes-with-pydantic-8ee4a023f26d

## 2022-05-26t10:23:37
setting up for integration tests with playwright
no conda builder for arm64 architecture so using pip within environment.yml
suboptimal but :shrug:


## 2022-05-25 18:40:44
made generic the names of the functions in main.py
this works better for a standalone app that serves 'result'
the only thing that changes then is the content of the query

## 2022-05-25 07:50:50
played with great expectations
the command line interface and the jupyter notebook style is nice
going to leave this on try/ branch for now and come back later
expecations are more mature for pandas than for sqlalchemy
and this is likely to be important when dealing with data types in sqlite (e.g. dob is text)
also need to work out how to manage relative imports when specifying the data source

## 2022-05-24 22:41:01
Suite of tools to make mock data now all in one file
Changed the name of the SQLModel to the generic Results
Next step
- use these mock functions in conftest.py to help build the fixtures for testing

## 2022-05-22 15:11:08
basic pytest work
added smoke markers
now need to work out how to insert mock data or ?use the dev environment variable to load the mock data??
the latter might be more appropriate for running integreation tests in the production environment??
that is have some tests tha check bits of code and need fake data
and some tests that check the app is working properly


for data pipeline tests then maybe better provide a fixture that serves the same data that your API will do
then those functions can start with that?

## 2022-05-20t19:18:53
TODO: add a postgres docker service and load with test data
then will need an environment variable to indicate in docker
?moving toward a triple set-up prod/docker/local dev
simpler to just move your mock data within src
done!
works!

## 2022-05-20t12:20:22
reconfigured imports and updated python path for pytest so that works in both docker and pytest

## 2022-05-19t22:51:46

working on testing
https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/
aim is to be able to use the synth data to mock for tests and development

pyproject files stand in for pip etc.
see https://stackoverflow.com/a/65162874/992999

```sh
python -m pip install . # would use pyproject
````


## 2022-05-19 19:46:07


Nice! Command that updates/syncs your conda environment to the yaml file
https://stackoverflow.com/questions/42352841/how-to-update-an-existing-conda-environment-with-a-yml-file


```sh
conda env update --file dev/steve/environment-short.yml --prune
```

## 2022-05-19 13:39:25
spent the morning getting sdv to work
seems to be good with some fiddling
done lots of re-organising and written some docs


## 2022-05-18t18:25:53
giving up on pip etc.
back to conda
working on a clean conda file

initial install
```sh
conda env create --file=./HyUi/dev/steve/environment-short.yml
```

updating
```sh
conda env update --file dev/steve/environment-short.yml
```

## 2022-05-18t17:01:05

1. Make synthetic version of the data
2. Work on my own machine rather than the disaster that is the DS desktop
3. Write some tests and quality control
4. Update the plot to run live
5. Allow inspection over the last months
6. Split by specialty

Problems with conda environment so rebuilt from yaml
Redoing conda environment
Don't forget to fix the sublime project file references
Don't forget to update `.envrc` as that will activate hyuiv2
Requirements files found in `./`, `./src/api`, `./src/dash`, and `.dev/steve`


```sh
conda create --name hyuiv3 python=3.9
pip install -r requirements.txt
pip install -r src/api/requirements.txt
pip install -r src/dash/requirements.txt
pip install -r dev/steve/requirements.txt
```

didn't use conda install this time, didn't seem to want to behave?
tried to use just pip but choked as usual on scipy
tried this suggestion https://github.com/scipy/scipy/issues/13409#issuecomment-1021057368
```sh
brew install openblas
export OPENBLAS=$(/opt/homebrew/bin/brew --prefix openblas)
export CFLAGS="-falign-functions=8 ${CFLAGS}"
pip3 install scipy
```
It worked! Until we hit problems with llvmlite
then https://stackoverflow.com/a/71249307
which took forever ...
and made me wonder whether I should have just stayed with conda
I think the command below forces an upgrade / install of the entire brew environment
```sh
arch -arm64 brew install llvm@11
LLVM_CONFIG="/opt/homebrew/Cellar/llvm@11/11.1.0_4/bin/llvm-config" arch -arm64 pip install llvmlite
```








## 2022-05-17t23:20:31
docker network now behaves b/c inserted NO_PROXY env variable


## 2022-05-16t17:38:00
working locally
aim is to tidy this repo up so that it can be used to template up a local app

## 2022-05-15 11:16
load .secrets and .env via docker-compose
confirm that this works by
```bash
docker-compose run web bash
# wait for the service to start
env
```


## 2022-05-15 9am
setting up work on UCLH machine
can't get DS desktop to behave so on windows
done a portable install of vscode insiders to local roaming dir (offered default)
no git here but :shrug:
then installed ssh-fs extension and set-up config to allow me to remote edit gae
can't get that to work for hymind
but with mobaxterm open in one window then I now can log on and remote edit the files in vscode
actually, vscode provides a terminal and this works too
BUT none of the python debug tools etc work b/c it can't see the remote environment



## 2022-05-12t23:26:38
working through fastapi docs
getting the testing sorted out
also fixed mypy and relative imports
and activated plugin for mypy for sqlalchemy


## 2022-05-12t18:16:12
https://yeray.dev/python/setting-up-sublime-text-4-for-python#manual-setup
finally got pylsp to work by following manual install as above

got pre-commit hooks to work for black by updating the tag for black in .pre-commit-config.yaml
```yaml
    rev: 22.3.0 # Replace by any tag/version: https://github.com/psf/black/tags
```

## 2022-05-12t17:29:11
https://towardsdatascience.com/fastapi-cloud-database-loading-with-python-1f531f1d438a
working out how to use fastapi
run through the example above and managed to get the data loaded into the database
https://github.com/edkrueger/sars-fastapi
and then it all works

```sh
# first you need to build the database
cd tuts/fastapi_v1
python load.py
# then run the server
uvicorn app.main:app
```
then naviagte to http://127.0.0.1:8000/docs#/default/show_records_records__get


## 2022-05-02 22:15:09
just got the python debugger to work
and re-installed packages for sublimetext without the pytest package which had a broken dependency

next step is to get back to writing some tests
TODO: you want to mock up some data as if you're hitting a real API
TODO: you also want to sort out your testing structure
for python relative imports you really want all your app in the src directory
with modules beneath that

distracted and switched to trying gov.uk environment
https://github.com/best-practice-and-impact/govcookiecutter
new conda environment at python 3.9.9 (as this matches hysys)
then

```sh
conda activate hyuiv2
make requirements
```

got the pre-commit hooks working (I think)
added in cruft (which I think keeps things cleaner)

```sh
pip install cruft
cruft link https://github.com/best-practice-and-impact/govcookiecutter
```

next steps
build a MWE dash app
then use the dash cookiecutter to get a similar and decent structure
merge the two
then write tests for MWE app
remember to use `conda` for installs (and avoid pip if poss)


add the following to .envrc (assuming you have direnv set up)
```sh
# Activate conda environment
# as per https://linuxtut.com/en/909f9619bc8c4330d523/
eval "$(conda shell.bash hook)"
conda activate hyuiv2
```

## 2022-04-26 23:17:35
played with pytest
built simple notebook on hymind lab
aim is to create a requests fixture and then some helper functions that do the appropriate data conversion

## 2022-04-25 22:12:32

Picking this up after a week
Need to practice writing tests

https://github.com/theskumar/python-dotenv
installed python-dotenv
```bash
pip install python-dotenv
```

and https://direnv.net

```bash
brew install direnv
touch .envrc
direnv allow .
```

add the following to .zshrc
```bash
eval "$(direnv hook zsh)"
```




## 2022-04-18t22:59:50
Trying to set-up pytest but not running for mutlipage apps
when the app is nested within src
pages feature from dash labs requires app to be at project level for testing to work



## 2022-04-17t22:30

working on multipage example from
https://github.com/plotly/dash-labs/blob/main/docs/08-MultiPageDashApp.md
mwe complete


## 2022-04-17t15:14:57
seleniumbase as an alternative
https://blog.streamlit.io/testing-streamlit-apps-using-seleniumbase/
some nice conceptual notes on testing
> ## Defining Test Success
> There are several ways to think about what constitutes looking the same in terms of testing. I chose the following three principles for testing my streamlit-folium package:
> 1. The Document Object Model (DOM) structure (but not necessarily the values) of the page should remain the same
> 2. For values such as headings, test that those values are exactly equal
> 3. Visually, the app should look the same
>
> I decided to take these less strict definitions of “unchanged” for testing streamlit-folium, as the internals of the Folium package itself appear to be non-deterministic. Meaning, the same Python code will create the same looking image, but the generated HTML will be different.

```shell
pip3 install seleniumbase
sbase
```

BUT ... https://github.com/seleniumbase/SeleniumBase/issues/1069#issuecomment-1100893208
does not seem compatible

## 2022-04-17t11:28:29
- fresh set-up of project
-
