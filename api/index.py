from flask import Flask, jsonify, request
import imaplib
import email
from flask_cors import CORS
from email.header import decode_header
from gevent.pywsgi import WSGIServer
import re
import logging
import os
os.system('color')
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.WARNING)
search_string = "I have read and understood the information"
username = "frnnanniesairra195p@gmail.com"
password = "fscmysjxgenfffcn"

def connect_to_gmail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)
    return mail

def search_unread_emails(mail):
    mail.select("inbox")
    status, messages = mail.search(None, 'UNSEEN')
    return messages[0].split()

def check_and_delete_emails(mail, search_string, an):
    email_ids = search_unread_emails(mail)
    if not email_ids:
        return False, None
    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["To"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                string_found = False
                email_body = None
                if msg.is_multipart():
                    for part in msg.walk():
                        try:
                            body = part.get_payload(decode=True).decode()
                            if search_string in body and an in subject:
                                string_found = True
                                email_body = body
                                break
                        except:
                            pass
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                        if search_string in body and an in subject:
                            string_found = True
                            email_body = body
                    except:
                        pass

                if string_found:
                    print(f"Deleting email with subject: {subject}")
                    url_pattern = r'http[s]?://[^\s]+click\?upn[^\s]*>'
                    urls = re.findall(url_pattern, email_body)[0].replace(">", "")
                    mail.store(email_id, '+FLAGS', '\\Deleted')
                    return True, urls

    mail.expunge()
    return False, None

@app.route('/check-emails', methods=['GET'])

def check_emails_api():
    email = request.args.get('email')
    mail = connect_to_gmail()
    result, email_body = check_and_delete_emails(mail, search_string, email)
    mail.close()
    mail.logout()
    if result:
        print(f"\033[92m>{email}: Statue:Delivred. \033[92m")
        return jsonify({"status": "ok", "email_body": email_body})
        
    else:
        return jsonify({"status": "no"})

if __name__ == '__main__':
    ascii_art = '''
    \033[92m▄▄▄█████▓▒███████▒     ██████  ██▓███   ▄▄▄       ██▀███  ▄▄▄█████▓
    ▓  ██▒ ▓▒▒ ▒ ▒ ▄▀░   ▒██    ▒ ▓██░  ██▒▒████▄    ▓██ ▒ ██▒▓  ██▒ ▓▒
    ▒ ▓██░ ▒░░ ▒ ▄▀▒░    ░ ▓██▄   ▓██░ ██▓▒▒██  ▀█▄  ▓██ ░▄█ ▒▒ ▓██░ ▒░
    ░ ▓██▓ ░   ▄▀▒   ░     ▒   ██▒▒██▄█▓▒ ▒░██▄▄▄▄██ ▒██▀▀█▄  ░ ▓██▓ ░ 
      ▒██▒ ░ ▒███████▒   ▒██████▒▒▒██▒ ░  ░ ▓█   ▓██▒░██▓ ▒██▒  ▒██▒ ░ 
      ▒ ░░   ░▒▒ ▓░▒░▒   ▒ ▒▓▒ ▒ ░▒▓▒░ ░  ░ ▒▒   ▓▒█░░ ▒▓ ░▒▓░  ▒ ░░   
        ░    ░░▒ ▒ ░ ▒   ░ ░▒  ░ ░░▒ ░       ▒   ▒▒ ░  ░▒ ░ ▒░    ░    
      ░      ░ ░ ░ ░ ░   ░  ░  ░  ░░         ░   ▒     ░░   ░   ░      \033[0m'''
    print(ascii_art)
    print('\033[94m                 Data protection Bls Snifer SPART V:1.01\033[0m')
    http_server = WSGIServer(('127.0.0.1', 3000), app)
    http_server.serve_forever()
