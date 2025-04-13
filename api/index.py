from flask import Flask, request, jsonify
from flask_cors import CORS
import imaplib
import email
from email.utils import parsedate_to_datetime
from email.header import decode_header
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
import traceback

app = Flask(__name__)
CORS(app)

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
SPECIFIC_SENDER = "Info@blsinternational.com"
SPECIFIC_STRING = "BLS Visa Appointment - Email Verification"

def get_body(msg):
            try:
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition") or "")

                        if "attachment" not in content_disposition:
                            try:
                                if content_type == "text/plain":
                                    return part.get_payload(decode=True).decode(errors="ignore")
                                elif content_type == "text/html":
                                    html_content = part.get_payload(decode=True).decode(errors="ignore")
                                    soup = BeautifulSoup(html_content, "html.parser")
                                    return soup.get_text()
                            except Exception as decode_err:
                                print("Decode error:", decode_err)
                else:
                    return msg.get_payload(decode=True).decode(errors="ignore")
            except Exception as e:
                traceback.print_exc()
                return ""  # Always return a string, even if empty

def fetch_otp(from_email, password):
    try:
        imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap.login(from_email, password)
        imap.select("inbox")

        result, data = imap.search(None, f'FROM "{SPECIFIC_SENDER}"')
        mail_ids = data[0].split()
        if not mail_ids:
            return {"status": "no", "error": "No OTP found"}

        latest_email_id = mail_ids[-1]
        result, msg_data = imap.fetch(latest_email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        message = email.message_from_bytes(raw_email)

        email_subject = message["subject"]
        email_date = message["date"]

        if SPECIFIC_STRING in email_subject:
            email_time = parsedate_to_datetime(email_date)
            time_limit = email_time + timedelta(seconds=180)
            current_time = datetime.now(timezone.utc)

            if current_time <= time_limit:
                body = get_body(message)
                print(body)
                if not body or not isinstance(body, str):
                    return {"status": "no", "error": "Failed to extract body from email"}

                cleaned_body = body.replace("\r", "").replace("\n", " ").replace("<br>", "").strip()

                try:
                    otp = cleaned_body.split("mentioned below ")[1][:6]
                    imap.store(latest_email_id, '+FLAGS', '\\Deleted')
                    imap.expunge()
                    imap.logout()
                    return {"status": "ok", "otp": otp}
                except IndexError:
                    return {"status": "no", "error": "OTP format not found in email body"}
            else:
                imap.store(latest_email_id, '+FLAGS', '\\Deleted')
                imap.expunge()
                imap.logout()
                return {"status": "no", "error": "OTP expired"}
        else:
            imap.logout()
            return {"status": "no", "error": "No matching email found"}

    except Exception as e:
        traceback.print_exc()
        return {"status": "no", "error": str(e)}

@app.route('/get-otp', methods=['GET'])
def get_otp():
    from_email = request.args.get('email')
    password = request.args.get('password')

    if not from_email or not password:
        return jsonify({"status": "no", "error": "Missing email or password"}), 400

    result = fetch_otp(from_email, password)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
