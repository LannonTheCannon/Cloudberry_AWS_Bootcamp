import streamlit as st
import pandas as pd
import requests
import boto3

# ─── Query Params ───────────────────────────────────────────────
query_params = st.query_params
username = query_params.get("user", ["Guest"])[0]
file_id = query_params.get("file_id", [None])[0]

st.title(f"Hi there, {username.capitalize()} 👋")

if file_id:
    st.write("🔄 Loading cleaned dataset...")

    try:
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=bucket, Key=cleaned_key)
        df = pd.read_csv(obj["Body"])

        st.success("✅ Loaded!")
        st.dataframe(df)
    except Exception as e:
        st.error(f"⚠️ Error loading dataset: {e}")

flask_api_url =  f"http://54.193.148.70:5001/api/file/{file_id}"
response = requests.get(flask_api_url)
cleaned_key = response.json().get("cleaned_key")
