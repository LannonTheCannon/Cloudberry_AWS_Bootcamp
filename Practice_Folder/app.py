from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    projects = [
        {'title': 'Data Forge Lite', 'description': 'Description of Data Forge Lite!', 'url': 'https://data-forge-lite.streamlit.app'},
        {'title': 'Data Forge Lite', 'description': 'Description of Data Forge Lite!', 'url': 'https://data-forge-lite.streamlit.app'},
        {'title': 'Data Forge Lite', 'description': 'Description of Data Forge Lite!', 'url': 'https://data-forge-lite.streamlit.app'},
    ]
    current_year = datetime.now().year
    return render_template('index.html', projects=projects, year=current_year)

if __name__ == '__main__':
    app.run(debug=True)


