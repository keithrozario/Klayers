#! /bin/bash

## First Argument to the script is the $STAGE, all other arguments are then taken from the configuration file
## e.g. $ ./deploy-container.sh Klayers-defaultp38

STAGE="${1:-Klayers-defaultp38}"
for d in ./*/ ; do (cd "$d" && ./deploy-container.sh $STAGE); done

