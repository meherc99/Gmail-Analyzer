"""
Gmail Updates Tab Email Deleter
This script deletes emails from the Updates category before a specific date.
"""

import os.path
import pickle
from datetime import datetime
from typing import List, Dict
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.utils import parsedate_to_datetime

# Modified scope to allow deletion
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def authenticate_gmail():
    """
    Authenticate and return Gmail API service instance with modify permissions.
    """
    creds = None
    # The file token_delete.pickle stores the user's access and refresh tokens
    # Using a different token file since we need modify scope
    if os.path.exists('token_delete.pickle'):
        with open('token_delete.pickle', 'rb') as token:
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
        with open('token_delete.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def parse_email_date(date_str: str) -> datetime:
    """
    Parse email date string to datetime object.
    
    Args:
        date_str: Date string from email
    
    Returns:
        datetime object
    """
    try:
        return parsedate_to_datetime(date_str)
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None


def load_emails(filename: str = 'emails.json') -> List[Dict]:
    """
    Load emails from JSON file.
    
    Args:
        filename: Path to the emails JSON file
    
    Returns:
        List of email dictionaries
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            emails = json.load(f)
        print(f"Loaded {len(emails)} emails from {filename}")
        return emails
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please run gmail_fetcher.py first.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filename}: {e}")
        return []


def filter_updates_before_date(emails: List[Dict], cutoff_date: datetime) -> List[Dict]:
    """
    Filter emails that are in Updates category and before the cutoff date.
    
    Args:
        emails: List of email dictionaries
        cutoff_date: Cutoff date (emails before this will be selected)
    
    Returns:
        List of emails to delete
    """
    emails_to_delete = []
    
    for email in emails:
        # Check if email is in Updates category
        labels = email.get('labels', [])
        if 'CATEGORY_UPDATES' not in labels:
            continue
        
        # Parse email date
        date_str = email.get('date', '')
        email_date = parse_email_date(date_str)
        
        if email_date and email_date < cutoff_date:
            emails_to_delete.append(email)
    
    return emails_to_delete


def delete_emails_batch(service, email_ids: List[str], batch_size: int = 100, dry_run: bool = True):
    """
    Delete emails in batches.
    
    Args:
        service: Authorized Gmail API service instance
        email_ids: List of email IDs to delete
        batch_size: Number of emails to delete per batch
        dry_run: If True, only show what would be deleted without actually deleting
    
    Returns:
        Number of successfully deleted emails
    """
    if not email_ids:
        print("No emails to delete.")
        return 0
    
    if dry_run:
        print(f"\n[DRY RUN MODE] Would delete {len(email_ids)} emails")
        return 0
    
    deleted_count = 0
    failed_count = 0
    
    print(f"\nDeleting {len(email_ids)} emails...")
    
    # Process in batches
    for i in range(0, len(email_ids), batch_size):
        batch = email_ids[i:i + batch_size]
        
        try:
            # Use batchDelete for efficiency (moves to trash)
            service.users().messages().batchDelete(
                userId='me',
                body={'ids': batch}
            ).execute()
            
            deleted_count += len(batch)
            print(f"Progress: {deleted_count}/{len(email_ids)} emails moved to trash")
            
        except HttpError as error:
            print(f"Error deleting batch: {error}")
            failed_count += len(batch)
    
    print(f"\nSuccessfully moved {deleted_count} emails to trash")
    if failed_count > 0:
        print(f"Failed to delete {failed_count} emails")
    
    return deleted_count


def display_preview(emails: List[Dict], limit: int = 10):
    """
    Display a preview of emails that will be deleted.
    
    Args:
        emails: List of emails to preview
        limit: Maximum number of emails to show
    """
    print("\n" + "="*100)
    print(f"PREVIEW OF EMAILS TO DELETE (showing {min(limit, len(emails))} of {len(emails)})")
    print("="*100)
    print(f"{'Date':<30} {'From':<40} {'Subject'}")
    print("-"*100)
    
    for email in emails[:limit]:
        date = email.get('date', 'Unknown')[:28]
        sender = email.get('from', 'Unknown')[:38]
        subject = email.get('subject', 'No Subject')[:40]
        
        print(f"{date:<30} {sender:<40} {subject}")
    
    if len(emails) > limit:
        print(f"\n... and {len(emails) - limit} more emails")
    print("="*100)


def main():
    """Main function to delete Updates emails before a specific date."""
    print("="*100)
    print("Gmail Updates Tab Email Deleter")
    print("="*100)
    
    # Get cutoff date from user
    print("\nEnter the cutoff date. Emails in the Updates tab BEFORE this date will be deleted.")
    print("Format: YYYY-MM-DD (e.g., 2024-01-01)")
    
    date_input = input("\nCutoff date: ").strip()
    
    try:
        cutoff_date = datetime.strptime(date_input, "%Y-%m-%d")
        # Make timezone aware (assume local timezone)
        cutoff_date = cutoff_date.replace(tzinfo=None)
        print(f"\nWill delete Updates emails before: {cutoff_date.strftime('%B %d, %Y')}")
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD")
        return
    
    # Load emails from JSON
    emails = load_emails('emails.json')
    
    if not emails:
        print("No emails to analyze. Exiting.")
        return
    
    # Filter emails to delete
    print("\nFiltering emails...")
    emails_to_delete = filter_updates_before_date(emails, cutoff_date)
    
    if not emails_to_delete:
        print(f"\nNo emails found in Updates tab before {cutoff_date.strftime('%B %d, %Y')}")
        return
    
    # Display preview
    display_preview(emails_to_delete)
    
    # Confirm with user
    print(f"\n⚠️  WARNING: This will move {len(emails_to_delete)} emails to trash!")
    print("You can restore them from trash within 30 days.")
    
    # Ask if user wants to proceed with dry run first
    dry_run_choice = input("\nDo you want to do a DRY RUN first? (y/n): ").strip().lower()
    
    if dry_run_choice == 'y':
        # Authenticate and run dry run
        print("\nAuthenticating with Gmail API...")
        service = authenticate_gmail()
        print("Authentication successful!")
        
        email_ids = [email['id'] for email in emails_to_delete]
        delete_emails_batch(service, email_ids, dry_run=True)
        
        proceed = input("\nProceed with actual deletion? (yes/no): ").strip().lower()
        if proceed != 'yes':
            print("Deletion cancelled.")
            return
    else:
        proceed = input("\nType 'DELETE' to confirm deletion: ").strip()
        if proceed != 'DELETE':
            print("Deletion cancelled.")
            return
    
    # Authenticate and delete
    print("\nAuthenticating with Gmail API...")
    service = authenticate_gmail()
    print("Authentication successful!")
    
    # Delete emails
    email_ids = [email['id'] for email in emails_to_delete]
    deleted_count = delete_emails_batch(service, email_ids, dry_run=False)
    
    print(f"\n✓ Done! {deleted_count} emails have been moved to trash.")
    print("You can restore them from the trash within 30 days if needed.")


if __name__ == '__main__':
    main()
