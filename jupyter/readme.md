Local Jupyter tools for exploratory work

Set-up from project root


```bash
pyenv deactivate
cd ./
pyenv virtualenv 3.11.0 hyui-jupyter
pyenv activate hyui-jupyter
pip install --no-cache-dir ./models
cd jupyter
pip install .
