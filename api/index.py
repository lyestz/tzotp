import imaplib
import email
import os
import re
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from email.header import decode_header

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

SEARCH_STRING = "I have read and understood the information"

# Use environment variables for security
USERNAME = os.getenv("EMAIL_USERNAME", "your_email@gmail.com")
PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")


def connect_to_gmail():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(USERNAME, PASSWORD)
        return mail
    except Exception as e:
        logging.error(f"Failed to connect to Gmail: {e}")
        return None


def search_unread_emails(mail):
    try:
        mail.select("inbox")
        status, messages = mail.search(None, "UNSEEN")
        return messages[0].split()
    except Exception as e:
        logging.error(f"Error searching unread emails: {e}")
        return []


def check_and_delete_emails(mail, search_string, recipient_email):
    email_ids = search_unread_emails(mail)
    if not email_ids:
        return False, None

    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # Decode email subject
                subject, encoding = decode_header(msg["To"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                string_found = False
                email_body = None

                if msg.is_multipart():
                    for part in msg.walk():
                        try:
                            body = part.get_payload(decode=True).decode()
                            if search_string in body and recipient_email in subject:
                                string_found = True
                                email_body = body
                                break
                        except Exception:
                            pass
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                        if search_string in body and recipient_email in subject:
                            string_found = True
                            email_body = body
                    except Exception:
                        pass

                if string_found:
                    print(f"Deleting email with subject: {subject}")
                    url_pattern = r"https?://[^\s]+click\?upn[^\s]*>"
                    urls = re.findall(url_pattern, email_body)
                    if urls:
                        urls = urls[0].replace(">", "")

                    mail.store(email_id, "+FLAGS", "\\Deleted")
                    return True, urls

    mail.expunge()
    return False, None


@app.route("/api/check-emails", methods=["GET"])
def check_emails_api():
    recipient_email = request.args.get("email")
    if not recipient_email:
        return jsonify({"status": "error", "message": "Missing email parameter"}), 400

    mail = connect_to_gmail()
    if not mail:
        return jsonify({"status": "error", "message": "Failed to connect to email server"}), 500

    result, email_body = check_and_delete_emails(mail, SEARCH_STRING, recipient_email)

    mail.close()
    mail.logout()

    if result:
        return jsonify({"status": "ok", "email_body": email_body})

    return jsonify({"status": "no"})


# Vercel handler
def handler(event, context):
    return app(event, context)
