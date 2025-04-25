# Create Read Update Delete
# TO DO LIST
# Mark Tasks as Completed (done)
# Add a Clear All Tasks button (done)
# Add due dates and display them
# Deploy the App sing PythonAnywhere or Heroku

from flask import Flask, render_template, request, redirect
from datetime import datetime

app = Flask(__name__)

# store the tasks here
tasks = []

# Home route if its
@app.route('/')
def home():
    return render_template('todo.html', tasks=tasks)

# the contract between front end and backend
@app.route('/add', methods=['POST'])
def add_task():
    task = request.form.get('task')
    due_date = request.form.get('due_date')
    due = datetime.strptime(due_date, "%Y-%m-%d").date()
    if task and due_date:
        # tasks.append(task)
        tasks.append({
            "text": task,
            "completed": False,
            'due_date': due # now this is a better looking date
        })
    return redirect('/')

# id are numbers not strings
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)
    return redirect('/')

# complete task contract
@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    # mark the task as done
    if 0 <= task_id < len(tasks):
        tasks[task_id]['completed'] = True
    return redirect('/')

@app.route('/clear_all')
def clear_all_tasks():
    # remove every task
    tasks.clear()
    return redirect('/')

# This is called namespace
if __name__ == '__main__':
    app.run(debug=True)


