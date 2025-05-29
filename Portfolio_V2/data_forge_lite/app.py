import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import pandas as pd
import boto3
from io import BytesIO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.db_secrets import get_db_secret
from utils.s3_secrets import get_s3_config

# ─── Get RDS Credentials ─────────────────────────────────────────
st.set_page_config(page_title="Data Forge Lite", layout="wide")

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

# ─── Get S3 Client ───────────────────────────────────────────────
try:
    s3_config = get_s3_config("prod/s3")  # Adjust secret name if needed
    s3 = boto3.client(
        "s3",
        aws_access_key_id=s3_config["aws_access_key_id"],
        aws_secret_access_key=s3_config["aws_secret_access_key"],
        region_name="us-west-2"
    )
    S3_BUCKET = s3_config["bucket_name"]
except Exception as e:
    st.error(f"❌ Failed to set up S3: {e}")
    st.stop()

# ─── Parse query_params ──────────────────────────────────────────
query_params = st.query_params
file_id = query_params.get("file_id")

if not file_id:
    st.error("Missing file_id in URL")
    st.stop()

# ─── Define Lightweight File Model ───────────────────────────────
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey

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

# ─── Pull File Metadata from RDS ─────────────────────────────────
session = Session()
file = session.query(File).get(int(file_id))

if not file:
    st.error("❌ File not found.")
    st.stop()

if not file.cleaned or not file.cleaned_key:
    st.warning("⚠️ File has not been cleaned yet.")
    st.stop()

# ─── Download from S3 + Display ──────────────────────────────────
try:
    obj = s3.get_object(Bucket=S3_BUCKET, Key=file.cleaned_key)
    df = pd.read_csv(BytesIO(obj['Body'].read()))

    st.title(f"🧹 Cleaned File: {file.filename}")
    st.dataframe(df, use_container_width=True)
    st.subheader("Summary Statistics")
    st.write(df.describe())

except Exception as e:
    st.error(f"❌ Failed to load data from S3: {e}")