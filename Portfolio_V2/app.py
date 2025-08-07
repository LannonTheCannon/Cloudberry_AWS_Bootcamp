from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g, jsonify
)
from flask import Flask, send_from_directory

from flask_sqlalchemy import SQLAlchemy
from jinja2 import TemplateNotFound
from flask import abort
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import boto3
import pandas as pd
from io import BytesIO
import os
import sys
from utils.ai_pipeline import run_clean_pipeline, get_openai_api_key
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import openai
import time
# Try importing - if it fails, we'll define it inline
try:
    from utils.standalone_assistant_manager import StandaloneAssistantManager
except ImportError:
    print("Import failed, defining StandaloneAssistantManager inline...")
    pass 

# from utils.s3_secrets import get_s3_config

# ─── SETUP ──────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = 'MySecretKey'

# Add these lines to increase upload limits
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

try:
    if os.environ.get("FLASK_ENV") == "production":
        from utils.db_secrets import get_db_secret  # import only if needed
        print('prod environment dababy')
        secret = get_db_secret("prod/rds/dababy")
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{secret['username']}:{secret['password']}"
            f"@{secret['host']}:{secret['port']}/{secret['dbname']}"
        )
    else:
        raise RuntimeError("Development environment detected")

except Exception as e:
    print(f"🛯 Using SQLite fallback — reason: {e}")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alc_db.sqlite3'

db = SQLAlchemy(app)

# S3_BUCKET_NAME = get_s3_config()["bucket_name"]
# s3_client = boto3.client("s3", region_name="us-west-1")
S3_BUCKET_NAME = 'fish-pale'
s3_client = boto3.client("s3", region_name="us-west-2")

@app.route('/')
def home():
    # Get first 3 items as a dict
    featured_projects = dict(list(projects.items())[:3])
    return render_template('index.html', featured_projects=featured_projects, services=services)

# ─── MODELS ─────────────────────────────────────────────────────────────────────

class Contact(db.Model):
    __tablename__ = 'contact'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    message = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw, method='pbkdf2:sha256')

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class File(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    filesize = db.Column(db.Integer, nullable=False)
    filetype = db.Column(db.String(50))
    cleaned = db.Column(db.Boolean, default=False)
    cleaned_key = db.Column(db.String(512))

    user = db.relationship('User', backref='files')

# ─── Hero Section  ──────────────────────────────────────────────────────────────────────

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_input = data.get("query") if data else None
        # Your constants
    ASSISTANT_ID = 'asst_lWehPiZNA8pnJqZiIRf0oZjd'
    THREAD_ID = 'thread_SvWn7zjRtUFwjOMGHBYbRzjV'

    if not user_input or not user_input.strip():
        return jsonify({"error": "No query provided"}), 400

    try:
        # Create standalone assistant manager
        assistant_manager = StandaloneAssistantManager(
            api_key=get_openai_api_key(),
            assistant_id=ASSISTANT_ID,
            thread_id=THREAD_ID
        )
        
        # Get response
        response = assistant_manager.run_assistant(user_input)
        print(f'🔥 Assistant response: {response}')
        
        if response:
            return jsonify({"response": response})
        else:
            return jsonify({"error": "Failed to get assistant response"}), 500
            
    except Exception as e:
        print(f"🔥 Error in ask_openai: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    

# 🔥 Agent configurations with corrected system prompts
AGENT_CONFIGS = {
    "Data Visualization AI Agent": {
        "assistant_id": "asst_SrQiMK3v7lkZmUipEhY0ReIh",
        "system_prompt": "You are Nova, a data visualization AI specialist. You create interactive charts, dashboards, and visual narratives using tools like matplotlib, Plotly, Power BI, or Tableau. You help users turn raw data into insights through visual storytelling."
    },
    "Data Wrangling AI Agent": {
        "assistant_id": "asst_R5zIDy8Q3LW0TCcWdhlIPTj3", 
        "system_prompt": "You are Orion, a data wrangling expert. You help users clean messy datasets, merge files, remove duplicates, handle missing values, and restructure data using Python libraries like pandas and numpy."
    },
    "Feature Engineering AI Agent": {
        "assistant_id": "asst_RPlJ9yluhaAzS4Tj6TUvuAB5",
        "system_prompt": "You are Vega, a feature engineering expert. You extract meaningful features, create derived variables, encode categorical data, and transform data to improve model performance in machine learning workflows."
    },
    "Business SQL Agent": {
        "assistant_id": "asst_Bvd1I7VoqDYA8uoMFW4vBTSe",
        "system_prompt": "You are Cosmo, a SQL and business intelligence expert. You help users write and optimize SQL queries to retrieve, aggregate, and analyze business data from relational databases like PostgreSQL, MySQL, or BigQuery."
    },
    "Product Expert": {
        "assistant_id": "asst_XdJtC6N7BuT4PvVnw877KaFK",
        "system_prompt": "You are Luma, a vector search and RAG (retrieval-augmented generation) specialist. You assist users in building semantic search systems using tools like Chroma, FAISS, or Weaviate, and integrating them with LLMs via LangChain or OpenAI Assistants."
    },
    "Segment Analysis Agent": {
        "assistant_id": "asst_MQI4tSxv5NZZngwS9qOPKGR9",
        "system_prompt": "You are Atlas, a segmentation and ETL expert. You help with cohort analysis, customer segmentation, and automating data pipelines using tools like Apache Airflow, dbt, or custom Python scripts."
    },
    "Supervisor Agent": {
        "assistant_id": "asst_HuLj0I4GO4taz7qU7atKzRnC",
        "system_prompt": "You are Echo, a large language model evaluation specialist. You design tests to assess AI agent performance, consistency, and reasoning using metrics like BLEU, ROUGE, or custom eval frameworks."
    },
    "Marketing Email Writer": {
        "assistant_id": "asst_p0imYKyt9G0CTLD9Z5qqtcb3",
        "system_prompt": "You are Lyra, a marketing email copywriting expert. You craft compelling, conversion-focused emails tailored to various audiences, blending persuasive language with strategic calls to action."
    }
}

# 🔥 Store agent-specific thread IDs (in production, use a database)
agent_threads = {}

@app.route('/ask_agent', methods=['POST'])
def ask_agent():
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        agent_name = data.get('agent_name', '').strip()
        
        if not user_query:
            return jsonify({"error": "No query provided"}), 400
            
        if not agent_name or agent_name not in AGENT_CONFIGS:
            return jsonify({"error": f"Unknown agent: {agent_name}"}), 400
        
        print(f"🔥 Agent Query: {agent_name} - {user_query}")
        
        # Get agent config
        agent_config = AGENT_CONFIGS[agent_name]
        assistant_id = agent_config["assistant_id"]
        
        # 🔥 Get or create thread for this agent
        thread_id = agent_threads.get(agent_name)
        
        # 🔥 Create assistant manager (will create thread if needed)
        assistant_manager = StandaloneAssistantManager(
            api_key=get_openai_api_key(),
            assistant_id=assistant_id,
            thread_id=thread_id
        )
        
        # 🔥 Store the thread ID if it was newly created
        if agent_name not in agent_threads:
            agent_threads[agent_name] = assistant_manager.thread_id
            print(f"🔥 Stored new thread for {agent_name}: {assistant_manager.thread_id}")
        
        # Get response from the specific agent
        agent_response = assistant_manager.run_assistant(user_query)
        
        if agent_response:
            print(f"🔥 Agent Response from {agent_name}: {agent_response[:100]}...")
            
            return jsonify({
                "response": agent_response,
                "agent": agent_name,
                "thread_id": assistant_manager.thread_id
            })
        else:
            return jsonify({"error": "Failed to get agent response"}), 500
            
    except Exception as e:
        print(f"Error in ask_agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# ─── About Me Section  ──────────────────────────────────────────────────────────────────────

@app.route('/about')
def about():
    return render_template('about.html')

# ─── Projects Section  ──────────────────────────────────────────────────────────────────────

projects = {
    "data-forge-plus": {
        "title": "Data Forge Plus",
        "description": "Data Forge helps you ask the right questions on your dataset AND helps you visualize them.",
        "tech": ["Flask", "Streamlit", "AWS Lambda", "S3", "RDS", "OpenAI"],
        "author": "Lannon Khau",
        "image1": "static/images/magma.png",
        "icon": "static/images/forge_icon.svg",
        "template": "data-forge-plus.html",
        "login_req": "True",
    },
    "exo-land": {
        "title": "Exo-Explorer",
        "description": "Ever wanted to see what the surface of our nearest exoplanet, Kepler 22B, looked like?",
        "tech": ["Pandas", "Scikit-Learn", "OpenAI", "DALL·E", "Streamlit", "Flask"],
        "author": "Lannon Khau",
        "image1": "static/images/ship.jpg",
        "icon": "static/images/planet_icon.svg",
        "template": "exo-land.html",
        "login_req": "False",

    },
    "Octopus Books": {
        "title": "Octopus Books",
        "description": (
            "Generate a thorough and detailed summary of any book! This web app is for those who occasionally forget what they read and would like a summary of their current place in the book (no spoilers)!"
        ),
        "tech": ["OCR", "LangChain", "OpenAI", "Streamlit / Discord", "Pinecone", "PDF Parsing"],
        "author": "Lannon Khau",
        "image1": "static/images/octo.svg",
        "icon": "static/images/bookstar.png",
        "template": "quote-able.html",
        "login_req": "False",
    },
    "SJ Services Expert": {
        "title": "Sweet James Services Expert",
        "description": (
            "An AI-powered legal assistant that helps users understand and navigate Sweet James personal injury legal services."
        ),
        "tech": [
            "LangChain", 
            "LangGraph", 
            "OpenAI", 
            "Streamlit", 
            "ChromaDB", 
            "Vector Database", 
            "YAML Config", 
            "Session State"
        ],
        "author": "Lannon Khau",
        "image1": "static/images/justice_robot.png",
        "icon": "static/icons/sj_icon.svg",
        "template": "services-expert.html",
        "login_req": "False",
    }
}
@app.route('/projects')
def show_projects():
    return render_template('projects.html', projects=projects)

@app.route('/projects/<slug>')
def show_project(slug):
    project = projects.get(slug)
    if project:
        try:
            return render_template(
                f"projects/{project['template']}",
                title=project["title"],
                description=project["description"],
                tech=project["tech"],
                author=project["author"],
                image=project["image1"],
                services=services
            )
        except TemplateNotFound:
            abort(404)
    else:
        abort(404)

# --- Course Catalog Section -------------------------------------------------------------

# Create a blog style like library catalog where users can enter in different organized study tools
# materials and events. Like a blog thats organized for easy information access. It's a bit tricky i
# think that a true project manager at this point would command and conquer- with even just a bit of
# planning, this bootcamp can end up wit you at the top of the class again.

# Like my own personal library - always with me - always here for reference . stored in S3? this can
# be an expensive catalog - like maybe even 50 - 60 / month.. is it necessary at this moment?

# Now you should be complete the AI Fast Track course - and you should be learning what you did last
# course and doing what's better. Like focusing on creating an outstanding plan at the get go.

# Your portfolio, is a beautiful piece as is! And we're going to keep it running. We want to keep
# coming back to this because you are obsessed with this piece and want to make incremental yet consistent
# changes as you continue to nail down the AI portion. This is perfect for tseting on the chatbot as well
# as might changes like a library page and some blogs. Hell i know I could definitely benefit by getting
# some things off my chest in a blog or vlog or something.

# It can be a tracking system! it can be a catalog system! it can be a github project behavior dashboard.
# it can be a project catalog. It can be a POC. It can be a information hub and a website hub.
# I don't think i'd want to get into making courses - but honestly practice that would be really
# helpful for me. Making videos from what I've learned and just posting them daily would be a gamechanger

# cosmetic changes of course. Yeah - these changes need to stay up to date because its your portfolio! \
# Focus 20% of your time on portfolio building. Add a resume section!

# 80% of your time should be allocated to Matt Dancho's course. This mean 12-8PM everyday for the next 8
# weeks. Right off the bat, you need to do a bit of catch up but I was able to truly nail the last camp.
# At the BEST footing possible.

# Alright of course, the most important thing for me to do is to get my thoughts out there on paper
# Let's create the blog app as soon as possible. we'll figure out out how to do the library catalog later.
# 1) Create Blog
# Date - Data Forge Blog Series - #001 - Cloudberry AWS Full Stack Engineer Bootcamp Part 1
# Date - Data Forge Blog Series - #002 - Data Science for Business Gen AI Bootcamp Part 1



labs = {
    "cloudberry-bootcamp": {
        "title": "Full Stack AWS Bootcamp",
        "content": "OOP, Flask, AWS S3, RDS MySql, EC2",
        "author": "Cloudberry",
        "template": "cloudberry.html",
        "image": 'static/images/hoster.svg',
        "icon": 'static/images/cloudy.svg'
    },

    "gen-ai-bootcamp": {
        "title": "Gen AI for Data Science and Business Application",
        "content": "Bootcamp 2 (Data Science, ML/ AI/ Streamlit)",
        "author": "Business Science",
        "template": "gen_ai_bootcamp.html",
        "image": 'static/images/ai2.svg',
        "icon": 'static/images/ds4u.png'
    }
}

@app.route('/the_lab')
def show_lab():
    return render_template('the_lab.html', labs=labs)
@app.route("/the_lab/<slug>")
def lab_post(slug):
    lab = labs.get(slug)
    if lab:
        try:
            return render_template(
                f"labs/{lab['template']}",
                title=lab["title"],
                author=lab["author"],
                content=lab["content"]
            )
        except TemplateNotFound:
            abort(404)
    else:
        abort(404)


# ─── Blog Section  ──────────────────────────────────────────────────────────────────────
#
blogs = {
    "first-lms-system": {
        "title": "First LMS with over 135 concurrent users!",
        "description": "What I've learned launching a LMS on Flask designed for 6th-12th grade students.",
        "tech": ["Flask", "SQLAlchemy", "Bootstrap", "HTML/CSS", "Tkinter"],
        "content": "What I've learned launching a GUI on TKinter designed for 6th-12th grade students.",
        "author": "Lannon Khau",
        "image1": "static/images/learn.svg",
        "icon": "static/icons/1.svg",
        "template": "first-lms-system.html"
    },
    "rhombus-systems": {
        "title": "Hour of Code with Anaheim School District",
        "description": "Created many IoT projects that solved key issues during the Hour of Code sessions at Anaheim School District",
        "tech": ["Python", "Flask", "SQLAlchemy", "HTML/CSS", "Raspberry Pi", "SSH", "Arduino", "OpenCV"],
        "content": "I've built a camera module that could keep track of student check-in/check-out IoT parts which saved thousands in missing parts per annum.",
        "author": "Lannon Khau",
        "image1": "static/images/mars.png",
        "icon": "static/icons/2.svg",
        "template": "rhombus-systems.html"
    },
    # "Python Entry Level Certification Exam": {
    #     "title": "Python Entry Level Certification Exam",
    #     "description": "What I've learned preparing for the Python Entry Level Certification Exam.",
    #     "tech": ["Python", "Flask", "SQLAlchemy", "HTML/CSS", "Bootstrap"],
    #     "content": "What I've learned preparing for the Python Entry Level Certification Exam.",
    #     "author": "Lannon Khau",
    #     "image1": "static/images/bronze.png",
    #     "icon": "static/icons/2.svg",
    #     "template": "pcep_exam.html"
    # },
    "hack-fy2025": {
        "title": "Microsoft Hackathan Reactor FY2025",
        "description": "Microsoft AI Agents Hackathon was an incredible experience. My one key takeaway is that innovation and creativity is born from urgency, chaos and limited resources.",
        "tech": ["Python", "Flask", "SQLAlchemy", "HTML/CSS", "Streamlit", "LangChain", "OpenAI"],
        "content": "What I've learned preparing for the Microsoft Hackathan Reactor FY2025.",
        "author": "Lannon Khau",
        "image1": "static/images/competition.jpg",
        "icon": "static/icons/3.svg",
        "template": "hack-fy2025.html"
    },
    "marketing-analytics-team": {
        "title": "AI Marketing Analytics Team",
        "description": "How to build an AI-powered marketing analytics team from the ground up using Python and generative AI.",
        "tech": ["Python", "Flask", "SQLAlchemy", "Streamlit", "LangChain", "OpenAI"],
        "content": "Step-by-step playbook for setting up AI-driven marketing analytics: collect data, automate insights, and build dashboards that matter. Fast, actionable, and scalable.",
        "author": "Lannon Khau",
        "image1": "static/images/ai_team.png",
        "icon": "static/icons/purp.svg",
        "template": "playbook1.html"
    },
    "jupyter-kernel-setup": {
        "title": "Jupyter Kernel and Virtual Environment Setup",
        "description": "How to set up a Jupyter kernel for your data science projects.",
        "tech": ["Python", "Jupyter", "Docker"],
        "content": "Step-by-step guide for configuring Jupyter kernels to streamline your data science workflow.",
        "author": "Lannon Khau",
        "image1": "static/images/jupiter_kernel.png",
        "icon": "static/icons/jupiter.svg",
        "template": "jupyter-kernel-setup.html"
    },

}

@app.route('/blog')
def show_blog():
    return render_template('blog.html', blogs=blogs)


@app.route('/blog/<slug>')
def show_blog_post(slug):
    blog = blogs.get(slug)
    if blog:
        try:
            return render_template(
                f"blog/{blog['template']}",
                title=blog["title"],
                author=blog["author"],
                content=blog["content"],
                services=services
            )
        except TemplateNotFound as e:
            print(f"Template not found: {e}")
            abort(404)
    else:
        print(f"No blog found for slug: {slug}")
        abort(404)


# ─── Services Section  ──────────────────────────────────────────────────────────────────────

services = {
    "data-visualization-ai-agent": {
        "title": "Data Visualization AI Agent",
        "description": "Generate Interactive Plotly Dashboards",
        "tech": ["LangChain", "OpenAI", "Streamlit", "Pandas AI", "NL2SQL", "RAG Pipelines"],
        "content": (
            "You are Nova, a data visualization AI specialist. You combine RAG pipelines with tools like Pandas AI, "
            "Streamlit, and Plotly to produce conversational dashboards. You help business leaders and analysts explore data "
            "visually through natural language and generate interactive visual insights that reveal underlying patterns."
        ),
        "team": ["product-expert", "business-sql-agent", "marketing-email-writer"],
        "author": "Lannon Khau",
        "image1": "/static/images/agent1.jpg",
        "icon": "/static/images/agent1.jpg",
        "template": "data-vis-agent.html"
    },

    "data-wrangling-ai-agent": {
        "title": "Data Wrangling AI Agent",
        "description": "Automate Data Cleaning and Transformation",
        "tech": ["Flask", "React", "TailwindCSS", "SQLAlchemy", "AWS", "Docker"],
        "content": (
            "You are Orion, a data wrangling expert. You automate dataset ingestion, cleanup, and transformation "
            "using Flask and React across full-stack systems. You work with SQLAlchemy and Dockerized services to ensure "
            "data systems remain clean, scalable, and production-ready."
        ),
        "team": ["product-expert", "business-sql-agent", "marketing-email-writer"],
        "author": "Lannon Khau",
        "image1": "/static/images/agent2.jpg",
        "icon": "/static/images/agent2.jpg",
        "template": "data-wrangling-agent.html"
    },

    "feature-engineering-ai-agent": {
        "title": "Feature Engineering AI Agent",
        "description": "Extract and Transform Features for ML",
        "tech": ["Python", "Pandas", "NumPy", "Scikit-learn", "Pickle", "SQL", "Airflow"],
        "content": (
            "You are Vega, a feature engineering expert. You specialize in transforming messy data into model-ready formats. "
            "You perform one-hot encoding, feature scaling, time-series transformations, and other preprocessing tasks "
            "using Python, Pandas, NumPy, and Scikit-learn to optimize ML pipelines."
        ),
        "team": ["product-expert", "business-sql-agent", "marketing-email-writer"],
        "author": "Lannon Khau",
        "image1": "/static/images/agent3.jpg",
        "icon": "/static/images/agent3.jpg",
        "template": "feature-engineering-agent.html"
    },

    "business-sql-agent": {
        "title": "Business SQL Agent",
        "description": "Translate Natural Language to SQL",
        "tech": ["LangChain", "OpenAI", "SQL", "PostgreSQL", "Flask", "NL2SQL"],
        "content": (
            "You are Cosmo, a SQL expert focused on business intelligence. You interpret natural language and generate accurate, "
            "optimized SQL queries using tools like LangChain and NL2SQL. You help teams uncover insights from databases like "
            "PostgreSQL without needing to write complex queries manually."
        ),
        "team": ["product-expert", "data-visualization-ai-agent", "marketing-email-writer"],
        "author": "Lannon Khau",
        "image1": "/static/images/agent4.jpg",
        "icon": "/static/images/agent4.jpg",
        "template": "sql-agent.html"
    },

    "product-expert": {
        "title": "Product Expert",
        "description": "Vector Search and Semantic Retrieval",
        "tech": ["LangChain", "OpenAI", "ChromaDB", "PDF Parsers", "Tiktoken", "Pinecone"],
        "content": (
            "You are Luma, a RAG and vector search specialist. You build systems that retrieve contextual information "
            "from embeddings using tools like Chroma, Pinecone, and LangChain. You help reduce hallucinations and provide "
            "semantically relevant answers for AI-powered apps."
        ),
        "team": ["business-sql-agent", "data-wrangling-ai-agent", "marketing-email-writer"],
        "author": "Lannon Khau",
        "image1": "/static/images/agent5.jpg",
        "icon": "/static/images/agent5.jpg",
        "template": "rag-qa-agent.html"
    },

    "etl-automation-agent": {
        "title": "ETL Automation Agent",
        "description": "Automate and Scale Data Pipelines",
        "tech": ["Airflow", "Pandas", "SQL", "AWS Lambda", "S3", "PostgreSQL"],
        "content": (
            "You are Atlas, an ETL automation expert. You orchestrate data ingestion and cleaning jobs using Airflow, "
            "PostgreSQL, AWS Lambda, and S3. Your mission is to automate and scale pipelines for structured, reliable data movement."
        ),
        "team": ["product-expert", "business-sql-agent", "marketing-email-writer"],
        "author": "Lannon Khau",
        "image1": "/static/images/agent6.jpg",
        "icon": "/static/images/agent6.jpg",
        "template": "etl-agent.html"
    },

    "llm-evaluation-agent": {
        "title": "LLM Evaluation Agent",
        "description": "Test and Benchmark Language Models",
        "tech": ["Python", "Jupyter", "LangChain", "OpenAI Eval", "Datasets", "JSONL"],
        "content": (
            "You are Echo, a large language model evaluation specialist. You assess LLM performance across datasets using "
            "custom evals, regression testing, and prompt variation analysis. Your job is to track hallucinations, response quality, "
            "and improve models iteratively with precision."
        ),
        "team": ["product-expert", "data-visualization-ai-agent", "marketing-email-writer"],
        "author": "Lannon Khau",
        "image1": "/static/images/agent7.jpg",
        "icon": "/static/images/agent7.jpg",
        "template": "llm-eval-agent.html"
    },

    "marketing-email-writer": {
        "title": "Marketing Email Writer",
        "description": "Generate Persuasive Email Campaigns",
        "tech": ["Flask", "JWT", "OAuth2", "SQLAlchemy", "Firebase", "AWS Cognito"],
        "content": (
            "You are Lyra, a marketing email copywriting expert. You create persuasive, audience-tailored email content for AI tools, "
            "dashboards, and data platforms. Your writing drives engagement, communicates value clearly, and moves users to action."
        ),
        "team": ["product-expert", "data-visualization-ai-agent", "business-sql-agent"],
        "author": "Lannon Khau",
        "image1": "/static/images/agent8.jpg",
        "icon": "/static/images/agent8.jpg",
        "template": "user-auth-agent.html"
    }
}

# On the dashboard i'd like to see how many missions they've been on
# which teams each agent is has been on 
# some basic statistics in the mission log like "I just analyzed 300 reports in less than 23 minutes"
# which projects? or that kind of sounds like mission 
# 


@app.route('/service')
def show_service():
    return render_template('service.html', services=services)


@app.route('/service/<slug>')
def show_service_post(slug):
    service = services.get(slug)
    if service:
        try:
            return render_template(
                f"service/{service['template']}",
                title=service["title"],
                author=service["author"],
                content=service["content"]
            )
        except TemplateNotFound as e:
            print(f"Template not found: {e}")
            abort(404)
    else:
        print(f"No service found for slug: {slug}")
        abort(404)

# ─── Contact Section  ──────────────────────────────────────────────────────────────────────

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        # Handle storing or sending the message here
        flash("Thanks for reaching out!", "success")

        if name and email and message:
            contact = Contact(name=name, email=email, message=message)
            db.session.add(contact)
            db.session.commit()
            return redirect(url_for("home"))

    return render_template("contact.html")

# ─── HELPERS ─────────────────────────────────────────────────────────────────────

@app.before_request
def load_logged_in_user():
    user_id  = session.get('user_id')
    #g.user   = User.query.get(user_id) if user_id else None

    g.user = db.session.get(User, user_id) if user_id else None

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.path))
        return view(**kwargs)
    return wrapped_view

# ─── Data Forge Plus Section  ──────────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not username or not password or not confirm_password:
            flash("Username and Password are required.")
            return render_template("register.html", action="Register")

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register", username=username))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.")
            return render_template("register.html", action="Register")

        # All good: create user
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created.')
        return render_template("login.html", action='Sign In')

    # GET request — render blank form
    return render_template("register.html", action="Register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials.")

    return render_template("login.html", action='Log In')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        f = request.files.get('file')

        if f:
            try:
                print("📎 Step 1: File selected")

                # Save file size before anything else
                f.seek(0, 2)  # move to end of file
                size = f.tell()
                f.seek(0)     # reset to beginning

                key = f"uploads/{g.user.id}/{f.filename}"

                # Upload to S3
                s3_client.upload_fileobj(f, S3_BUCKET_NAME, key)
                print("🪣 Step 2: Upload to S3 successful")

                # Save to DB
                new_file = File(
                    user_id=g.user.id,
                    filename=f.filename,
                    s3_key=key,
                    filetype=f.filename.split('.')[-1].lower(),
                    filesize=size
                )
                db.session.add(new_file)
                db.session.commit()
                print("🧱 Step 3: DB commit complete")

            except Exception as e:
                print(f"❌ Upload failed: {e}")

        else:
            print("⚠️ No file selected.", "warning")
        return redirect(url_for("dashboard"))

    # GET — load all files
    files = File.query.filter_by(user_id=g.user.id).order_by(File.uploaded_at.desc()).all()
    return render_template('dashboard.html', files=files, user=g.user)

@app.route('/preview/<int:file_id>')
@login_required
def preview_file(file_id):
    # Fetch the file from the DB and verify ownership
    file = File.query.get_or_404(file_id)
    if file.user_id != g.user.id:
        flash("Unauthorized access to file.", 'danger')
        return redirect(url_for('dashboard'))

    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file.s3_key)
        df  = pd.read_csv(BytesIO(obj['Body'].read()))
        preview_html  = df.head().to_html(classes='data')
        describe_html = df.describe().to_html(classes='data')

        columns = df.columns.tolist()
        rows = df.head().to_dict(orient='records')

        return render_template("preview.html",
                       filename=file.filename,
                       columns=columns,
                       rows=rows,
                       describe=describe_html)

    except Exception as e:
        flash(f"Preview error: {e}", 'danger')
        return redirect(url_for('dashboard'))

# ---- AI Data Science Team Agent -----------------------------------#

@app.route('/clean/<int:file_id>', methods=["POST"])
@login_required
def clean_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != g.user.id:
        # flash('Unauthorized access to file.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # Load from S3
        s3_obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file.s3_key)
        df = pd.read_csv(BytesIO(s3_obj['Body'].read()))

        # Run AI pipeline
        df_cleaned = run_clean_pipeline(df)

        # Upload cleaned file
        buffer = BytesIO()
        df_cleaned.to_csv(buffer, index=False)
        buffer.seek(0)

        cleaned_key = f"cleaned/{g.user.id}/{file.filename}"
        s3_client.upload_fileobj(buffer, S3_BUCKET_NAME, cleaned_key)

        # Update db
        file.cleaned = True
        file.cleaned_key = cleaned_key
        db.session.commit()

        # flash("Cleaning complete!", "success")

    except Exception as e:
        flash(f"Cleaning error: {e}", "danger")


    # 🔁 This line must exist outside the try/except block too
    return redirect(url_for('dashboard'))


@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    file = File.query.get_or_404(file_id)

    if file.user_id != g.user.id:
        print("Unauthorized attempt to delete file.")
        return redirect(url_for('dashboard'))

    try:
        # Delete raw file
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file.s3_key)
        print(f"🗑️ Deleted raw: {file.s3_key}")

        # Delete cleaned file if exists
        if file.cleaned_key:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file.cleaned_key)
            print(f"🗑️ Deleted cleaned: {file.cleaned_key}")

        db.session.delete(file)
        db.session.commit()
        print(f"✅ DB record removed for {file.filename}")

    except Exception as e:
        print(f'Delete Error: {e}', 'danger')

    return redirect(url_for('dashboard'))



@app.route('/api/file/<int:file_id>')
@login_required
def get_file_info(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != g.user.id:
        return {"error": "unauthorized"}, 401
    return {"cleaned_key": file.cleaned_key}




# This is for getting the logs from data cleaning step
@app.route('/logs/<int:file_id>')
def get_logs(file_id):
    file = File.query.get(file_id)
    if not file:
        return jsonify({"status": "not_found", "logs": []})

    logs = get_current_logs(file_id)  # This should return a list of strings
    status = "pending"
    if file.cleaned:
        status = "cleaned"
    elif file.cleaning:
        status = "cleaning"
    elif file.failed:
        status = "failed"

    return jsonify({"status": status, "logs": logs})

@app.route("/diagram")
def serve_diagram():
    return send_from_directory("static/react-diagram", "index.html")

@app.route("/diagram/<path:path>")
def serve_diagram_assets(path):
    return send_from_directory("static/react-diagram", path)

#------------------------ Front facing chatbot ---------------------------------------#


if __name__ == '__main__':
    print("Running db.create_all()")
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
