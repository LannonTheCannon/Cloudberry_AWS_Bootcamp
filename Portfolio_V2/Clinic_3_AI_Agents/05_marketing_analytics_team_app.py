# BUSINESS SCIENCE UNIVERSITY
# PYTHON FOR GENERATIVE AI COURSE
# AI MARKETING ANALYTICS AGENT
# ***

# GOAL: Streamlit chat interface for Marketing Analytics Team
# Tracks: email_subject, email_body, email_list, plots/data, intermediate responses

# Command Line:
#   streamlit run app.py

# LIBRARIES ----
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import warnings
import uuid

from langchain_core.messages import HumanMessage, AIMessage

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langgraph.checkpoint.memory import MemorySaver

from marketing_analytics_team.teams import make_marketing_analytics_team


warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

# -- Constants & Config ------------------------------------------------------
CHAT_LLM_OPTIONS   = [
    # "gpt-4.1-nano", # Don't use this one, it's too small
    "gpt-4.1-mini", 
    "gpt-4.1", 
    "gpt-4o-mini", 
    "gpt-4o"
]
EMBEDDING_OPTIONS  = ["text-embedding-ada-002"]
PATH_TRANSACTIONS_DB = "sqlite:///data/database-sql-transactions/leads_scored.db"
PATH_PRODUCTS_VDB     = "data/data-rag-product-information/products_clean.db"

# -- Streamlit Page Setup ---------------------------------------------------
TITLE = "AI Marketing Analytics Team"
st.set_page_config(
    page_title=TITLE,
    page_icon=":bar_chart:",
    layout="wide"
)
st.title(TITLE)


with st.expander("I'm a complete marketing analytics copilot that contains a team of experts: Business intelligence SQL Expert, Product Expert, Marketing email writer. (see example questions)"):
    st.markdown(
        """
        #### Business Intelligence
        
        - What tables are in the SQL database?
        - What does the leads_scored table look like?
        - What are the top 10 customers by revenue?
        - Draw a bar chart of the top 10 customers by revenue.
        
        #### Product Expert
        
        - What are the key features of the 5-Course R-Track?
        - What products are available in the database?
        
        #### Marketing Email Writer
        
        - Find the top 20 email subscribers ranked by probability of purchase (p1 lead score in the leads_scored table) who have not purchased any courses yet? Have the Product Expert collect information on the 5-Course R-Track for use with the Marketing Expert. Have the Marketing Expert write a compelling marketing email.
        - Have the marketing email writer remove Kamryn Tremblay from the email list. Do not use any other agents.
        
        """
    )


# -- Sidebar: Controls & Summary ---------------------------------------------
with st.sidebar:
    st.header("Settings")
    model_option         = st.selectbox("OpenAI Model", CHAT_LLM_OPTIONS)
    embed_option         = st.selectbox("Embedding Model", EMBEDDING_OPTIONS)
    add_short_term_memory = st.checkbox("Add Short-Term Memory", value=True)
    show_reasoning       = True
    if add_short_term_memory:
        if st.button("Clear Chat History"):
            msgs = StreamlitChatMessageHistory(key="marketing_messages")
            msgs.clear()
            msgs.add_ai_message("How can I help with your marketing analytics today?")
            st.session_state.details = []
            # Clear checkpointer state (MemorySaver is in-memory, so just reinitialize)
            st.session_state.checkpointer = MemorySaver()
    else:
        st.session_state.checkpointer = None

# -- Cache the Checkpointer --------------------------------------------------
@st.cache_resource
def get_checkpointer():
    """Initialize and cache the LangGraph MemorySaver checkpointer."""
    return MemorySaver()

# -- Initialize Session State -----------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())  # Unique thread ID per session
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = get_checkpointer()  # Cache checkpointer
if "details" not in st.session_state:
    st.session_state.details = []

# -- Initialize History & Detail Store --------------------------------------
msgs = StreamlitChatMessageHistory(key="marketing_messages")
if not msgs.messages:
    msgs.add_ai_message("How can I help with your marketing analytics today?")

# -- Function to Render Chat ------------------------------------------------
def display_chat_history():
    for i, msg in enumerate(msgs.messages):
        with st.chat_message(msg.type):
            content = msg.content
            if content.startswith("DETAILS_INDEX:"):
                idx = int(content.split(":")[1])
                detail = st.session_state.details[idx]
                with st.expander("Marketing Analysis", expanded=True):
                    tabs = st.tabs(["AI Reasoning", "SQL Query", "Plot/Data", "Email & List"])
                    with tabs[0]:
                        text = detail.get("reasoning", "_(No reasoning available)_")
                        if show_reasoning:
                            st.write(text)
                        else:
                            st.info("Enable 'Show AI Reasoning' in sidebar to view intermediate thoughts.")
                    with tabs[1]:
                        sql = detail.get("sql_query")
                        if sql:
                            st.code(sql, language="sql")
                        else:
                            st.info("No SQL query generated.")
                    with tabs[2]:
                        if detail.get("chart_json"):
                            fig = pio.from_json(detail["chart_json"])
                            st.plotly_chart(fig, key=f"plot_data_{i}")
                        elif detail.get("data") is not None:
                            df = pd.DataFrame(detail["data"])
                            st.dataframe(df)
                        else:
                            st.info("No plot or data returned.")
                    with tabs[3]:
                        st.markdown("**Subject:**")
                        st.write(detail.get("title", ""))
                        st.markdown("**Body:**")
                        st.write(detail.get("body", ""))
                        st.markdown("**Recipients:**")
                        st.write(detail.get("list", []))
            else:
                st.write(content)

# -- Initialize LLM & Team --------------------------------------------------
llm = ChatOpenAI(model=model_option)
embeddings = OpenAIEmbeddings(model=embed_option)

marketing_team = make_marketing_analytics_team(
    model=llm,
    model_embedding=embeddings,
    path_products_vector_db=PATH_PRODUCTS_VDB,
    path_transactions_sql_db=PATH_TRANSACTIONS_DB,
    
    # Short Term Memory
    checkpointer=st.session_state.checkpointer,
)

# -- Handle User Input & AI Response ----------------------------------------
if prompt := st.chat_input("Enter your marketing analytics request here…"):

    with st.spinner("Thinking..."):    
        # 2. Add user message
        st.chat_message("human").write(prompt)
        msgs.add_user_message(prompt)

        try:
            result = marketing_team.invoke(
                input={
                    "messages": [HumanMessage(content=prompt)]
                },  
                config={
                    "recursion_limit": 10, 
                    "configurable": {
                        # *New: Implement session specific thread_id
                        "thread_id": st.session_state.thread_id
                    }
                }
            )
        except Exception as e:
            st.error("Error invoking marketing team.")
            print(e)
            result = None

    if result:
        
        recipients = result.get("email_list", [])
        
        # 3. Collect reasoning with agent names, only for AI messages after the latest Human message
        reasoning = ""
        latest_human_index = -1
        for i, message in enumerate(result.get("messages", [])):
            if isinstance(message, HumanMessage):
                latest_human_index = i  # Track the index of the latest Human message
        for message in result.get("messages", [])[latest_human_index + 1:]:  # Process only messages after the latest Human message
            if isinstance(message, AIMessage):
                reasoning += f"##### {message.name}:\n\n{message.content}\n\n---\n\n"
        
        # 4. Collect detail
        detail = {
            "reasoning": reasoning,
            "sql_query": result.get("sql_query"),
            "chart_json": result.get("chart_plotly_json"),
            "data": result.get("data"),
            "title": result.get("email_subject"),
            "body": result.get("email_body"),
            "list": recipients,
        }
        idx = len(st.session_state.details)
        st.session_state.details.append(detail)
        msgs.add_ai_message(f"DETAILS_INDEX:{idx}")

# Render current messages from StreamlitChatMessageHistory
display_chat_history()
