# Default set up for working with docker on the GAE
# Load the user and group ids to avoid permissions trouble
NB_UID := $(shell id -u)
NB_GID := $(shell id -g)

export NB_UID
export NB_GID

# Load secrets so available to docker
# Specifically the UDS credentials
include ../.secrets

.PHONY:
	dkbuild
	dkrun
	dkstop
	help

## Build docker image (uses Dockerfile)
dkbuild:
	docker build \
		--build-arg HTTP_PROXY \
		--build-arg HTTPS_PROXY \
		--build-arg http_proxy \
		--build-arg https_proxy \
		-t jupyter-hyui .

## Run docker image and make the API SQL query available
dkrun:
	@echo "*** JupyterLab will run on port 8091"
	@echo "*** The SQL query that runs the API is copied into hyui/work "
	cp ../src/api/query.sql ./work/

	docker run -it --rm \
		--detach \
		-p 8091:8888 \
		--user root \
		-e NB_USER=hyui \
		-e NB_UID="${NB_UID}" \
		-e NB_GID="${NB_GID}"  \
		-e CHOWN_HOME=yes \
		-e CHOWN_HOME_OPTS="-R" \
		-e UDS_USER \
		-e UDS_PWD \
		-e UDS_HOST \
		-w "/home/${NB_USER}" \
		-v ${PWD}/work:/home/hyui/work \
		jupyter-hyui:latest \
		start.sh jupyter lab --LabApp.token=''

## Stop that docker image and copies synth data to ./data/raw
## Beware that this will stop all containers on this machine derived from this image
dkstop:
	@echo "*** Stopping all docker containers derived from jupyter-hyui"
	cp ./work/sdv_model.pkl ../data/raw/
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
