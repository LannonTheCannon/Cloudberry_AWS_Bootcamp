import pandas as pd
from ai_data_science_team.agents import DataCleaningAgent, FeatureEngineeringAgent
from langchain_openai import ChatOpenAI
import boto3
import json
import traceback
import time
import plotly.io as pio

def get_openai_api_key(secret_name="dev/openai/api_key", region_name="us-west-1"):
    print(f"🔑 Loading secret: {secret_name}")
    client = boto3.client("secretsmanager", region_name=region_name)
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

# You can switch between static and Secrets Manager here
api_key = get_openai_api_key()

llm = ChatOpenAI(
    model='gpt-4o-mini',
    openai_api_key=api_key
)

data_cleaning_agent = DataCleaningAgent(model=llm, n_samples=50, log=False)
feature_engineering_agent = FeatureEngineeringAgent(model=llm, n_samples=50, log=False)

def run_clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    try:
        start_all = time.time()
        print("⏳ Loading OpenAI API key...")


        
        if not api_key:
            raise RuntimeError("🛑 OpenAI API key could not be loaded.")


        print("🧹 Starting Cleaning Agent...")
        t1 = time.time()
        # cleaning_agent = DataCleaningAgent(model=llm)
        data_cleaning_agent.invoke_agent(data_raw=df, user_instructions='Use default cleaning steps.')
        df_cleaned = data_cleaning_agent.get_data_cleaned()

        print(f"✅ Cleaning completed in {time.time() - t1:.2f} seconds.")

        print("🧠 Starting Feature Engineering Agent...")
        t2 = time.time()

        # fe_agent = FeatureEngineeringAgent(model=llm)

        feature_engineering_agent.invoke_agent(data_raw=df_cleaned, user_instructions='Use default feature engineering steps')
        df_final = feature_engineering_agent.get_data_engineered()

        print(f"✅ Feature Engineering completed in {time.time() - t2:.2f} seconds.")
        print(f"⏱️ Total pipeline runtime: {time.time() - start_all:.2f} seconds.")
        return df_final

    except Exception as e:
        print("❌ AI Pipeline Error:")
        traceback.print_exc()
        raise
