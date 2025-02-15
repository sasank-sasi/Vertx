from flask import Flask, request, jsonify
import os
import json
import csv
from dotenv import load_dotenv
from datetime import datetime
import groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import asdict
from pipeline import Founder  # Importing data models from pipeline.py

# Load environment variables
load_dotenv()

app = Flask(__name__)

groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

# Endpoint to get environment variables
@app.route('/env', methods=['GET'])
def get_env():
    return jsonify({
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "SMTP_SERVER": os.getenv("SMTP_SERVER"),
    })

# Endpoint to create a Founder
@app.route('/founder', methods=['POST'])
def create_founder():
    data = request.json
    founder = Founder(**data)
    return jsonify(asdict(founder))

# Endpoint to send an email
@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.json
    sender_email = os.getenv("SMTP_EMAIL")
    receiver_email = data["to"]
    subject = data["subject"]
    body = data["body"]
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), 587) as server:
            server.starttls()
            server.login(sender_email, os.getenv("SMTP_PASSWORD"))
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return jsonify({"message": "Email sent successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to generate email content using Groq
@app.route('/generate-email', methods=['POST'])
def generate_email():
    data = request.json
    founder = Founder(**data)
    prompt = f"Generate an email for {founder.name} of {founder.company_name} in {founder.industry} industry. Pitch: {founder.pitch}"
    
    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are an email generator."},
                {"role": "user", "content": prompt}
            ]
        )
        email_content = response.choices[0].message.content
        return jsonify({"email_content": email_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True) 
