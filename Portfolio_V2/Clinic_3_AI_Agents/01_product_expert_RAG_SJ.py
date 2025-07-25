# GOAL: Make a product expert AI agent based on the RAG agent from Clinic #1

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Rag Agents
from langchain_chroma import Chroma
from langchain.document_loaders import WebBaseLoader
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

# Other Libraries
import pandas as pd
import joblib
import re
import os
import yaml

from pprint import pprint
from IPython.display import Markdown

# Backup to display mermaid graphs
from IPython.display import display, Image

MODEL = 'gpt-4.1-mini'
EMBEDDING = 'text-embedding-ada-002'

# * STEP 1: CREATE THE VECTOR DATABASE IF YOU HAVE ONE 


os.environ["OPENAI_API_KEY"] = yaml.safe_load(open('credentials.yml'))['openai']

# TEST OUT Loading a single webpage 
url = "https://sweetjames.com/personal-injury/car-accident-lawyers/"

# Create a loader for the website 
loader = WebBaseLoader(url)

# Load the data from the website 
documents = loader.load()

pprint(documents[0].metadata)


