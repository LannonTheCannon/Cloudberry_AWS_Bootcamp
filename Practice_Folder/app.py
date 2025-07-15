from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging
import boto3
import os
from dotenv import load_dotenv
import pandas as pd
from io import BytesIO
from datetime import datetime
import json
import uuid
import openai 
from utils.ai_pipeline import get_openai_api_key
from flask_cors import CORS


# ─── SETUP ──────────────────────────────────────────────────────────────────────

load_dotenv()
app = Flask(__name__)
CORS(app)


app.secret_key = 'SuperSecretKey'

THREAD_ID = 'thread_LGQV4Dbxch9nmCLS44Rlswon'
ASSISTANT_ID = "asst_6gmouMfvq4cpc99N74qKV6qY"

try:
    if os.environ.get("FLASK_ENV") == "production":
        from utils.db_util import get_db_secret  # import only if needed
        secret = get_db_secret("prod/rds/db")
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{secret['username']}:{secret['password']}"
            f"@{secret['host']}:{secret['port']}/{secret['dbname']}"
        )
    else:
        raise RuntimeError("Development environment detected")
except Exception as e:
    print(f"🛯 Using SQLite fallback — reason: {e}")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alc_db.sqlite3'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

@app.route("/whoami")
def whoami():
    return boto3.client("sts").get_caller_identity()

# S3
S3_BUCKET_NAME = 'dataforge-uploader-bucket'
s3_client = boto3.client("s3")
# ─── MODELS ─────────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'user'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw, method='pbkdf2:sha256')
        app.logger.debug(f"[SET PASSWORD] Raw: '{pw}' → Hash: {self.password_hash}")

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)
    
class Contact(db.Model):
    __tablename__ = 'contact'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class File(db.Model):
    __tablename__ = 'file'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename   = db.Column(db.String(255), nullable=False)
    s3_key     = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_size  = db.Column(db.Integer)  # in bytes
    file_type  = db.Column(db.String(50))  # e.g., 'csv', 'xlsx'
    cleaned = db.Column(db.Boolean, default=False)
    cleaned_key = db.Column(db.String(512))

    user = db.relationship('User', backref='files')
    
# ─── DEBUG ROUTES ───────────────────────────────────────────────────────────────

# @app.route('/debug-users-full')
# def debug_users_full():
#     users = User.query.all()
#     html = "<h2>Registered Users (w/ hashes)</h2><ul>"
#     for u in users:
#         html += f"<li><b>{u.username}</b>: {u.password_hash}</li>"
#     html += "</ul>"
#     return html

# ─── HELPERS ─────────────────────────────────────────────────────────────────────

# checks to see if a user id is stored within the session
@app.before_request
def load_logged_in_user():
    user_id  = session.get('user_id')
    g.user   = User.query.get(user_id) if user_id else None

# only an authenticated route can use them
# A decorator in Python is essentially a function in Python
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.path))
        return view(**kwargs)
    return wrapped_view

# ─── AUTH ROUTES ────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        app.logger.debug(f"[REGISTER] Username: {username}, Password bytes: {list(password.encode())}")

        if not username or not password:
            flash('Username and password are required.')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken.')
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))

    return render_template('register.html', action='Register', next=request.args.get('next'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user     = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))   # ← now sends to dashboard
        else:
            flash('Invalid credentials.')

    return render_template('register.html', action='Log In', next=request.args.get('next'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── BASIC PAGES ────────────────────────────────────────────────────────────────

projects = [
    {
        'id': 1,
        'title': 'S3 File-Uploader',
        'description': (
            "A Flask-based file management system that enables user registration, "
            "secure S3 uploads, and CSV previewing. Hosted on EC2 with file metadata stored in RDS. "
            "Built using AWS S3, RDS (MySQL), EC2, and Boto3."
        ),
        'url': '/dashboard',
        'tags': [
            'Python', 'Flask', 'AWS S3', 'AWS RDS', 'AWS EC2',
            'Boto3', 'MySQL', 'CSV Preview', 'User Auth'
        ]
    },

    {
        'id': 2,
        'title': 'Task Master Plus',
        'description': (
            "A minimalist to-do list app with user authentication, task creation, editing, and filtering. "
            "Built with Flask, Tailwind, and SQLite, featuring clean MVC architecture and session-based login."
        ),
        'url': 'https://lannoncan.pythonanywhere.com',
        'tags': [
            'Python', 'Flask', 'SQLite', 'Tailwind CSS', 'MVC',
            'To-Do App', 'Authentication', 'CRUD'
        ]
    },

    {
        'id': 3,
        'title': 'Data Forge Lite',
        'description': (
            "Data-Forge-Lite is a lightweight, AI-powered Streamlit app designed to help you clean, engineer, "
            "and explore your datasets with interactive mind maps and visual storytelling — all without needing to "
            "touch a single line of code."
        ),
        'url': 'https://data-forge-lite.streamlit.app',
        'tags': [
            'Python', 'Streamlit', 'OpenAI', 'LangChain',
            'Interactive EDA', 'Custom AI Agents', 'Data Visualization',
            'Plotly'
        ]
    }
]

@app.route('/')
def home():
    return render_template('index.html', projects=projects)

@app.route('/projects')
def show_projects():
    return render_template('projects.html', projects=projects)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name    = request.form['name'].strip()
        email   = request.form['email'].strip()
        subject = request.form.get('subject', '').strip()
        message = request.form['message'].strip()

        if not name or not email or not message:
            flash('Name, email, and message are required.', 'warning')
        else:
            new_msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(new_msg)
            db.session.commit()
            flash('Thanks for your message!', 'success')
            return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/data-forge-lite')
@login_required
def data_forge_lite():
    # return redirect("https://data-forge-lite.streamlit.app")
    return redirect(url_for('dashboard'))

# ─── S3 DASHBOARD ROUTES ────────────────────────────────────────────────────────

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        f = request.files.get('file')

        if f:
            key = f'uploads/{g.user.id}/{f.filename}'
            try:
                # Upload to S3
                s3_client.upload_fileobj(f, S3_BUCKET_NAME, key)

                # # Rewind file to read its size (fixes "I/O on closed file")
                # f.seek(0, os.SEEK_END)
                # size = f.tell()
                # f.seek(0)

                # Save metadata in DB
                new_file = File(
                    user_id=g.user.id,
                    filename=f.filename,
                    s3_key=key,
                    # file_size=size,
                    file_type=f.filename.split('.')[-1].lower()
                )
                db.session.add(new_file)
                db.session.commit()

                flash(f"Uploaded '{f.filename}'!", 'success')
                return redirect(url_for('dashboard'))

            except Exception as e:
                flash(f"File not saved to db: {e}", 'danger')

        else:
            flash("No file selected.", 'warning')
        return redirect(url_for('dashboard'))

    # Load files for this user from the database
    files = File.query.filter_by(user_id=g.user.id).all()
    return render_template('dashboard.html', files=files, username=g.user.username)


@app.route('/files')
@login_required
def list_files():
    files = File.query.filter_by(user_id=g.user.id).all()
    return render_template('files.html', files=files)

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

        return render_template('preview.html',
                               filename=file.filename,
                               preview=preview_html,
                               describe=describe_html)

    except Exception as e:
        flash(f"Preview error: {e}", 'danger')
        return redirect(url_for('dashboard'))

@app.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)

    # Security check: make sure the file belongs to the current user
    if file.user_id != g.user.id:
        flash("Unauthorized attempt to delete file.", 'danger')
        return redirect(url_for('dashboard'))

    try:
        # Delete from S3
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file.s3_key)

        # Delete from DB
        db.session.delete(file)
        db.session.commit()

        flash(f"Deleted '{file.filename}'!", 'success')

    except Exception as e:
        flash(f"Delete error: {e}", 'danger')

    return redirect(url_for('dashboard'))

# ─── LAMBDA Functions ────────────────────────────────────────────────────────────────
@app.route('/clean/<int:file_id>')
@login_required
def clean_file(file_id):
    file = File.query.get_or_404(file_id)

    if file.user_id != g.user.id:
        flash("Unauthorized file access.", "danger")
        return redirect(url_for('dashboard'))

    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        payload = {
            "s3_bucket": S3_BUCKET_NAME,
            "s3_key": file.s3_key,
            "user_id": g.user.id,
            "request_id": str(uuid.uuid4()),
        }

        response = lambda_client.invoke(
            FunctionName='dataforge_etl_handler',
            InvocationType='Event',  # Async so it doesn't block user
            Payload=json.dumps(payload)
        )

        if response['StatusCode'] == 202:
            flash(f"Started cleaning: {file.filename}. Please check back in a moment.", "success")
        else:
            flash("Failed to invoke Lambda function.", "danger")

    except Exception as e:
        app.logger.error(f"[Lambda Invoke Error] {e}")
        flash(f"Error triggering Lambda: {e}", "danger")

    return redirect(url_for('dashboard'))


@app.route("/ask", methods=["POST"])
def ask_openai():
    openai.api_key = get_openai_api_key()

    data = request.get_json()
    print("DEBUG Incoming JSON:", data)

    user_input = data.get("query") if data else None

    if not user_input or not user_input.strip():
        return jsonify({"error": "No query provided"}), 400

    try:
        print(f"🔥 Using THREAD_ID: {THREAD_ID}")
        print(f"🔥 Using ASSISTANT_ID: {ASSISTANT_ID}")

        # Add user input to the thread
        message = openai.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=user_input
        )
        print(f"🔥 Created message: {message.id}")

        # 🔥 DEBUG: Check thread history BEFORE running
        before_messages = openai.beta.threads.messages.list(
            thread_id=THREAD_ID,
            limit=5  # Show last 5 messages
        )
        print(f"🔥 Thread history before run ({len(before_messages.data)} messages):")
        for msg in before_messages.data:
            content = msg.content[0].text.value[:100] + "..." if len(msg.content[0].text.value) > 100 else msg.content[0].text.value
            print(f"   {msg.role}: {content}")

        # Run assistant
        run = openai.beta.threads.runs.create(
            thread_id=THREAD_ID,
            assistant_id=ASSISTANT_ID
        )
        print(f"🔥 Created run: {run.id}")

        # Poll for run completion
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=THREAD_ID,
                run_id=run.id
            )
            print(f"🔥 Run status: {run_status.status}")
            
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                print(f"🔥 Run failed with status: {run_status.status}")
                if hasattr(run_status, 'last_error'):
                    print(f"🔥 Error details: {run_status.last_error}")
                return jsonify({"error": f"Run failed: {run_status.status}"}), 500
            time.sleep(0.5)

        # Get messages after run
        messages = openai.beta.threads.messages.list(
            thread_id=THREAD_ID,
            order="desc"
        )
        
        print(f"🔥 Total messages after run: {len(messages.data)}")
        
        # Get the most recent assistant message
        for message in messages.data:
            if message.role == "assistant":
                last_msg = message.content[0].text.value
                print(f"🔥 Assistant response: {last_msg[:200]}...")
                return jsonify({"response": last_msg})

        return jsonify({"error": "No assistant response found."}), 500

    except Exception as e:
        print(f"🔥 Error in ask_openai: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
# ─── ENTRYPOINT ────────────────────────────────────────────────────────────────

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
