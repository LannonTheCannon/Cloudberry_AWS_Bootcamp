import os
import sys
import json
import boto3
import pandas as pd
from io import BytesIO
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Add parent dir to path to import utils ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_secrets import get_db_secret
from utils.s3_secrets import get_s3_config

# ────────────────────────────────────────────────────────
# SETUP: Streamlit Page + Session State
# ────────────────────────────────────────────────────────
st.set_page_config(page_title="Data Forge Lite", layout="wide")

# 1. Get query params
query_params = st.query_params
file_id = query_params.get("file_id")

if not file_id:
    st.error("❌ Missing file_id in URL")
    st.stop()

# 2. Connect to RDS
try:
    db = get_db_secret("prod/rds/dababy")
    DB_URI = (
        f"mysql+pymysql://{db['username']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['dbname']}"
    )
    engine = create_engine(DB_URI)
    Session = sessionmaker(bind=engine)
except Exception as e:
    st.error(f"❌ Failed to connect to RDS: {e}")
    st.stop()

# 3. Connect to S3
try:
    s3_config = get_s3_config("prod/s3")  # should contain correct bucket + credentials
    s3 = boto3.client(
        "s3",
        aws_access_key_id=s3_config.get("aws_access_key_id"),
        aws_secret_access_key=s3_config.get("aws_secret_access_key"),
        region_name="us-west-1"  # or change if needed
    )
    S3_BUCKET = s3_config["bucket_name"]
except Exception as e:
    st.error(f"❌ Failed to connect to S3: {e}")
    st.stop()

# ────────────────────────────────────────────────────────
# Load cleaned file metadata from RDS
# ────────────────────────────────────────────────────────
Base = declarative_base()
class File(Base):
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    filename = Column(String(255))
    s3_key = Column(String(255))
    cleaned_key = Column(String(512))
    cleaned = Column(Boolean)
    uploaded_at = Column(DateTime)

session = Session()
file = session.query(File).get(int(file_id))

if not file:
    st.error("❌ File not found in database.")
    st.stop()

if not file.cleaned or not file.cleaned_key:
    st.warning("⚠️ This file has not been cleaned yet.")
    st.stop()

# ────────────────────────────────────────────────────────
# Load the actual cleaned dataset from S3
# ────────────────────────────────────────────────────────
try:
    obj = s3.get_object(Bucket=S3_BUCKET, Key=file.cleaned_key)
    df = pd.read_csv(BytesIO(obj['Body'].read()))
    st.session_state.df = df
    st.session_state["DATA_RAW"] = df
    st.session_state["dataset_name"] = file.filename
except Exception as e:
    st.error(f"❌ Failed to load data from S3: {e}")
    st.stop()

# ────────────────────────────────────────────────────────
# UI NAVIGATION
# ────────────────────────────────────────────────────────
PAGE_OPTIONS = ['📊 Cleaned Data Preview', '🧠 Mind Mapping']
page = st.sidebar.radio("Navigation", PAGE_OPTIONS)

# ────────────────────────────────────────────────────────
# PAGE: Cleaned Data Preview
# ────────────────────────────────────────────────────────
if page == '📊 Cleaned Data Preview':
    st.title(f"🧹 Cleaned File: {file.filename}")
    st.dataframe(df, use_container_width=True)
    st.subheader("Summary Statistics")
    st.write(df.describe())

elif page == '🧠 Mind Mapping':
    pass