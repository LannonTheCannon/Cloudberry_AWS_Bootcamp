import streamlit as st

# Set up page config
st.set_page_config(page_title="Bootcamp Notes", layout="wide")

# Sidebar navigation
st.sidebar.title("🧪 The Lab")
section = st.sidebar.radio("Navigate", ["📚 Table of Contents", "Week 1", "Week 2", "Week 3", "Week 4", "Week 5"])

# Main display logic
st.title("📘 Bootcamp Learning Catalog")

if section == "📚 Table of Contents":
    st.header("Welcome to The Lab")
    st.markdown("""
    This is your personal lab space — a place to document, demo, and reflect on everything you're learning throughout the bootcamp.

    ### 🧭 Sections:
    - **Week 1**: Foundations & Setup
    - **Week 2**: APIs, Flask & EC2
    - **Week 3**: Streamlit & Data Wrangling
    - **Week 4**: Cloud Deployments
    - **Week 5**: AI Agents & Final Projects
    """)

    with st.expander("📦 Bonus Tools"):
        st.info("Try using `streamlit run app.py` from your EC2 machine to launch this demo.")

elif section == "Week 1":
    st.subheader("🛠️ Week 1: Bootcamp Setup & Foundations")
    st.markdown("Focus: AWS Console, GitHub SSH, Flask basics")

    st.code("flask run --host=0.0.0.0", language="bash")

    with st.echo():
        # Echo block to display both code + output
        st.write("✅ Flask App Running Successfully")
        st.success("Hello from Flask!")

    st.text_input("🔐 Enter your PEM file name:")
    st.checkbox("I have added my SSH key to GitHub")

elif section == "Week 2":
    st.subheader("🔌 Week 2: Flask, APIs & Cloud")
    st.markdown("This week you built REST APIs and deployed Flask to EC2.")

    code_example = """
@app.route("/api/healthcheck")
def ping():
    return {"status": "ok"}
"""
    st.code(code_example, language="python")

    st.metric("API Uptime", "99.9%", "+0.3%")

elif section == "Week 3":
    st.subheader("📊 Week 3: Streamlit Dashboards & Pandas")
    st.markdown("You started building interactive dashboards.")

    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart({"visitors": [100, 120, 150, 80]})
    with col2:
        st.line_chart([1, 5, 2, 6, 4])

    st.text_area("Paste CSV data snippet")

elif section == "Week 4":
    st.subheader("🚀 Week 4: Cloud Deployments & Streamlit Tricks")
    st.markdown("How to deploy Streamlit apps via nohup on EC2")

    st.code("nohup streamlit run app.py --server.port=8502 &", language="bash")

    progress = st.progress(0)
    for i in range(1, 101):
        progress.progress(i)

elif section == "Week 5":
    st.subheader("🤖 Week 5: Agents, AI, and LangChain")
    st.markdown("Welcome to agentic workflows. Meet `PandasDataAnalyst` and `LangChain`.")

    st.selectbox("Choose an agent", ["Data Cleaner", "Visualizer", "Summarizer"])
    st.code("""
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4.1-mini")
""", language="python")

    st.warning("Agents need environment variables to work! Don't forget your API keys.")

# Footer
st.markdown("---")
st.caption("Built with ❤️ by Lannon Khau • 2025")