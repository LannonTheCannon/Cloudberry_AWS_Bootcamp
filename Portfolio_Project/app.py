from flask import Flask, render_template, request, redirect
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
import os

app = Flask(__name__)

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


@app.route('/')
def home():
    # Hey Ninja, I want you to have access to a variable named projects and its
    # value is whatever my Python variable proejcts contains!
    return render_template('index.html', projects=projects)

@app.route('/projects')
def show_projects():
    return render_template('projects.html', projects=projects)

if __name__ == '__main__':
    app.run(port=5010, debug=True)