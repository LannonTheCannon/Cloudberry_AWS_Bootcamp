import json
import boto3

def get_s3_config(secret_name='prod/s3', region="us-west-1"):
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

