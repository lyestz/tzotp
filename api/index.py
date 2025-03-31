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
        error_message = f"Error connecting to IMAP server: {str(e)}"
        app.logger.error(error_message)
        return None, error_message

def search_unread_emails(mail):
    """Search unread emails."""
    try:
        mail.select("inbox")
        status, messages = mail.search(None, 'UNSEEN')
        return messages[0].split() if status == "OK" else []
    except Exception as e:
        error_message = f"Error searching emails: {str(e)}"
        app.logger.error(error_message)
        return [], error_message

def check_and_delete_emails(mail, mymail, search_string):
    """Check and delete emails if they match criteria."""
    email_ids, search_error = search_unread_emails(mail)
    if search_error:
        return False, None, search_error

    if not email_ids:
        return False, None, "No unread emails found."

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
                            verification_code = match.group() if match else "No code found"
                            mail.store(email_id, '+FLAGS', '\\Deleted')
                            return True, verification_code, None
                        else:
                            mail.store(email_id, '+FLAGS', '\\Deleted')
                            return True, "No code found", None
        except Exception as e:
            error_message = f"Error processing email: {str(e)}"
            app.logger.error(error_message)
            return False, None, error_message

    mail.expunge()
    return False, None, "No matching emails found."

@app.route('/check-emails', methods=['GET'])
def check_emails_api():
    """API endpoint to check emails."""
    mail, connection_error = connect_to_imap()
    if not mail:
        return jsonify({"status": "error", "message": connection_error}), 500
    
    myemail = request.args.get('Email')
    if not myemail:
        return jsonify({"status": "error", "message": "Email parameter is required."}), 400

    result, email_body, error = check_and_delete_emails(mail, myemail, SEARCH_STRING)
    
    mail.close()
    mail.logout()

    if error:
        return jsonify({"status": "error", "message": error}), 500
    return jsonify({"status": "ok" if result else "no", "email_body": email_body}), (200 if result else 404)

# Vercel needs `app` to be exposed
if __name__ == "__main__":
    app.run(debug=True)
