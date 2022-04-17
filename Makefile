# Default set up for working with docker on the GAE
UID := $(shell id -u)
GID := $(shell id -g)
# These two lines make local environment variables available to Make
include .env
export $(shell sed 's/=.*//' .env)

# Self-documenting help; any comment line starting ## will be printed
# https://swcarpentry.github.io/make-novice/08-self-doc/index.html
## 
## Sitrep application 
## HYLODE team 2021
## 
## help             : call this help function
.PHONY: help
help : Makefile
	@sed -n 's/^##//p' $<

## app-build        : Build the app locally (docker-compose build)
.PHONY: app-build
app-build:
	docker-compose build \
		 --build-arg http_proxy \
		 --build-arg https_proxy \
		 --build-arg HTTP_PROXY \
		 --build-arg HTTPS_PROXY 
	@echo "*** HyUI build complete"

## app-run          : Run the app locally
.PHONY: app-run
app-run:
	docker-compose up -d
	docker-compose logs -f

## app-down         : Stop the app
.PHONY: app-down
app-down:
	docker-compose down

## app-test         : Run tests
.PHONY: app-test
app-test:
	docker build --tag hyui .
	docker run hyui


