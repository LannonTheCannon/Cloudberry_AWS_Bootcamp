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


# -------------- Session State Initialization -------------- #

if "curr_state" not in st.session_state:
    dataset_label = st.session_state.get("dataset_name", "Dataset")
    root_theme = ThemeNode(
        node_id="S0",
        label="ROOT",
        full_question="Overview of the dataset",
        category="Meta",
        node_type="theme",
        parent_id=None,
        metadata={"content": dataset_label}
    )
    st.session_state.mindmap_nodes = {"S0": root_theme}
    st.session_state.curr_state = StreamlitFlowState(nodes=[root_theme.to_streamlit_node()], edges=[])

for key in [
    "chart_path", "df", "df_preview", "df_summary", "metadata_string",
    "saved_charts", "DATA_RAW", "plots", "dataframes", "msg_index",
    "clicked_questions", "dataset_name"
]:
    if key not in st.session_state:
        if key == "df":
            # seed with an empty DataFrame so .columns always exists
            st.session_state[key] = pd.DataFrame()
        elif key in ["chart_path", "df_preview", "df_summary", "metadata_string", "DATA_RAW"]:
            st.session_state[key] = None
        else:
            st.session_state[key] = []

if "expanded_nodes" not in st.session_state:
    st.session_state.expanded_nodes = set()

if "seen_embeddings" not in st.session_state:
    st.session_state.seen_embeddings = []


# -------------- Utility Functions -------------- #

def generate_root_summary_question(metadata_string: str) -> str:
    if not metadata_string:
        return "Overview of the dataset"
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a data summarizer."},
                {"role": "user", "content": f"Dataset metadata:\n{metadata_string}\n\nSummarize in one sentence."}
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip().split("\n")[0]
    except Exception:
        return "Overview of the dataset"

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
    st.write('hey im here!')