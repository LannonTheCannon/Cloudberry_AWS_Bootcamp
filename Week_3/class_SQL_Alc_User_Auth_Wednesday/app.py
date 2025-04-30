from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import session, flash, g
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
# Add a secret key!
app.secret_key = "My-Super-Secret-Key"

# Configure where the db and where it will be located
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alc_db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initializing the ORM
db = SQLAlchemy(app)

# Define the Task table model
class Task(db.Model):
    __tablename__ = 'task'
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title         = db.Column(db.String(100), nullable=False)
    due_date      = db.Column(db.Date, nullable=True)
    completed     = db.Column(db.Boolean, default=False, nullable=False)
    password_hash = db.Column(db.String(128))

    # Create Password
    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


# Home Run
@app.route('/')
def home():
    # Read the filter from query string (default = 'all')
    status = request.args.get('filter', 'all')

    # Choose the query based on status
    if status == 'pending':
        tasks = Task.query.filter_by(completed=False).order_by(Task.id).all()
    elif status == 'completed':
        tasks = Task.query.filter_by(completed=True).order_by(Task.id).all()
    else:
        tasks = Task.query.order_by(Task.id).all()

    return render_template('todo.html', tasks=tasks, active_filter=status)  # Passes this list into your todo.html
    # The template loops over tasks and displays
    # title, due date, and completion state

# The function to add new items to the database
@app.route('/add', methods=['POST'])
def add_task():
    title        = request.form.get('task')  # Reads the form task and due_date from the POST body
    due_date_str = request.form.get('due_date')
    due_date     = None  # Coverts the data string into a date object or leaves it at none
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

    new_task = Task(title=title, due_date=due_date)  # Instantiates Task(), adds it to the session,
    # then commits (writing to SQLITE)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('home'))

# A function or contract that completes items on the
@app.route('/complete/<int:task_id>')  # Fetches that row by its primary key
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit() # commits, then redirects to refresh the list
    return redirect(url_for('home'))

@app.route('/delete/<int:task_id>')  # Retrieves the row, deletes it from the session, commits, then return you to home
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/clear_all')
def clear_all():
    Task.query.delete()  # Inserts a bulk DELETE FROM task, wiping the table clean
    db.session.commit()
    return redirect(url_for('home'))

# Create the table on startup
if __name__ == '__main__':
    with app.app_context(): # This lets the app know which app its bound to
        db.create_all() # issues a CREATE TABLE for every model
    app.run(debug=True) # starts the built-in server on porto 5000 with a hot ass reload
