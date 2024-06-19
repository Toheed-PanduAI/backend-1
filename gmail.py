from googleapiclient.discovery import build
from gmail_oauth import get_credentials

def list_messages():
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        print('Messages:')
        for message in messages:
            print(message)

if __name__ == '__main__':
    list_messages()
