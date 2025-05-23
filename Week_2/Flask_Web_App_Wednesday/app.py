from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/greet', methods=['GET', "POST"])
def greet():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        return render_template('feedback.html', username=name, message=message, email=email)

    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)



