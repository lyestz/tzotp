import datetime
import pytz
import base64
import json
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Embed credentials JSON directly into the script
CREDENTIALS_JSON = {
    "installed": {
        "client_id": "your_client_id",
        "project_id": "your_project_id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "your_client_secret",
        "redirect_uris": ["http://localhost"]
    }
}

TOKEN_JSON = {
    "token": "your_token",
    "refresh_token": "your_refresh_token",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "scopes": SCOPES
}

app = Flask(__name__)

class GmailAPI:
    def __init__(self):
        self.creds = None
        if TOKEN_JSON:
            self.creds = Credentials.from_authorized_user_info(TOKEN_JSON, SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(CREDENTIALS_JSON, SCOPES)
                self.creds = flow.run_local_server(port=0)

    def get_ManageAppointment_otp(self, target):
        current_time = datetime.datetime.utcnow()
        time_threshold_start = current_time - datetime.timedelta(minutes=10)
        time_threshold_end = current_time + datetime.timedelta(minutes=10)
        
        time_start_unix = int(time_threshold_start.replace(tzinfo=pytz.UTC).timestamp())
        time_end_unix = int(time_threshold_end.replace(tzinfo=pytz.UTC).timestamp())
        
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            query = f"FROM:info@blsinternational.com TO:{target} SUBJECT:BLS Visa Appointment - Email Verification after:{time_start_unix} before:{time_end_unix}"
            results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
            messages = results.get('messages')
            if messages:
                txt = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
                return txt["snippet"].split("Your verification code is as mentioned below ")[1][:6]
            return "No OTP found"
        except HttpError as error:
            return f'An error occurred: {error}'

@app.route('/api/get_otp', methods=['GET'])
def get_otp():
    target = request.args.get('email')
    if not target:
        return jsonify({"error": "Email parameter is required"}), 400
    gmail_api = GmailAPI()
    otp = gmail_api.get_ManageAppointment_otp(target)
    return jsonify({"email": target, "otp": otp})

if __name__ == '__main__':
    app.run(debug=True)
