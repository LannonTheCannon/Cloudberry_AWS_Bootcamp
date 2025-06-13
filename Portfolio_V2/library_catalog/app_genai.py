# BUSINESS SCIENCE UNIVERSITY
# PYTHON FOR GENERATIVE AI COURSE
# CHALLENGE - CREATE A CALL REPORT APP
# ***
# GOAL: Exposure to using LLM's, Document Loaders, and Prompts

# streamlit run 04-Bonus-Streamlit-App/01_bonus_call_report_app_pdf_download.py

import yaml
import streamlit as st

import subprocess
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tempfile import NamedTemporaryFile
import shutil

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from utils.ai_pipeline import get_openai_api_key
import openai

# Load API Key
openai.api_key = get_openai_api_key()
MODEL = 'gpt-3.5-turbo'

def generate_pdf_with_quarto(markdown_text):
    with NamedTemporaryFile(delete=False, suffix=".qmd", mode='w') as md_file:
        md_file.write(markdown_text)  # Write string directly
        md_file_path = md_file.name

    pdf_file_path = md_file_path.replace('.qmd', '.pdf')

    # Use the Quarto command line instead of Python integration for more complex rendering
    subprocess.run(["quarto", "render", md_file_path, "--to", "pdf"], check=True)

    os.remove(md_file_path)  # Clean up the Markdown file
    return pdf_file_path

def move_file_to_downloads(pdf_file_path):
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    destination_path = os.path.join(downloads_path, os.path.basename(pdf_file_path))
    shutil.move(pdf_file_path, destination_path)
    return destination_path

def load_and_summarize(file):
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.getvalue())
        file_path = tmp.name

    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        prompt_template = """
        Write a business report from the following earnings call transcript:
        {text}

        Use the following Markdown format:
        # Insert Descriptive Report Title

        ## Earnings Call Summary
        Use 3 to 7 numbered bullet points

        ## Important Financials:
        Describe the most important financials discussed during the call. Use 3 to 5 numbered bullet points.

        ## Key Business Risks
        Describe any key business risks discussed on the call. Use 3 to 5 numbered bullets.

        ## Conclusions
        Conclude with any overarching business actions that the company is pursuing that may have positive or negative implications and what those implications are. 
        """

        prompt = PromptTemplate.from_template(prompt_template)
        model = ChatOpenAI(
            model=MODEL,
            temperature=0,
            api_key=openai.api_key
        )

        llm_chain = LLMChain(llm=model, prompt=prompt)
        stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
        response = stuff_chain.invoke(docs)

    finally:
        os.remove(file_path)

    return response['output_text']

# Streamlit Interface
st.set_page_config(layout='wide', page_title="Call Transcript Summarizer")
st.title('Earnings Call Transcript Summarizer')
col1, col2 = st.columns(2)

with col1:
    st.subheader('Upload a PDF document:')
    uploaded_file = st.file_uploader("Choose a file", type="pdf", key="file_uploader")
    if uploaded_file:
        summarize_flag = st.button('Summarize Document', key="summarize_button")


if uploaded_file and summarize_flag:
    with col2:
        with st.spinner('Summarizing...'):
            summary = load_and_summarize(uploaded_file)
            st.subheader('Summarization Result:')
            st.markdown(summary)

            pdf_file = generate_pdf_with_quarto(summary)
            download_path = move_file_to_downloads(pdf_file)
            st.markdown(f"**PDF Downloaded to your Downloads folder: {download_path}**")

else:
    with col2:
        st.write("No file uploaded. Please upload a PDF file to proceed.")



