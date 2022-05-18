# Default set up for working with docker on the GAE
NB_UID := $(shell id -u)
NB_GID := $(shell id -g)

export NB_UID
export NB_GID

.PHONY:
	build

## build docker image
build: 
	docker build \
		--build-arg HTTP_PROXY \
		--build-arg HTTPS_PROXY \
		--build-arg http_proxy \
		--build-arg https_proxy \
		-t jupyter-hyui .

# run docker image
run:
	docker run -it --rm \
		-p 8091:8888 \
		--user root \
		-e NB_USER=steve \
		-e NB_UID="${NB_UID}" \
		-e NB_GID="${NB_GID}"  \
		-e CHOWN_HOME=yes \
		-e CHOWN_HOME_OPTS="-R" \
		-w "/home/${NB_USER}" \
		-v ${PWD}/work:/home/steve/work \
		jupyter-hyui:latest \
		start.sh jupyter lab --LabApp.token=''
