import pandas as pd
from ai_data_science_team import DataCleaningAgent, FeatureEngineeringAgent
from langchain_openai import ChatOpenAI
import boto3
import json
import traceback

# Corrected secret name and region (match AWS console)
def get_openai_api_key(secret_name="dev/openai/api_key", region_name="us-west-1"):
    print(f"🔑 Loading secret: {secret_name}")
    client = boto3.client("secretsmanager", region_name=region_name)
    print(client)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response["SecretString"])
        api_key = secret_dict.get("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in secret JSON.")

        return api_key

    except Exception as e:
        print(f"❌ Secret load error: {e}")
        return None

# Core AI Cleaning Pipeline
# def run_clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
#     try:
#         api_key = get_openai_api_key()
#         if not api_key:
#             raise RuntimeError("🛑 OpenAI API key could not be loaded from AWS Secrets Manager.")
#
#         llm = ChatOpenAI(
#             model='gpt-4o-mini',
#             openai_api_key=api_key
#         )
#
#         # Step 1: Clean
#         cleaning_agent = DataCleaningAgent(model=llm)
#         cleaning_agent.invoke_agent(data_raw=df, user_instructions='Use default cleaning steps.')
#         df_cleaned = cleaning_agent.get_data_cleaned()
#
#         # Step 2: Feature Engineer
#         fe_agent = FeatureEngineeringAgent(model=llm)
#         fe_agent.invoke_agent(data_raw=df_cleaned, user_instructions='Use default feature engineering steps')
#         df_final = fe_agent.get_data_engineered()
#
#         return df_final


def run_clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    try:
        start_all = time.time()

        print("⏳ Loading OpenAI API key...")
        api_key = get_openai_api_key()
        if not api_key:
            raise RuntimeError("🛑 OpenAI API key could not be loaded from AWS Secrets Manager.")

        llm = ChatOpenAI(
            model='gpt-4o-mini',
            openai_api_key=api_key
        )

        # Step 1: Clean
        print("🧹 Starting Cleaning Agent...")
        t1 = time.time()
        cleaning_agent = DataCleaningAgent(model=llm)
        cleaning_agent.invoke_agent(data_raw=df, user_instructions='Use default cleaning steps.')
        df_cleaned = cleaning_agent.get_data_cleaned()
        print(f"✅ Cleaning completed in {time.time() - t1:.2f} seconds.")

        # Step 2: Feature Engineer
        print("🧠 Starting Feature Engineering Agent...")
        t2 = time.time()
        fe_agent = FeatureEngineeringAgent(model=llm)
        fe_agent.invoke_agent(data_raw=df_cleaned, user_instructions='Use default feature engineering steps')
        df_final = fe_agent.get_data_engineered()
        print(f"✅ Feature Engineering completed in {time.time() - t2:.2f} seconds.")

        print(f"⏱️ Total pipeline runtime: {time.time() - start_all:.2f} seconds.")
        return df_final

    except Exception as e:
        print("❌ AI Pipeline Error:")
        traceback.print_exc()
        raise