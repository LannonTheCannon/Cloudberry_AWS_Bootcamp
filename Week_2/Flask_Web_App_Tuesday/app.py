from flask import Flask, render_template, request

app = Flask(__name__)

# This decorator is what links the route to the function
@app.route('/')
def home():
    return render_template('form.html')

# this is essentially a rest API
@app.route('/user/<name>')
def user(name):
    return f"Hello {name}!"

@app.route('/about')
def about():
    return render_template('/about.html', name='Lannon', passion='data apps')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    return f"""
    <h2>Thanks, {name}!</h2>
    <p>We've received your message:</p>
    <blockquote>{message}</blockquote>
    <p>We'll reach out to you at <strong>{email}</strong>.</p>
    """

if __name__ == '__main__':
    app.run(debug=True)



