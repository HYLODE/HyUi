# Default set up for working with docker on the GAE
# Load the user and group ids to avoid permissions trouble
NB_UID := $(shell id -u)
NB_GID := $(shell id -g)

export NB_UID
export NB_GID

# Load secrets so available to docker
# Specifically the UDS credentials
include .secrets

.PHONY:
	build

## build docker image (uses Dockerfile)
build:
	docker build \
		--build-arg HTTP_PROXY \
		--build-arg HTTPS_PROXY \
		--build-arg http_proxy \
		--build-arg https_proxy \
		-t jupyter-hyui .

## run docker image
run:
	@echo "*** JupyterLab will run on port 8091"
	docker run -it --rm \
		--detach \
		-p 8091:8888 \
		--user root \
		-e NB_USER=steve \
		-e NB_UID="${NB_UID}" \
		-e NB_GID="${NB_GID}"  \
		-e CHOWN_HOME=yes \
		-e CHOWN_HOME_OPTS="-R" \
		-e UDS_USER \
		-e UDS_PWD \
		-e UDS_HOST \
		-w "/home/${NB_USER}" \
		-v ${PWD}/work:/home/steve/work \
		jupyter-hyui:latest \
		start.sh jupyter lab --LabApp.token=''

## stop that docker image
stop:
	@echo "*** Stopping all docker containers derived from jupyter-hyui"
	docker ps --filter ancestor=jupyter-hyui -aq | xargs docker stop
