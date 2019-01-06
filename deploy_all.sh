#!/bin/bash

# Installs all these packages as publicly available layers in all aws regions (except China)
./package.sh -p requests -l Apache-2.0 -r python3.7 -x public
./package.sh -p beautifulsoup4 -l MIT -r python3.7 -x public
./package.sh -p elasticsearch -l Apache-2.0 -r python3.7 -x public
./package.sh -p sqlite3 -l Apache-2.0 -r python3.7 -x public
./package.sh -p bcrypt -l Apache-2.0 -r python3.7 -x public
./package.sh -p pymongo -l Apache-2.0 -r python3.7 -x public
