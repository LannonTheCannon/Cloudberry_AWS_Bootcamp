import streamlit as st
import pandas as pd
import requests
import boto3

# ─── Query Params ───────────────────────────────────────────────
query_params = st.query_params
username = query_params.get("user", ["Guest"])[0]
file_id = query_params.get("file_id", [None])[0]

st.title(f"Hi there, {username.capitalize()} 👋")

if file_id is None:
    st.warning("No file ID provided.")
    st.stop()

flask_api_url = f"http://localhost:5001/api/file/{file_id}"
response = requests.get(flask_api_url)
cleaned_key = response.json().get("cleaned_key")
