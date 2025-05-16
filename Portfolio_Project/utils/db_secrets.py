# utils/db_util.py

import boto3
import json

def get_db_secret(secret_name):
    region_name = "us-west-1"  # Update to your region

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])

    return {
        "username": secret["username"],
        "password": secret["password"],
        "host": secret["host"],
        "port": secret["port"],
        "dbname": secret["dbname"]
    }