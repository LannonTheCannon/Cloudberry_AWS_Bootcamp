from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging

# ─── SETUP ──────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = 'SuperSecretKey'

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:Ismloao1117@mydbinstance.carwyykiawaw.us-east-1.rds.amazonaws.com:3306/mydb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alc_db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)  # <- this line guarantees it logs


# ─── MODELS ─────────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        # This fucking guy right here
        self.password_hash = generate_password_hash(pw, method='pbkdf2:sha256')
        app.logger.debug(f"[SET PASSWORD] Raw: '{pw}' → Hash: {self.password_hash}")

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

@app.route('/debug-users-full')
def debug_users_full():
    users = User.query.all()
    html = "<h2>Registered Users (w/ hashes)</h2><ul>"
    for u in users:
        html += f"<li><b>{u.username}</b>: {u.password_hash}</li>"
    html += "</ul>"
    return html

@app.route('/check-hash')
def check_hash():
    from werkzeug.security import check_password_hash
    h = request.args.get('hash')
    pw = request.args.get('pw')
    if not h or not pw:
        return "Usage: /check-hash?hash=...&pw=..."
    match = check_password_hash(h, pw)
    return f"<p>Password match? <b>{match}</b></p>"


# ─── HELPERS ─────────────────────────────────────────────────────────────────────

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = User.query.get(user_id) if user_id else None

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

        # Log exact byte-level details for certainty
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
            db.session.expire_all()  # ← THIS LINE IS THE KEY
            flash('Registration successful. Please log in.')
            return redirect(url_for('login', next=request.args.get('next')))
    return render_template('auth.html', action='Register', next=request.args.get('next'))


@app.route('/login', methods=['GET','POST'])
def login():
    next_page = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        app.logger.debug(f"[LOGIN] Username: {username}, Password: {password}")

        user = User.query.filter_by(username=username).first()

        if user:
            app.logger.debug(f"[LOGIN] Found user: {user.username}")
            app.logger.debug(f"[LOGIN] Password match: {user.check_password(password)}")
        else:
            app.logger.debug(f"[LOGIN] User '{username}' not found")

        if user is None or not user.check_password(password):
            flash('Invalid credentials.')
        else:
            session.clear()
            session['user_id'] = user.id

            if not next_page or next_page == 'None':
                next_page = url_for('home')

            return redirect(next_page)

    return render_template('auth.html', action='Log In', next=next_page)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── BASIC PAGES ────────────────────────────────────────────────────────────────

projects = [
    {
        'id': 1,
        'title': 'Data Forge Lite',
        'description': 'AI-powered Streamlit EDA tool',
        'url': '/data-forge-lite',
        'tags': ['python', 'AI', 'streamlit']
    },
    {
        'id': 2,
        'title': 'Task Master Plus',
        'description': 'Task manager built with Flask',
        'url': 'https://lannoncan.pythonanywhere.com',
        'tags': ['flask', 'sqlite', 'tailwind']
    },
]

@app.route('/')
def home():
    return render_template('home.html', projects=projects)

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
    return redirect("https://data-forge-lite.streamlit.app")

# ─── ENTRYPOINT ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)

