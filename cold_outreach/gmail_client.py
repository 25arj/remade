import base64
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_gmail_service(credentials_file: str, token_file: str):
    """OAuth for your own Gmail inbox. First run opens a browser to
    authorize; after that the token is cached in token_file and refreshed
    automatically.
    """
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, _SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, _SCOPES)
            creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(token_file) or ".", exist_ok=True)
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def send_email(service, from_email: str, to_email: str, subject: str, body: str) -> None:
    message = MIMEText(body)
    message["to"] = to_email
    message["from"] = from_email
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def has_reply_from(service, email: str, since_iso: str) -> bool:
    since_date = since_iso.split("T")[0].replace("-", "/")
    query = f"from:{email} after:{since_date}"
    result = service.users().messages().list(userId="me", q=query, maxResults=1).execute()
    return bool(result.get("messages"))
