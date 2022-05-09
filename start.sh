#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Export env variables
set -a
. "${SCRIPT_DIR}/.env"
set +a

docker-compose -f "${SCRIPT_DIR}/docker/docker-compose.yml" up
