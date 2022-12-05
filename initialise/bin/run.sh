#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
if [[ "${TRACE-0}" == "1" ]]; then
    set -o xtrace
fi

if [[ "${1-}" =~ ^-*h(elp)?$ ]]; then
    echo 'Usage: ./initialise.sh

Initialises the Docker Compose services. Run once the services are running.

'
    exit
fi

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${BIN_DIR%/*/*}"

docker build -t "hyui-initialise" -f "${PROJECT_DIR}/docker/initialise/Dockerfile" .

# Used to ensure that we don't use the proxy server when running from the same
# machine. We only use the first part of the domain name below.
HOSTNAME="$(hostname)"

docker run --rm --env NO_PROXY="${HOSTNAME%%.*}" --env-file "${PROJECT_DIR}/.env" hyui-initialise --log=INFO
