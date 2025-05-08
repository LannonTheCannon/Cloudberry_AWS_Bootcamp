from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

#
# ─── APP & DB SETUP ─────────────────────────────────────────────────────────────
#

app = Flask(__name__)
app.secret_key = 'SuperSecretKey'

# SQLite database for auth
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio_auth.sqlite3'

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://admin:Ismloao1117@'
    'mydbinstance.carwyykiawaw.us-east-1.rds.amazonaws.com:3306/mydb'
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#
# ─── MODELS ─────────────────────────────────────────────────────────────────────
#

class User(db.Model):
    __tablename__ = 'user'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

#
# ─── AUTH HELPERS ───────────────────────────────────────────────────────────────
#

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user  = User.query.get(user_id) if user_id else None

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.path))
        return view(**kwargs)
    return wrapped_view

#
# ─── AUTH ROUTES ────────────────────────────────────────────────────────────────
#

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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
            return redirect(url_for('login', next=request.args.get('next')))
    return render_template('auth.html', action='Register', next=request.args.get('next'))

@app.route('/login', methods=['GET','POST'])
def login():
    next_page = request.args.get('next') or request.form.get('next')
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        print(f"[DEBUG] Attempt login for username: '{username}' with password: '{password}'")

        user = User.query.filter_by(username=username).first()

        if user:
            print(f"[DEBUG] Found user in DB: {user.username}")
            print(f"[DEBUG] Stored hash: {user.password_hash}")
            print(f"[DEBUG] Password match? {user.check_password(password)}")
        else:
            print(f"[DEBUG] No user found with username '{username}'")

        if user is None or not user.check_password(password):
            flash('Invalid credentials.')
        else:
            session.clear()
            session['user_id'] = user.id
            return redirect(next_page or url_for('home'))

    return render_template('auth.html', action='Log In', next=next_page)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#
# ─── PORTFOLIO DATA & ROUTES ──────────────────────────────────────────────────
#

projects = [
    {
        'id': 1,
        'title': 'Data Forge Lite',
        'description': 'An AI-powered Streamlit app that lets users explore and clean datasets with mind maps, natural language queries, and dynamic visual storytelling — all without writing code.',
        'url': '/data-forge-lite',
        'tags': ['python', 'AI', 'streamlit', 'data science']
    },
    {
        'id': 2,
        'title': 'Task Master Plus',
        'description': 'A Flask & Tailwind CSS–powered task manager that lets users add, edit, update, and delete tasks—all persisted to an SQLite database.',
        'url': 'https://lannoncan.pythonanywhere.com',
        'tags': ['python', 'flask', 'sqlite', 'tailwindcss', 'html']
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
        name    = request.form.get('name')
        email   = request.form.get('email')
        message = request.form.get('message')
        flash('Thanks for your message!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

#
# ─── PROTECTED STREAMLIT GATE ─────────────────────────────────────────────────
#

@app.route('/data-forge-lite')
@login_required
def data_forge_lite():
    # After login, immediately redirect to the Streamlit app
    return redirect("https://data-forge-lite.streamlit.app")

#
# ─── APP ENTRYPOINT ────────────────────────────────────────────────────────────
#

if __name__ == '__main__':
    # create auth tables if they don’t exist
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='test').first():
            u = User(username='test')
            u.set_password('test123')
            db.session.add(u)
            db.session.commit()

    app.run(host='0.0.0.0', port=5000, debug=True)
