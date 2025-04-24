from flask import Flask, render_template, request

app = Flask(__name__)

# This decorator is what links the route to the function
@app.route('/')
def home():
    return render_template('form.html')

@app.route('/form2')
def form2():
    return render_template("form2.html", )

# this is essentially a rest API
@app.route('/user/<name>')
def user(name):
    # return f"Hello {name}!"
    return render_template('user.html', username=name)

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

@app.route('/greet', methods=['GET', "POST"])
def greet():
    if request.method == "POST":
        name = request.form['name']
        return render_template('user.html', username = name)
    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)



