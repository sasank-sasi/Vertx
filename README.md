# AI-Powered Investor Email Pipeline

Automates personalized investor email generation and sending using Groq API.

## Features

* AI-driven email variants (business, personal, metrics, vision).
* Custom prompts and templates.
* Email verification (greeting, signature, length, call to action).
* SMTP email sending.
* CSV and JSON logging.
* Interactive CLI.

## Installation

```bash
git clone https://github.com/vinod-polinati/VertxAI.git
cd VertxAI
python3 -m venv env && source env/bin/activate  # or env\Scripts\activate on Windows
pip install -r requirements.txt
# Create .env: GROQ_API_KEY, EMAIL_SENDER, EMAIL_PASSWORD
```

## Usage
```bash
python pipeline.py
```
Follow CLI prompts to generate, review, and send emails.

## Logging
logs/email_logs.json (JSON)
logs/email_logs.csv (CSV)
