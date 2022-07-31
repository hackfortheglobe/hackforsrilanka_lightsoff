#!/usr/bin/env bash

docker-compose -f docker/docker-compose.yml logs --tail 1000 -f
