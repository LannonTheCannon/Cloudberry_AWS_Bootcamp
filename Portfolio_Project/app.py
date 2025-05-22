from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
import os
from flask_sqlalchemy import SQLAlchemy
import logging
import os
from datetime import datetime
import pandas as pd
import uuid
from utils.flask_secrets import get_flask_secret
from utils.s3_secrets import get_s3_config

# ─── SETUP ──────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = get_flask_secret()['secret_key']

try:
    if os.environ.get("FLASK_ENV") == "production":
        from utils.db_secrets import get_db_secret  # import only if needed
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


S3_BUCKET_NAME = get_s3_config()["bucket_name"]
s3_client = boto3.client("s3", region_name="us-west-1")

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
        confirm = request.form['confirm_password']

        if password != confirm:
            flash('Passwords do not match.')
            return render_template('register.html', action='Sign Up')

        # app.logger.debug(f"[REGISTER] Username: {username}, Password bytes: {list(password.encode())}")

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
            # return redirect(url_for('login'))
            return render_template('login.html', action='Sign In')

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
            return redirect(url_for('dashboard'))   # ← now sends to home
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

# Top of your app.py
posts = {
    "graphic-design-skills": {
        "title": "12 Graphic Design Skills You Need To Get Hired",
        "content": "Here’s what you should know...",
        "author": "Michael Andreuzza",
        "preview": "A wonderful serenity has taken possession...",
        "slug": "graphic-design-skills"
    },
    "ai-blog-future": {
        "title": "The Future of AI-Driven Development",
        "content": "LLMs are changing everything, from prototyping to production.",
        "author": "Lannon Khau",
        "preview": "What if AI could write your entire backend?",
        "slug": "ai-blog-future"
    }
}

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

## -------------------------------------------------------------------------------------

# ─── LAMBDA Functions ────────────────────────────────────────────────────────────────
# --- Lambda Functions (Deprecated/Removed)
# Lambda based file cleaning functionality no longer relevant to Data Forge


@app.route('/')
def home():
    # Hey Ninja, I want you to have access to a variable named projects and its
    # value is whatever my Python variable proejcts contains!
    return render_template('index.html', projects=projects)

@app.route('/projects')
def show_projects():
    return render_template('projects.html', projects=projects)

@app.route('/blog')
def show_blog():
    return render_template('blog.html', posts=posts)

@app.route('/blog/<slug>')
def blog_post(slug):
    # Example data — usually from DB
    posts = {
        "graphic-design-skills": {
            "title": "12 Graphic Design Skills You Need To Get Hired",
            "content": "Here’s what you should know...",
            "author": "Michael Andreuzza",
        }
    }
    try:
        return render_template(f"posts/{slug}.html")
    except TemplateNotFound:
        abort(404)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)