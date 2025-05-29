import streamlit as st
import pandas as pd
import requests
import boto3

# Get the username from the URL query parameters
query_params = st.query_params
username = query_params.get("user", ["Guest"])

# Display a greeting
st.title(f"Hello, {username} 👋")

# # ─── Query Params ───────────────────────────────────────────────
# query_params = st.query_params
# username = query_params.get("user", ["Guest"])[0]
# file_id = query_params.get("file_id", [None])[0]
#
# st.title(f"Hi there, {username.capitalize()} 👋")
#
# if not file_id:
#     st.warning("⚠️ No file ID provided.")
#     st.stop()
#
# # ─── Fetch Cleaned File Key from Flask ───────────────────────────
# flask_api_url = f"http://54.193.148.70:5001/api/file/{file_id}"
#
# try:
#     response = requests.get(flask_api_url)
#     response.raise_for_status()  # will raise HTTPError for bad status
#     cleaned_key = response.json().get("cleaned_key")
#
#     if not cleaned_key:
#         st.error("❌ Could not retrieve cleaned file key.")
#         st.stop()
# except Exception as e:
#     st.error(f"❌ Failed to fetch file info: {e}")
#     st.stop()
#
# # ─── Load from S3 ────────────────────────────────────────────────
# try:
#     bucket = "your-bucket-name"  # 🔁 Replace this with your actual S3 bucket name
#     s3 = boto3.client("s3")
#     obj = s3.get_object(Bucket=bucket, Key=cleaned_key)
#     df = pd.read_csv(obj["Body"])
#
#     st.success("✅ Loaded!")
#     st.dataframe(df)
# except Exception as e:
#     st.error(f"⚠️ Error loading dataset from S3: {e}")