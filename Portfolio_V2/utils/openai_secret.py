import traceback
import boto3
import json
import logging

def get_openai_api_key(secret_name="dev/openai/api_key", region_name="us-west-1"):
    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response["SecretString"])
        return secret_dict["OPENAI_API_KEY"]
    except Exception as e:
    	# Avoid recursive logging errors in Gunicorn
    	with open("/tmp/openai_secret_error.log", "a") as f:
        	f.write(f"Secret load error: {str(e)}\n")
    	return None
