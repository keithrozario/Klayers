#!/bin/bash

# Installs all these packages as publicly available layers in all aws regions (except China)
package.sh -p requests -l Apache-2.0 -r python3.7 -x public
package.sh -p beautifulsoup4 -l MIT -r python3.7 -x public
package.sh -p elasticsearch -l Apache-2.0 -r python3.7 -x public
package.sh -p bcrypt -l Apache-2.0 -r python3.7 -x public
package.sh -p pymongo -l Apache-2.0 -r python3.7 -x public
package.sh -p ffmpeg-python -l Apache-2.0 -r python3.7 -x public -a us-east-1
package.sh -p pyOpenSSL -l Apache-2.0 -r python3.7 -x public
package.sh -p aiohttp -l Apache-2.0 -r python3.7 -x public
package.sh -p tldextract -l "github.com/john-kurkowski/tldextract/blob/master/LICENSE" -r python3.7 -x public
package.sh -p construct -l "github.com/construct/construct/blob/master/LICENSE" -r python3.7 -x public
package.sh -p Pillow -l "raw.githubusercontent.com/python-pillow/Pillow/master/LICENSE" -r python3.7 -x public
package.sh -p pytesseract -l GPL-3 -r python3.7 -x public
package_binaries.sh -p tesseract -l Apache-2.0 -x public -d tesseract.zip -b
package_binaries.sh -p spacy -l MIT -x public -d Klayers-python37-spacy.zip -b
package.sh -p boto3 -l "aws.amazon.com/apache2.0/" -r python3.7 -x public
package.sh -p PyMuPDF -l "GPL-3" -r python3.7 -x public
package.sh -p pytz -l "MIT" -r python3.7 -x public
package_binaries.sh -p pip -l MIT -x public -d binaries/pip/pip.zip -b
package_binaries.sh -p netcat -l GPL -x public -d netcat.zip -b