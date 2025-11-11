"""
Gmail Email Fetcher
This script uses the Gmail API to fetch all emails from your Gmail account.
"""

import os.path
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def authenticate_gmail():
    """
    Authenticate and return Gmail API service instance.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json not found. Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def get_all_messages(service, user_id='me', max_results=None):
    """
    Fetch all message IDs from Gmail.
    
    Args:
        service: Authorized Gmail API service instance
        user_id: User's email address (default: 'me' for authenticated user)
        max_results: Maximum number of messages to retrieve (None for all)
    
    Returns:
        List of message IDs
    """
    try:
        messages = []
        request = service.users().messages().list(userId=user_id, maxResults=500)
        
        while request is not None:
            response = request.execute()
            
            if 'messages' in response:
                messages.extend(response['messages'])
                print(f"Fetched {len(messages)} message IDs so far...")
            
            # Check if we've reached the max_results limit
            if max_results and len(messages) >= max_results:
                messages = messages[:max_results]
                break
            
            request = service.users().messages().list_next(request, response)
        
        print(f"Total messages found: {len(messages)}")
        return messages
    
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []


def get_message_details(service, user_id, msg_id):
    """
    Get detailed information about a specific message.
    
    Args:
        service: Authorized Gmail API service instance
        user_id: User's email address
        msg_id: Message ID
    
    Returns:
        Dictionary containing message details
    """
    try:
        message = service.users().messages().get(
            userId=user_id, 
            id=msg_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = message['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        
        return {
            'id': msg_id,
            'thread_id': message.get('threadId', ''),
            'subject': subject,
            'from': sender,
            'date': date,
            'snippet': message.get('snippet', ''),
            'labels': message.get('labelIds', [])
        }
    
    except HttpError as error:
        print(f'An error occurred fetching message {msg_id}: {error}')
        return None


def fetch_all_emails(max_emails=None):
    """
    Main function to fetch all emails from Gmail.
    
    Args:
        max_emails: Maximum number of emails to fetch (None for all)
    
    Returns:
        List of email details
    """
    print("Authenticating with Gmail API...")
    service = authenticate_gmail()
    print("Authentication successful!")
    
    print("\nFetching message IDs...")
    messages = get_all_messages(service, max_results=max_emails)
    
    if not messages:
        print("No messages found.")
        return []
    
    print(f"\nFetching details for {len(messages)} messages...")
    all_emails = []
    
    for i, msg in enumerate(messages, 1):
        if i % 100 == 0:
            print(f"Processing message {i}/{len(messages)}...")
        
        details = get_message_details(service, 'me', msg['id'])
        if details:
            all_emails.append(details)
    
    print(f"\nSuccessfully fetched {len(all_emails)} emails!")
    return all_emails


if __name__ == '__main__':
    # Fetch all emails (or specify a limit, e.g., max_emails=100)
    emails = fetch_all_emails(max_emails=100)  # Change to None to fetch all
    
    # Display sample results
    if emails:
        print("\n" + "="*80)
        print("SAMPLE EMAILS (first 5):")
        print("="*80)
        for email in emails[:5]:
            print(f"\nSubject: {email['subject']}")
            print(f"From: {email['from']}")
            print(f"Date: {email['date']}")
            print(f"Snippet: {email['snippet'][:100]}...")
            print("-"*80)
        
        # Optional: Save to a file
        import json
        with open('emails.json', 'w', encoding='utf-8') as f:
            json.dump(emails, f, indent=2, ensure_ascii=False)
        print(f"\nAll emails saved to emails.json")
