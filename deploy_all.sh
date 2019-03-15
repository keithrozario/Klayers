#!/bin/bash

# Installs all these packages as publicly available layers in all aws regions (except China)
./package.sh -p requests -l Apache-2.0 -r python3.7 -x public
./package.sh -p beautifulsoup4 -l MIT -r python3.7 -x public
./package.sh -p elasticsearch -l Apache-2.0 -r python3.7 -x public
./package.sh -p bcrypt -l Apache-2.0 -r python3.7 -x public
./package.sh -p pymongo -l Apache-2.0 -r python3.7 -x public
./package.sh -p ffmpeg-python -l Apache-2.0 -r python3.7 -x public -a us-east-1
./package.sh -p pyOpenSSL -l Apache-2.0 -r python3.7 -x public
./package.sh -p aiohttp.txt -l Apache-2.0 -r python3.7 -x public
./package.sh -p tldextract -l "github.com/john-kurkowski/tldextract/blob/master/LICENSE" -r python3.7 -x public
./package.sh -p construct -l "github.com/construct/construct/blob/master/LICENSE" -r python3.7 -x public
./package.sh -p Pillow -l "raw.githubusercontent.com/python-pillow/Pillow/master/LICENSE" -r python3.7 -x public
./package.sh -p pytesseract -l GPL-3 -r python3.7 -x public