import imaplib
import email
import datetime
import pytz
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Gmail IMAP settings
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_ACCOUNT = "massilaskadi@gmail.com"
EMAIL_PASSWORD = "rqpujwulgfeyzxer"

app = Flask(__name__)
CORS(app)

# Disable Flask's default logging
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

class IMAPGmail:
    def __init__(self):
        self.mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        self.mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        self.mail.select("inbox")

    def get_ManageAppointment_otp(self, target):
        current_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        time_threshold_start = current_time - datetime.timedelta(minutes=10)
        time_threshold_end = current_time + datetime.timedelta(minutes=10)
        date_since = time_threshold_start.strftime("%d-%b-%Y")
        date_before = time_threshold_end.strftime("%d-%b-%Y")
        search_criteria = f'(FROM "info@blsinternational.com" TO "{target}" SUBJECT "BLS Visa Appointment - Email Verification" SINCE "{date_since}" BEFORE "{date_before}")'
        try:
            status, message_ids = self.mail.search(None, search_criteria)
            if status != "OK" or not message_ids[0]:
                return "No OTP found"

            message_ids = message_ids[0].split()
            latest_email_id = message_ids[-1]
            status, msg_data = self.mail.fetch(latest_email_id, "(RFC822)")
            if status != "OK":
                return "Error fetching email"

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            email_body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        email_body = part.get_payload(decode=True).decode(errors='ignore')
                        break
            else:
                email_body = msg.get_payload(decode=True).decode(errors='ignore')

            otp_start = "Your verification code is as mentioned below "
            if otp_start in email_body:
                return email_body.split(otp_start)[1][:6]

            return "No OTP found"
        except Exception as e:
            return f'An error occurred: {e}'
        finally:
            self.mail.logout()

@app.route('/get_otp', methods=['GET'])
def get_otp():
    target = request.args.get('email')
    if not target:
        return jsonify({"error": "Email parameter is required"}), 400

    imap_gmail = IMAPGmail()
    otp = imap_gmail.get_ManageAppointment_otp(target)
    return jsonify({"email": target, "otp": otp})

if __name__ == '__main__':
    app.run(debug=True)
