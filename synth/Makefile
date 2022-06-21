# Default set up for working with docker on the GAE
# Load the user and group ids to avoid permissions trouble
NB_UID := $(shell id -u)
NB_GID := $(shell id -g)

export NB_UID
export NB_GID

# Load secrets so available to docker
# Specifically the UDS credentials
# include ../.env

.PHONY:
	mock1build
	mock2copyin
	mock3run
	mock4copyout
	mock5stop
	help

.DEFAULT_GOAL := help

## Build docker image (uses Dockerfile)
mock1build:
	docker build \
		--build-arg HTTP_PROXY \
		--build-arg HTTPS_PROXY \
		--build-arg http_proxy \
		--build-arg https_proxy \
		--build-arg NB_UID  \
		--build-arg NB_GID  \
		-t jupyter-hyui .

## Copy the example synthetic data pipeline into the portal
mock2copyin:
	cp ./synth_data.ipynb ./portal/

## Run docker image and make the API SQL query available
mock3run:
	@echo "*** JupyterLab will run on port 8091"
	@echo "*** Working directory (portal) is exluded from version control"
	@echo "*** You must manually copy files in and out as needed"
	docker run -u "${NB_UID}":"${NB_GID}" \
		-v ${PWD}/portal:${PWD} \
		-w ${PWD} \
		-e HOME=${PWD}/.home \
		-it \
		--rm \
		--init \
		-p 8091:8888 \
		--env-file ../.env \
		jupyter-hyui jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --LabApp.token=''

# docker run -it --rm \ --detach \ -p 8091:8888 \ --user root \ -e NB_USER=hyui \ -e NB_UID="${NB_UID}" \ -e NB_GID="${NB_GID}"  \ -e CHOWN_HOME=yes \ -e CHOWN_HOME_OPTS="-R" \ --env-file ../.env \ -w "/home/${NB_USER}" \ -v ${PWD}/portal:/home/hyui/portal \ jupyter-hyui:latest \

## Copy the synthetic data and the query from the portal
mock4copyout:
	cp ./portal/mock.h5 ./
	cp ./portal/query.sql ./
	@echo "*** Now move these files to the corresponding API folder"


## Stop that docker image
## Beware that this will stop all containers on this machine derived from this image
mock5stop:
	@echo "*** Stopping all docker containers derived from jupyter-hyui"
	docker ps --filter ancestor=jupyter-hyui -aq | xargs docker stop


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
