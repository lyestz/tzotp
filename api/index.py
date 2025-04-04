from flask import Flask, request, jsonify
from flask_cors import CORS
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import traceback


app = Flask(__name__)
CORS(app)

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
SPECIFIC_SENDER = "massilaskadi@gmail.com"
SPECIFIC_STRING = "BLS Visa Appointment - Email Verification"

def get_body(msg):
    try:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        return part.get_payload(decode=True).decode()
                    elif content_type == "text/html":
                        html_content = part.get_payload(decode=True).decode()
                        soup = BeautifulSoup(html_content, "html.parser")
                        return soup.get_text()
        else:
            return msg.get_payload(decode=True).decode()
    except Exception as e:
        return {"statue":"no","error": "No OTP found"}

def fetch_otp(from_email, password):
    try:
        imap = imaplib.IMAP4_SSL(IMAP_SERVER)
        imap.login(from_email, password)
        imap.select("inbox")

        result, data = imap.search(None, f'FROM "{SPECIFIC_SENDER}"')
        mail_ids = data[0].split()
        if not mail_ids:
            return {"statue":"no","error": "No OTP found"}

        latest_email_id = mail_ids[-1]
        result, msg_data = imap.fetch(latest_email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        message = email.message_from_bytes(raw_email)

        email_subject = message["subject"]
        email_from = message["from"]
        email_date = message["date"]

        if SPECIFIC_SENDER in email_from and SPECIFIC_STRING in email_subject:
            email_time = email.utils.parsedate_to_datetime(email_date)
            mail_time_plus_60 = email_time + timedelta(seconds=60)
            current_time = datetime.now()

            if current_time.timestamp() < mail_time_plus_60.timestamp():
                body = get_body(message)
                body1 = body.replace("\r\n", " ").replace("\n", " ").strip()
                otp = body1.split("mentioned below ")[1][:6]
                imap.store(latest_email_id, '+FLAGS', '\\Deleted')
                imap.expunge()
                imap.logout()
                return {"statue":"ok","otp": otp}
            else:
                imap.store(latest_email_id, '+FLAGS', '\\Deleted')
                imap.expunge()
                imap.logout()
                return {"statue":"no","error": "No OTP found"}
        else:
            imap.logout()
            return {"statue":"no","error": "No OTP found"}

    except Exception as e:
        traceback.print_exc()
        return {"statue":"no","errora": str(e)}

@app.route('/get-otp', methods=['GET'])
def get_otp():
    from_email = request.args.get('email')
    password = request.args.get('password')

    if not from_email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    result = fetch_otp(from_email, password)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
