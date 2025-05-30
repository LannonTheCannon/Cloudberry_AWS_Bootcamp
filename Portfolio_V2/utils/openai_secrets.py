import traceback
import json
import boto3

def get_openai_api_key(secret_name="dev/openai/api_key", region_name="us-west-1"):
    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response["SecretString"])
        return secret_dict["OPENAI_API_KEY"]
    except Exception as e:
        print("❌ Secret load error:")
        traceback.print_exc()
        return None
