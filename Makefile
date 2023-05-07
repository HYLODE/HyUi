.PHONY:
	help
	jupyterlab
	testci
	api
	web

.DEFAULT_GOAL := help

## Short cut to docker run the web app locally
web-run:
	docker compose -f compose.dev.yml run --rm --no-deps --service-ports web gunicorn -c web/gunicorn_config.py web.app:server
## Use VS Code to debug a running docker compose config
## web docker compose debug = web-dcdb
## DEBUGGER=True runs the debugger.py module
## GEVENT support might(?) help
web-dcdb:
	# docker compose -f compose.dev.yml up -d api baserow redis celery_beat celery_worker celery_flower
	docker compose -f compose.dev.yml run --rm --no-deps -e DEBUGGER=True -e GEVENT_SUPPORT=True --service-ports web gunicorn -c web/gunicorn_config.py web.app:server


## Run a JupyterLab instance for local interactive work
## this will come with the same packages as the full environment
## NB: Use the Jupyter docker image specified in ./synth for sdv
jupyterlab:
	jupyter lab --port 8091 --ip 0.0.0.0 --LabApp.token=''

## GitHub Actions - pre-push testing
testci:
	act -j lint_etc
	act -j test_unit


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
