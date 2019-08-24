#!/usr/bin/env bash

set -e

rm -rf layer
docker build -t keithrozario/netcat .
CONTAINER=$(docker run -d keithrozario/netcat:latest false)
docker cp $CONTAINER:/tmp/layer/netcat.zip netcat.zip
docker rm $CONTAINER