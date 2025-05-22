Project Title: Portfolio_V2 – AI-Enhanced Data Project Portfolio

⸻

📌 Summary

Portfolio_V2 is a full-stack, production-ready portfolio application designed to showcase a suite of AI-powered data projects. The app includes a custom landing page, user authentication, AWS-integrated dataset upload and cleaning features, and a seamless bridge to an interactive Streamlit-based EDA tool. Built using Flask, Tailwind, AWS (EC2, S3, RDS), and GitHub Actions, the platform reflects best practices in cloud-first development and modular AI-driven data workflows.

⸻

🎯 Core Features

🔗 Landing Page (Custom Built, No Template Frameworks)
	•	Minimalist Tailwind-based UI
	•	Hero section with call-to-actions
	•	Navigation bar: Home, Blog, Projects, Contact, About Me
	•	Project Showcases: Data-Forge-Plus, Task Master Plus, Data Forge Lite
	•	Featured Blog Cards: First Hackathon, Completed Cloudberry
	•	Footer with links and credits

🔐 Authentication
	•	User registration/login with hashed password storage (SQLite → RDS MySQL)
	•	Includes a persistent session + home navigation button

📁 User Dashboard (Data-Forge-Plus Page)
	•	Upload up to 5 datasets per session (to S3)
	•	Preview uploaded datasets
	•	Track cleaning/feature engineering job status (queued or complete)
	•	AI-driven cleaning via AI_Data_Science_Team agent suite on AWS Lambda
	•	Queue multiple jobs concurrently
	•	After job completion, launch Explore via Streamlit

📊 EDA Integration with Streamlit
	•	Connects cleaned datasets (sampled ~1000 rows) to Data Forge Lite
	•	Visual exploration powered by:
	•	AI-generated mind maps
	•	Summary statistics
	•	Interactive charts (Pandas, Plotly)
	•	Code editor for live AI-powered modifications

🚧 In-Progress Setup
	•	Finalize basic Flask app (app.py, requirements, templates/static, venv)
	•	SSH access via PEM + alias setup (lannonwill)
	•	EC2 production deployment with WSGI + Gunicorn
	•	GitHub Actions workflow
	•	Switch SQLite to RDS for persistent user/file tracking
	•	Streamlit EC2 deployment finalized and linked
	•	Tailwind responsive tuning for production

⸻

📈 Milestone Vision
	•	Launch a portfolio-quality demo of Data-Forge-Plus
	•	Show seamless user journey: login → upload → clean → explore
	•	Showcase real-time AI-powered transformation
	•	Post walkthrough on LinkedIn with visuals and demo link
	•	Gather feedback from peers and potential collaborators


TECH STACK

Component
Tech
Frontend Flask + Tailwind CSS
Authentication & Routing Flask + Jinja2
Database (Local/Prod) SQLite (dev) → AWS RDS (prod)
File Storage AWS S3 (dataforge-uploader-bucket)
Serverless Processing AWS Lambda
AI Agents GPT-4o-mini via AI_Data_Science_Team
EDA Interface Streamlit (hosted on EC2)
Deployment EC2 (WSGI + Gunicorn)
CI/CD GitHub Actions
