## Developer set-up

### Secrets and environment variables

Navigate to project root and make a `.env` file then add environment vars into this. This is excluded from version control.

```shell
cd hyui
touch .env
```

### Setting up environment for PyCharm on Mac M1

Using conda and miniforge on mac m1 else problems with scipy etc. 

```shell
conda create --name hyui python=3.10 
conda activate hyui
conda install pyscopg2 # pip fails b/c of c compiler
conda install scipy # pip fails b/c of c compiler
pip3 install -r requirements.txt
```

- [X] prepare a separate `requirements.txt` for docker
- [X] mwe dash app locally
- [X] pytest
- [X] mwe dash in docker
- [ ] mwe dash in docker tested on GAE
- [X] GitHub Actions

## Setting up Dash testing 
- Used example from https://stackoverflow.com/q/69255703
- https://dash.plotly.com/testing
 
 
The following may be useful for the CI/CD step
- https://blog.streamlit.io/testing-streamlit-apps-using-seleniumbase/


```shell
pip install selenium
pip install 'dash[testing]' # need quotes with zsh shell
```

Install the chromedriver for selenium. This won't work the first time (it will timeout) unless you go to the Mac 'Security & Privacy' preference pain and authorise apps downloaded from 'App Store and identified developers'
- `brew install --cask chromedriver`
