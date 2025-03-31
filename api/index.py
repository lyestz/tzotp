from flask import Flask, jsonify, request
import imaplib
import email
from flask_cors import CORS
from email.header import decode_header
import logging
import re
import os

app = Flask(__name__)
CORS(app)

# Disable Flask's default logging
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

# Email credentials (Use environment variables for security)
USERNAME = os.getenv("EMAIL_USERNAME", "massilaskadi@gmail.com")
PASSWORD = os.getenv("EMAIL_PASSWORD", "ibkidqshjxahdszh")
IMAP_SERVER = 'imap.gmail.com'

# Search string for email
SEARCH_STRING = "mentioned below"

def connect_to_imap():
    """Connect to IMAP server."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(USERNAME, PASSWORD)
        return mail
    except Exception as e:
        print(f"Error connecting to IMAP server: {e}")
        return None

def search_unread_emails(mail):
    """Search unread emails."""
    try:
        mail.select("inbox")
        status, messages = mail.search(None, 'UNSEEN')
        return messages[0].split() if status == "OK" else []
    except Exception as e:
        print(f"Error searching emails: {e}")
        return []

def check_and_delete_emails(mail, mymail, search_string):
    """Check and delete emails if they match criteria."""
    email_ids = search_unread_emails(mail)
    if not email_ids:
        return False, None

    for email_id in email_ids:
        try:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="replace")
                    from_email = msg.get("From")

                    if "Email Verification" in subject and mymail in from_email:
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

                        if search_string in body:
                            match = re.search(r'\b\d{6}\b', body)
                            if match:
                                verification_code = match.group()
                                print(verification_code)
                                mail.store(email_id, '+FLAGS', '\\Deleted')
                                return True, verification_code
                            else:
                                mail.store(email_id, '+FLAGS', '\\Deleted')
                                return True, "No code found"
                        else:
                            mail.store(email_id, '+FLAGS', '\\Deleted')
                            return True, "No code found"
        except Exception as e:
            print(f"Error processing email: {e}")

    mail.expunge()
    return False, None

@app.route('/check-emails', methods=['GET'])
def check_emails_api():
    """API endpoint to check emails."""
    mail = connect_to_imap()
    if not mail:
        return jsonify({"message": "Failed to connect to the IMAP server."}), 500
    
    myemail = request.args.get('Email')
    result, email_body = check_and_delete_emails(mail, myemail, SEARCH_STRING)
    mail.close()
    mail.logout()

    return jsonify({"status": "ok" if result else "no", "email_body": email_body}), (200 if result else 404)

# Vercel needs `app` to be exposed
if __name__ == "__main__":
    app.run(debug=True)
