#!/usr/bin/env bash

set -e

rm -rf layer
docker build -t keithrozario/openssl .
CONTAINER=$(docker run -d keithrozario/openssl false)
docker cp $CONTAINER:/tmp/layer layer
docker rm $CONTAINER
