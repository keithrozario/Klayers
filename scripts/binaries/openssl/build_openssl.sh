#!/usr/bin/env bash

set -e

rm -rf layer
docker build -t keithrozario/openssl .
CONTAINER=$(docker run -d keithrozario/openssl:latest false)
docker cp $CONTAINER:/tmp/layer/openssl.zip openssl.zip
docker rm $CONTAINER
