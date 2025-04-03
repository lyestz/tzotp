from fastapi import FastAPI, HTTPException, Query
from imap2dict import MailClient
from mangum import Mangum

app = FastAPI()

GMAIL_IMAP_HOST = "imap.gmail.com"
USER_ID = "frnnanniesairra195p@gmail.com"
PASSWORD = "fscmysjxgenfffcn"

@app.get("/fetch_mail")
def fetch_mail(
    search_option: str = "UNSEEN"
):
    cli = MailClient(GMAIL_IMAP_HOST, USER_ID, PASSWORD)
    messages = cli.fetch_mail(search_option=search_option)
    return {"status": "OK", "messages": messages}

@app.get("/delete_mail")
def delete_mail(
    days: int = 90
):
    cli = MailClient(GMAIL_IMAP_HOST, USER_ID, PASSWORD)
    delete_count = cli.delete_mail(days=days)
    return {"delete_count": delete_count}

handler = Mangum(app)

