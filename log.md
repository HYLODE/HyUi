# Running notes log

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
