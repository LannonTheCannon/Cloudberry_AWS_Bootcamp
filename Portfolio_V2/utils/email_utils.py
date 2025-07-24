import boto3
import json
import smtplib
from email.message import EmailMessage

def get_smtp_credentials(secret_name="prod/email/smtp", region_name="us-west-1"):
    """
    Loads SMTP email credentials from AWS Secrets Manager.
    Returns a dict with smtp_host, smtp_port, username, password, from_email, etc.
    """
    client = boto3.client("secretsmanager", region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)›
        
        secret_dict = json.loads(response["SecretString"])
        return secret_dict
    except Exception as e:
        print(f"❌ Error loading SMTP credentials: {e}")
        return None

def send_contact_notification(name, email, message):
    """
    Sends an email notification to yourself when a user submits the contact form.
    """
    creds = get_smtp_credentials()
    if not creds:
        print("❌ SMTP credentials missing or could not be loaded!")
        return False

    msg = EmailMessage()
    msg["Subject"] = "🚨 New Contact Form Submission"
    msg["From"] = creds["from_email"]
    msg["To"] = creds["from_email"]  # send to yourself, or add other recipients here
    msg.set_content(f"Name: {name}\nEmail: {email}\nMessage:\n{message}")

    try:
        with smtplib.SMTP(creds["smtp_host"], int(creds["smtp_port"])) as server:
            server.starttls()
            server.login(creds["username"], creds["password"])
            server.send_message(msg)
        print("✅ Contact email sent successfully.")
        return True
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False
