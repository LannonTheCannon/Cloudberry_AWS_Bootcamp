from flask import Flask, render_template, request, redirect, url_for, flash, session, g

app = Flask(__name__)
app.secret_key = 'SuperSecretKey'

# Data stub
projects = [
    {
        'id': 1,
        'title': 'Data Forge Lite',
        'description': 'An AI-powered Streamlit app that lets users explore and clean datasets with mind maps, natural language queries, and dynamic visual storytelling — all without writing code.',
        'url': 'https://data-forge-lite.streamlit.app',
        'tags': ['python', 'AI', 'streamlit', 'data science']
    },

    {
        'id': 2,
        'title': 'Data Forge Plus',
        'description': 'An AI-powered Streamlit app that lets users explore and clean datasets with mind maps, natural language queries, and dynamic visual storytelling — all without writing code.',
        'url': 'https://data-forge-lite.streamlit.app',
        'tags': ['python', 'AI', 'streamlit', 'data science']
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
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Here you'd send email or store message
        flash('Thanks for your message!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)