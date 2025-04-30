from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure where the db will be located
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alc_db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    __tablename__ = 'task'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title      = db.Column(db.String(100), nullable=False)
    due_date   = db.Column(db.Date, nullable=True)
    completed  = db.Column(db.Boolean, default=False, nullable=False)

@app.route('/')
def home():
    tasks = Task.query.order_by(Task.id).all()
    return render_template('todo.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    title        = request.form.get('task')
    due_date_str = request.form.get('due_date')
    due_date     = None
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    new_task = Task(title=title, due_date=due_date)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/clear_all')
def clear_all():
    Task.query.delete()
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
