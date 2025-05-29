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

from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import ManualLayout, RadialLayout, TreeLayout

# Node template (your custom classes)
from node_template import BaseNode, ThemeNode, QuestionNode, TerminalNode

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

    # Save everything into session_state
    df_final = df
    st.session_state.df = df_final
    st.session_state.DATA_RAW = df_final
    st.session_state.df_preview = df_final.head()

    st.session_state.df_final = df_final
    st.session_state.cleaning_code = data_cleaning_agent.get_data_cleaner_function()
    st.session_state.feature_engineering_code = feature_engineering_agent.get_feature_engineer_function()

    numeric_summary = df_final.describe()
    # categorical_summary = df_final.describe(include=['object', 'category', 'bool'])

    #############
    numeric_cols = df_final.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df_final.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    # Protect against weird columns
    safe_categorical_cols = []
    cat_cardinalities = {}
    top_cats = {}

    for col in categorical_cols:
        try:
            nunique = int(df_final[col].nunique())
            top_values = df_final[col].value_counts().head(3).to_dict()

            cat_cardinalities[col] = nunique
            top_cats[col] = top_values
            safe_categorical_cols.append(col)

        except Exception as e:
            st.warning(f"Skipping column `{col}` due to error: {e}")

    # Now use only the safe columns
    st.session_state.df_summary = numeric_summary
    st.session_state.metadata_string = (
        f"Columns: {list(df_final.columns)}\n"
        f"Numeric columns: {numeric_cols}\n"
        f"Categorical columns: {safe_categorical_cols} (cardinalities: {cat_cardinalities})\n"
        f"Top categories: {top_cats}\n"
        f"Row count: {len(df_final)}"
    )
    # st.write(st.session_state.metadata_string)

    root_question = generate_root_summary_question(st.session_state.metadata_string)
    if st.session_state.curr_state.nodes:
        root_node = st.session_state.curr_state.nodes[0]
        root_node.data["full_question"] = root_question
        root_node.data["content"] = dataset_name
        root_node.data["short_label"] = "ROOT"

    st.title('🧠 Mind Mapping + Agentic Exploration')

    if st.session_state.get("dataset_name"):
        root_node = st.session_state.curr_state.nodes[0]
        if root_node.data["content"] != st.session_state["dataset_name"]:
            root_node.data["content"] = st.session_state["dataset_name"]

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("🔄 Reset Mind Map"):
            dataset_label = st.session_state.get("dataset_name", "Dataset")
            new_root = StreamlitFlowNode(
                "S0",
                (0, 0),
                {
                    "section_path": "S0",
                    "short_label": "ROOT",
                    "full_question": st.session_state.metadata_string,
                    "content": dataset_label
                },
                "input",
                "right",
                style={"backgroundColor": COLOR_PALETTE[0]}
            )
            st.session_state.curr_state = StreamlitFlowState(nodes=[new_root], edges=[])
            st.session_state.expanded_nodes = set()
            st.session_state.clicked_questions = []
            st.rerun()

    # Render mind map
    st.session_state.curr_state = streamlit_flow(
        "mind_map",
        st.session_state.curr_state,
        layout=TreeLayout(direction="right"),
        fit_view=True,
        height=550,
        get_node_on_click=True,
        enable_node_menu=True,
        enable_edge_menu=True,
        show_minimap=False
    )