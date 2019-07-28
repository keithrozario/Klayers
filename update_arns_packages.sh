#!/usr/bin/env bash

aws s3 cp s3://klayers-bucket--prod/packages packages --profile LayerUploader --recursive
aws s3 cp s3://klayers-bucket--prod/arns arns --profile LayerUploader --recursive
