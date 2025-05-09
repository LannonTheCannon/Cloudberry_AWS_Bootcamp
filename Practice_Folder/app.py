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

# ─── SETUP ──────────────────────────────────────────────────────────────────────

load_dotenv()
app = Flask(__name__)
app.secret_key = 'SuperSecretKey'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alc_db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# ─── S3 CLIENT ─────────────────────────────────────────────────────────────────

AWS_ACCESS_KEY_ID     = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION            = os.getenv('AWS_REGION')
S3_BUCKET_NAME        = 'dataforge-uploader-bucket'

s3_client = boto3.client(
    's3',
    aws_access_key_id     = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name           = AWS_REGION
)

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

# ─── DEBUG ROUTES ───────────────────────────────────────────────────────────────

@app.route('/debug-users-full')
def debug_users_full():
    users = User.query.all()
    html = "<h2>Registered Users (w/ hashes)</h2><ul>"
    for u in users:
        html += f"<li><b>{u.username}</b>: {u.password_hash}</li>"
    html += "</ul>"
    return html

# ─── HELPERS ─────────────────────────────────────────────────────────────────────

@app.before_request
def load_logged_in_user():
    user_id  = session.get('user_id')
    g.user   = User.query.get(user_id) if user_id else None

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

    return render_template('auth.html', action='Register', next=request.args.get('next'))

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

    return render_template('auth.html', action='Log In', next=request.args.get('next'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── BASIC PAGES ────────────────────────────────────────────────────────────────

projects = [
    {'id':1,'title':'Data Forge Lite','description':'AI-powered Streamlit EDA tool','url':'/data-forge-lite','tags':['python','AI','streamlit']},
    {'id':2,'title':'Task Master Plus','description':'Task manager built with Flask','url':'https://lannoncan.pythonanywhere.com','tags':['flask','sqlite','tailwind']},
    {'id':3,'title':'Data Forge Plus','description':'Your next big project','url':'https://data-forge-lite.streamlit.app','tags':['flask','API']},
]

@app.route('/')
def home():
    return render_template('index.html', projects=projects)

@app.route('/projects')
def show_projects():
    return render_template('projects.html', projects=projects)

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        flash('Thanks for your message!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/data-forge-lite')
@login_required
def data_forge_lite():
    # return redirect("https://data-forge-lite.streamlit.app")
    return redirect(url_for('dashboard'))

# ─── S3 DASHBOARD ROUTES ────────────────────────────────────────────────────────

@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        f = request.files.get('file')
        if f:
            try:
                s3_client.upload_fileobj(f, S3_BUCKET_NAME, f'uploads/{f.filename}')
                flash(f"Uploaded '{f.filename}' to S3!", 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f"Upload error: {e}", 'danger')
                return redirect(url_for('dashboard'))
        flash("No file selected.", 'warning')
        return redirect(url_for('dashboard'))

    # list existing
    files = []
    resp  = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='uploads/')
    for obj in resp.get('Contents', []):
        key = obj['Key']
        if not key.endswith('/'):
            files.append(key.split('uploads/')[1])
    return render_template('dashboard.html', files=files)

@app.route('/files')
@login_required
def list_files():
    files = []
    resp  = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='uploads/')
    for obj in resp.get('Contents', []):
        key = obj['Key']
        if not key.endswith('/'):
            files.append(key.split('uploads/')[1])
    return render_template('files.html', files=files)

@app.route('/preview/<filename>')
@login_required
def preview_file(filename):
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=f'uploads/{filename}')
        df  = pd.read_csv(BytesIO(obj['Body'].read()))
        preview_html  = df.head().to_html(classes='data')
        describe_html = df.describe().to_html(classes='data')
        return render_template('preview.html',
                               filename=filename,
                               preview=preview_html,
                               describe=describe_html)
    except Exception as e:
        flash(f"Preview error: {e}", 'danger')
        return redirect(url_for('dashboard'))

@app.route('/delete/<filename>')
@login_required
def delete_file(filename):
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=f'uploads/{filename}')
        flash(f"Deleted '{filename}'!", 'success')
    except Exception as e:
        flash(f"Delete error: {e}", 'danger')
    return redirect(url_for('dashboard'))

# ─── ENTRYPOINT ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
