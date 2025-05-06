# CREATE-READ-UPDATE-DELETE for Data Files

from flask import Flask, request, render_template, render_template_string, redirect, url_for, flash
import boto3
import os
from dotenv import load_dotenv
import pandas as pd
from io import BytesIO

# Load environmental variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET_NAME = 'dataforge-uploader-bucket'

# Initialize Boto3 client
s3_client = boto3.client('s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# # Simple HTML form for uploading
# UPLOAD_FORM = """
# <!doctype html>
# <title>Upload file to S3</title>
# <h1>Upload new File</h1>
# <form method=post enctype=multipart/form-data>
#   <input type=file name=file>
#   <input type=submit value=Upload>
# </form>
# {% with messages = get_flashed_messages() %}
#   {% if messages %}
#     <ul>
#     {% for message in messages %}
#       <li>{{ message }}</li>
#     {% endfor %}
#     </ul>
#   {% endif %}
# {% endwith %}
# """


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file:
            filename = uploaded_file.filename
            try:
                s3_client.upload_fileobj(
                    uploaded_file,
                    S3_BUCKET_NAME,
                    f'uploads/{filename}'
                )
                flash(f"File '{filename}' uploaded successfully to S3!", 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f"Error uploading file: {str(e)}", 'danger')
                return redirect(url_for('dashboard'))
        else:
            flash("No file selected.", 'warning')
            return redirect(url_for('dashboard'))

    # List files here too!
    files = []
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='uploads/')
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                if not key.endswith('/'):
                    files.append(key.split('uploads/')[1])
    except Exception as e:
        flash(f"Error listing files: {str(e)}", 'danger')

    return render_template('dashboard.html', files=files)

@app.route('/files')
def list_files():
    try:
        # List objects inside 'uploads/' prefix
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='uploads/')
        files = []

        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                if not key.endswith('/'):  # Ignore the folder itself
                    files.append(key.split('uploads/')[1])  # Remove 'uploads/' prefix

        return render_template('files.html', files=files)

    except Exception as e:
        flash(f"Error listing files: {str(e)}", 'danger')
        return redirect(url_for('upload_file'))

@app.route('/preview/<filename>')
def preview_file(filename):
    try:
        # Download file from S3 into memory
        obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=f'uploads/{filename}')
        df = pd.read_csv(BytesIO(obj['Body'].read()))

        # Get preview and stats
        preview_html = df.head().to_html(classes='data')
        describe_html = df.describe().to_html(classes='data')

        return render_template('preview.html', filename=filename, preview=preview_html, describe=describe_html)

    except Exception as e:
        flash(f"Error previewing file: {str(e)}", 'danger')
        return redirect(url_for('list_files'))

@app.route('/delete/<filename>')
def delete_file(filename):
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=f'uploads/{filename}')
        flash(f"File '{filename}' deleted successfully!", 'success')
    except Exception as e:
        flash(f"Error deleting file: {str(e)}", 'danger')
    return redirect(url_for('dashboard'))



if __name__ == '__main__':
    app.run(debug=True)
