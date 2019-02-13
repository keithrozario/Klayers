#!/bin/bash

# Installs all these packages as publicly available layers in all aws regions (except China)
./package.sh -p requests -l Apache-2.0 -r python3.7 -x public
./package.sh -p beautifulsoup4 -l MIT -r python3.7 -x public
./package.sh -p elasticsearch -l Apache-2.0 -r python3.7 -x public
./package.sh -p sqlite3 -l Apache-2.0 -r python3.7 -x public
./package.sh -p bcrypt -l Apache-2.0 -r python3.7 -x public
./package.sh -p pymongo -l Apache-2.0 -r python3.7 -x public
./package.sh -p ffmpeg-python -l Apache-2.0 -r python3.7 -x public -a us-east-1
./package.sh -p pyOpenSSL -l Apache-2.0 -r python3.7 -x public
./package_multiple.sh -p aiohttp.txt -l Apache-2.0 -r python3.7 -x public -n aiohttp
./package.sh -p tldextract -l "github.com/john-kurkowski/tldextract/blob/master/LICENSE" -r python3.7 -x public