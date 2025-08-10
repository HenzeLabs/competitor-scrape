import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

def write_to_google_doc(doc_id, text):
    SCOPES = ['https://www.googleapis.com/auth/documents']
    SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('docs', 'v1', credentials=creds)
    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': text + "\n\n"
            }
        }
    ]
    service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
