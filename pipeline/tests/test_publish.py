import boto3
import json
import time
import get_config
from datetime import datetime

from botocore.exceptions import ClientError

stage = "Klayers-defaultp38"
config, session = get_config.get_config(stage)
table_name = f"{config['app_name']}.{stage}.db"
package = "boto3"
region = config["aws_region"]
