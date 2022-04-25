# Running notes log

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
