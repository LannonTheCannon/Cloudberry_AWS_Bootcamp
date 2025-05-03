from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from flask import jsonify

app = Flask(__name__)
app.secret_key = "SuperSecretKey"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alc_db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)

# Authentication helpers
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = User.query.get(user_id) if user_id else None

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# Auth routes
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
            return redirect(url_for('login'))

    return render_template('auth.html', action='Register')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid credentials.')
        else:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('home'))
    return render_template('auth.html', action='Log In')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# To-do routes
@app.route('/')
@login_required
def home():
    status = request.args.get('filter', 'all')
    if status == 'pending':
        tasks = Task.query.filter_by(completed=False).order_by(Task.id).all()
    elif status == 'completed':
        tasks = Task.query.filter_by(completed=True).order_by(Task.id).all()
    else:
        tasks = Task.query.order_by(Task.id).all()
    return render_template('todo.html', tasks=tasks, active_filter=status)



@app.route('/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('task')
    due_date_str = request.form.get('due_date')
    due_date = None
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    new_task = Task(title=title, due_date=due_date)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('home'))

# ######### ACTIONS ############

@app.route('/complete/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/api/tasks/<int:task_id>', methods=['POST'])
@login_required
def api_update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or {}

    task.title = data.get('title', task.title)
    due = data.get('due_date', '')
    task.due_date = (
        datetime.strptime(due, '%Y-%m-%d').date()
        if due else None
    )

    db.session.commit()
    return jsonify({
        "id": task.id,
        "title": task.title,
        "due_date": task.due_date.isoformat() if task.due_date else ""
    })

@app.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/clear_all')
@login_required
def clear_all():
    Task.query.delete()
    db.session.commit()
    return redirect(url_for('home'))

# App entry point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
