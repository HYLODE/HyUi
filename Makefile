.PHONY:
	help
	lint
	testunit
	teste2e
	app
	api
	jupyterlab
	coverage
	coverage_html
	coverage_xml
	docs
	docs_check_external_links
	prepare_docs_folder
	requirements

.DEFAULT_GOAL := help

# ---------------------------
# hyui
# ---------------------------
## Linting etc
lint:
	mypy src/
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

## GitHub Actions - pre-push testing
testci:
	act -j lint_etc
	act -j test_unit


## Run the local development version of fastapi
api:
	cd src
	uvicorn api.main:app --reload --workers 4 --host 0.0.0.0 --port 8092

## Run the local development version of Plotly Dash in debug mode
app:
	cd src
	ENV=dev DOCKER=False python app/app.py

## Run tests within docker
testdocker:
	docker-compose down
	docker-compose build
	docker-compose run api pytest tests/unit/api
	docker-compose run apps pytest tests/unit/apps

## Run unit tests locally
testunit:
	@echo "Running just smoke tests"
	pytest -m smoke src/tests/unit
	@echo "Running unit tests"
	pytest -m "not smoke" src/tests/unit

## Run end-2-end tests (playwright)
teste2e:
	docker-compose down
	docker-compose up -d --build
	docker-compose run playwright

## Run a JupyterLab instance for local interactive work
## this will come with the same packages as the full environment
## NB: Use the Jupyter docker image specified in ./synth for sdv
jupyterlab:
	jupyter lab --port 8091 --ip 0.0.0.0 --LabApp.token=''

# ---------------------------
# gov.uk cookiecutter content
# ---------------------------

## Install the Python requirements for contributors, and install pre-commit hooks
requirements:
	python -m pip install -U pip setuptools
	python -m pip install -r requirements.txt
	pre-commit install

## Create a `docs/_build` folder, if it does not exist. Otherwise delete any sub-folders and their contents within it
prepare_docs_folder:
	if [ ! -d "./docs/_build" ]; then mkdir ./docs/_build; fi
	find ./docs/_build -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} \;

## Compile the Sphinx documentation in HTML format in the docs/_build folder from a clean build
docs: prepare_docs_folder requirements
	sphinx-build -b html ./docs ./docs/_build

## Check external links in the Sphinx documentation using linkcheck in the docs/_build folder from a clean build
docs_check_external_links: prepare_docs_folder requirements
	sphinx-build -b linkcheck ./docs ./docs/_build

## Run code coverage
coverage: requirements
	coverage run -m pytest

## Run code coverage, and produce a HTML output
coverage_html: coverage
	coverage html

## Run code coverage, and produce an XML output
coverage_xml: coverage
	coverage xml


## Get help on all make commands; referenced from https://github.com/drivendata/cookiecutter-data-science
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=25 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
