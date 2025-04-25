# Create Read Update Delete
# TO DO LIST

from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# store the tasks here
tasks = []

# Home route if its
@app.route('/')
def home():
    return render_template('index.html', tasks=tasks)

# the contract between front end and backend
@app.route('/add', methods=['POST'])
def add_task():
    task = request.form.get('task')
    if task:
        tasks.append(task)
    return redirect('/')

# id are numbers not strings
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 0 < task_id < len(tasks):
        tasks.pop(task_id)
    return redirect('/')

# This is called namespace 
if __name__ == '__main__':
    app.run(debug=True)


