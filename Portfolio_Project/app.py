from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = '…some secret for flashes…'

# ---- Routes ----
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/projects')
def projects():
    # you might load a JSON/YAML of projects here
    return render_template('projects.html')

@app.route('/blog')
def blog():
    # you could pull blog posts from markdown files or a simple DB
    return render_template('blog.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        # process form: e.g. send email or write to a Google Sheet
        flash('Thanks for reaching out—message sent!')
        return redirect(url_for('contact'))
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
