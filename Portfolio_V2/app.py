from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)
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
from utils.ai_pipeline import run_cleaning_pipeline
# from utils.s3_secrets import get_s3_config

# ─── SETUP ──────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = 'MySecretKey'

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
    return render_template('index.html')

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

# ─── About Me Section  ──────────────────────────────────────────────────────────────────────

@app.route('/about')
def about():
    return render_template('about.html')

# ─── Projects Section  ──────────────────────────────────────────────────────────────────────

projects = {
    "data-forge-plus": {
        "title": "Data Forge Plus",
        "description": "A Flask + Streamlit-powered AI engine for automated dataset cleaning and visual EDA. ",
        "tech": ["Flask", "Streamlit", "AWS Lambda", "S3", "RDS", "OpenAI"],
        "author": "Lannon Khau",
        "template": "data-forge-plus.html"
    },
    "task-master-plus": {
        "title": "Task Master Plus",
        "description": "A minimalist productivity app designed to help users create, track, and complete goals using habit reinforcement and lightweight analytics.",
        "tech": ["Flask", "Tailwind", "SQLite", "Chart.js"],
        "author": "Lannon Khau",
        "template": "task-master-plus.html"
    },
    "data-forge-lite": {
        "title": "Data Forge Lite",
        "description": "A public-facing demo of the Data Forge engine, running streamlined EDA visualizations for smaller datasets with zero-code interaction.",
        "tech": ["Streamlit", "Pandas AI", "Plotly"],
        "author": "Lannon Khau",
        "template": "data-forge-lite.html"
    },
    "Quotability": {
        "title": "Quoutability",
        "description": "An AI powered quote app that also lets users have conversations with AI about what they've read.",
        "tech": ["Streamlit", "Pandas AI", "Plotly"],
        "author": "Lannon Khau",
        "template": "data-forge-lite.html"
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
                author=project["author"]
            )
        except TemplateNotFound:
            abort(404)
    else:
        abort(404)



# ─── Blog Section  ──────────────────────────────────────────────────────────────────────

posts = {
    "graphic-design-skills": {
        "title": "12 Graphic Design Skills You Need To Get Hired",
        "content": "Here’s what you should know...",  # Optional fallback
        "author": "Michael Andreuzza",
        "template": "graphic-design-skills.html"  # points to templates/posts/
    },
    "my-first-hackathon": {
        "title": "🚀 My First Hackathon",
        "content": "What I learned building under pressure.",
        "author": "Lannon Khau",
        "template": "my-first-hackathon.html"
    }
}

@app.route('/blog')
def show_blog():
    return render_template('blog.html', posts=posts)
@app.route("/blog/<slug>")
def blog_post(slug):
    post = posts.get(slug)
    if post:
        try:
            return render_template(
                f"posts/{post['template']}",
                title=post["title"],
                author=post["author"],
                content=post["content"]
            )
        except TemplateNotFound:
            abort(404)
    else:
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
    g.user   = User.query.get(user_id) if user_id else None

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

@app.route('/clean/<int:file_id>', method=["POST"])
@login_required
def clean_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != g.user.id:
        flash('Unauthorized access to file.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # Load from S3
        s3_obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, key=file.s3_key)
        df = pd.read_csv(BytesIO(s3_obj['Body'].read()))

        # Run AI pipeline
        df_cleaned = run_cleaning_pipeline(df)

        # Upload cleaned file
        buffer = BytesIO
        df_cleaned.to_csv(buffer, index=False)
        buffer.seek(0)

        cleaned_key = f"cleaned/{g.user.id}/{file.filename}"
        s3_client.upload_fileobj(buffer, S3_BUCKET_NAME, cleaned_key)

        # Update db
        file.cleaned = True
        file.cleaned_key = cleaned_key
        db.session.commit()

        flash("Cleaning complete!", "success")

    except Exception as e:
        flash(f"Cleaning error: {e}", '')



@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    file = File.query.get_or_404(file_id)

    # Security Check: Make sure the file belongs to the current user
    if file.user_id != g.user.id:
        print("Unauthorized attempt to delete file.")
        return redirect(url_for('dashboard'))

    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file.s3_key)
        db.session.delete(file)
        db.session.commit()

        print(f"Deleted {file.filename}!", 'success')

    except Exception as e:
        print(f'Delete Error: {e}', 'danger')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("Running db.create_all()")
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
