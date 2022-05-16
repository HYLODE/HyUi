# Running notes log

## 2022-05-16t17:38:00
working locally
aim is to tidy this repo up so that it can be used to template up a local app
general tidying up and readme added at each folder level
requirements split into separate files for each component

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
