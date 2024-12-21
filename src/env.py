import json
from dataclasses import dataclass
from os import environ

import boto3
from dotenv import load_dotenv

load_dotenv()

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId=environ.get('SECRET_ARN'))
secret = json.loads(response['SecretString'])


@dataclass
class Env:
    bsky_handle: str = secret.get('BSKY_HANDLE')
    bsky_password: str = secret.get('BSKY_PASSWORD')
