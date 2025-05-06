from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'replace-with-secure-key'

# Data stub
projects = [
    { 'id': 1, 'title': 'Project One', 'description': 'An AI chatbot demo.', 'url': 'https://data-forge-lite.streamlit.app', 'tags': ['python','ai'] },
    { 'id': 2, 'title': 'Project Two', 'description': 'Interactive data viz.', 'url': '#', 'tags': ['javascript','visualization'] },
]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/projects')
def show_projects():
    return render_template('projects.html', projects=projects)

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Here you'd send email or store message
        flash('Thanks for your message!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)