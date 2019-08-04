#!/usr/bin/env bash

aws s3 cp s3://klayers-bucket--prod/packages packages --profile LayerUploader --recursive
aws s3 cp s3://klayers-bucket--prod/arns arns --profile LayerUploader --recursive

# https://security.stackexchange.com/questions/29106/openssl-recover-key-and-iv-by-passphrase/29139#29139
