import boto3
import pandas as pd
import os
import json
from io import BytesIO
from ai_data_science_team.agents import DataCleaningAgent
from langchain_openai import ChatOpenAI

s3 = boto3.client("s3")
secrets = boto3.client("secretsmanager")

def get_openai_key():
    secret_id = "prod/openai/api"  # Replace with your actual secret name
    response = secrets.get_secret_value(SecretId=secret_id)
    secret = json.loads(response['SecretString'])
    return secret['OPENAI_API_KEY']

def lambda_handler(event, context):
    bucket = event["bucket"]
    key    = event["key"]

    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(BytesIO(obj["Body"].read()))

    # Invoke DataCleaningAgent
    api_key = get_openai_key()
    model = ChatOpenAI(model="gpt-4o-mini", openai_api_key=api_key)
    cleaner = DataCleaningAgent(model=model, log=False)

    cleaner.invoke_agent(df, user_instructions="Use default cleaning steps.")
    df_cleaned = cleaner.get_data_cleaned()

    buffer = BytesIO()
    df_cleaned.to_csv(buffer, index=False)
    buffer.seek(0)

    cleaned_key = key.replace("uploads/", "cleaned/")
    s3.put_object(Bucket=bucket, Key=cleaned_key, Body=buffer)

    return {
        "status": "success",
        "cleaned_key": cleaned_key
    }
