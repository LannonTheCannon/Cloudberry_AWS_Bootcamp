
# Cloudberry_AWS_Bootcamp / Portfolio_V2

This repository contains the full production-grade source code for **Lannon Khau's Portfolio** and **Data Forge Plus**, running simultaneously via Flask and Streamlit on AWS infrastructure.

## 🧠 About the Project

This project started as an idea to process 1.3 million rows of financial data interactively. Over time, it evolved into a powerful AI-powered web application that can accept **any size dataset**, clean it, perform feature engineering, and visualize it in an intuitive UI—all powered by GPT-4o, LangChain, and serverless AWS tools.

## 🌐 Live Architecture

**Hosted on AWS:**
- **EC2**: Flask backend with Gunicorn and Nginx serving the app
- **S3**: Securely store and manage user-uploaded datasets
- **RDS (MySQL)**: Persistent metadata storage for file uploads and user sessions
- **AWS Lambda**: Clean + feature engineer CSV files asynchronously using OpenAI agents
- **AWS Secrets Manager**: Manages the OpenAI API key securely
- **GitHub Actions**: Automate deployment and continuous integration

## 🛠️ Tech Stack

| Layer           | Tools & Libraries                                             |
|----------------|---------------------------------------------------------------|
| Backend         | Flask, Gunicorn, Python                                       |
| Frontend        | HTML, TailwindCSS, Jinja2, Streamlit                          |
| AI Agents       | OpenAI GPT-4o, LangChain, AI_Data_Science_Team               |
| Infrastructure  | AWS EC2, S3, Lambda, RDS (MySQL), Secrets Manager             |
| CI/CD           | GitHub Actions                                                |

## 🧹 Data Pipeline (AI-Powered)

1. **File Upload**
    - Users can upload CSVs directly via a secure Flask interface.
    - Streamlit limited uploads to ~200MB—AWS S3 solves this by offloading upload limits.

2. **Cleaning & Feature Engineering**
    - Datasets are cleaned and transformed by AI agents via AWS Lambda.
    - All results are stored in `cleaned/` S3 prefix and logged to RDS.

3. **Exploration & Visualization**
    - Users can launch "Explore" to view AI-generated insights and mind maps via Streamlit.
    - PandasAI + custom LangChain visual chains power the plots.

## 📁 Repository Structure

```
Cloudberry_AWS_Bootcamp/
│
├── Portfolio_V2/                  # Core Flask app
│   ├── app.py                     # Entrypoint Flask application
│   ├── templates/                 # Jinja2 HTML templates
│   ├── static/                    # TailwindCSS and JS
│   ├── utils/                     # AI pipeline, S3 handlers, and secrets manager
│   ├── data_forge_lite/          # Streamlit-powered exploration dashboard
│   └── requirements.txt
│
├── .github/workflows/            # GitHub Actions CI/CD scripts
├── README.txt                    # You're reading it!
└── start.sh                      # Launch script for Gunicorn
```

## ⚙️ Running Locally

1. Clone the repo:
```bash
git clone https://github.com/LannonTheCannon/Cloudberry_AWS_Bootcamp.git
cd Cloudberry_AWS_Bootcamp/Portfolio_V2
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Set your environment variables:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
```

4. Run the app:
```bash
flask run
```

## 🧪 How It Works

- **User uploads data** via the Flask Dashboard.
- File is stored in S3, and metadata goes to RDS.
- Lambda function (triggered manually) calls `DataCleaningAgent` and `FeatureEngineeringAgent`.
- Cleaned file is stored in `cleaned/` S3 path.
- Streamlit loads cleaned preview and launches EDA mind map + visualization UI.

## 🚧 Known Limitations

- Streamlit’s native file uploader has strict limits (~200MB).
- Resolved via AWS S3 upload redirection and server-side processing.

## 🏁 Roadmap

- ✅ Secure upload to S3
- ✅ Multi-agent AI cleaning pipeline
- ✅ RDS + Lambda integration
- ✅ Streamlit visual dashboard
- ⏳ Real-time Lambda progress UI
- ⏳ Role-based access (Admin, Viewer)
- ⏳ Public visualization share mode

## 🙌 Credits

- **Lannon Khau** – Full-stack developer, AI engineer, and builder of the Data Forge ecosystem
- Built using:
    - [LangChain](https://www.langchain.com/)
    - [OpenAI](https://platform.openai.com/)
    - [AWS](https://aws.amazon.com/)
    - [Flask](https://flask.palletsprojects.com/)
    - [Streamlit](https://streamlit.io/)

## 📬 Contact

If you're interested in using this platform internally for your team, or just want to jam on ideas—reach out at [lannonkhau@gmail.com](mailto:lannonkhau@gmail.com)

---

© 2025 Lannon Khau. All rights reserved.
