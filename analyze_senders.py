"""
Email Senders Analysis
This script analyzes emails from emails.json to find the most common senders.
"""

import json
import re
from collections import Counter
from typing import List, Tuple


def extract_email_address(from_field: str) -> str:
    """
    Extract email address from the 'From' field.
    Handles formats like: "Name <email@example.com>" or "email@example.com"
    
    Args:
        from_field: The 'from' field value from email
    
    Returns:
        Extracted email address
    """
    # Try to extract email from angle brackets first
    match = re.search(r'<([^>]+)>', from_field)
    if match:
        return match.group(1).strip().lower()
    
    # If no angle brackets, try to find email pattern
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_field)
    if email_match:
        return email_match.group(0).strip().lower()
    
    # Return as-is if no pattern matched
    return from_field.strip().lower()


def extract_sender_name(from_field: str) -> str:
    """
    Extract sender name from the 'From' field.
    
    Args:
        from_field: The 'from' field value from email
    
    Returns:
        Sender name or email if name not available
    """
    # Try to extract name before angle bracket
    match = re.search(r'^([^<]+)<', from_field)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        if name:
            return name
    
    # Return email address if no name found
    return extract_email_address(from_field)


def load_emails(filename: str = 'emails.json') -> List[dict]:
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


def analyze_senders(emails: List[dict], top_n: int = 20) -> List[Tuple[str, str, int]]:
    """
    Analyze emails to find the most common senders.
    
    Args:
        emails: List of email dictionaries
        top_n: Number of top senders to return
    
    Returns:
        List of tuples (email, name, count) sorted by count
    """
    sender_info = {}  # email -> (name, count)
    
    for email in emails:
        from_field = email.get('from', '')
        if not from_field:
            continue
        
        email_addr = extract_email_address(from_field)
        name = extract_sender_name(from_field)
        
        if email_addr in sender_info:
            sender_info[email_addr] = (sender_info[email_addr][0], sender_info[email_addr][1] + 1)
        else:
            sender_info[email_addr] = (name, 1)
    
    # Sort by count (descending)
    sorted_senders = sorted(sender_info.items(), key=lambda x: x[1][1], reverse=True)
    
    # Return top N as (email, name, count)
    return [(email, info[0], info[1]) for email, info in sorted_senders[:top_n]]


def display_results(top_senders: List[Tuple[str, str, int]], total_emails: int):
    """
    Display the analysis results in a formatted way.
    
    Args:
        top_senders: List of (email, name, count) tuples
        total_emails: Total number of emails analyzed
    """
    print("\n" + "="*100)
    print(f"TOP {len(top_senders)} MOST COMMON SENDERS")
    print("="*100)
    print(f"{'Rank':<6} {'Count':<8} {'Percentage':<12} {'Sender Name':<30} {'Email Address'}")
    print("-"*100)
    
    for rank, (email, name, count) in enumerate(top_senders, 1):
        percentage = (count / total_emails * 100) if total_emails > 0 else 0
        # Truncate name if too long
        display_name = name[:28] + ".." if len(name) > 30 else name
        print(f"{rank:<6} {count:<8} {percentage:>6.2f}%      {display_name:<30} {email}")
    
    print("="*100)
    
    # Summary statistics
    total_from_top = sum(count for _, _, count in top_senders)
    top_percentage = (total_from_top / total_emails * 100) if total_emails > 0 else 0
    print(f"\nTop {len(top_senders)} senders account for {total_from_top} emails ({top_percentage:.2f}% of total)")


def save_results(top_senders: List[Tuple[str, str, int]], filename: str = 'sender_analysis.json'):
    """
    Save analysis results to a JSON file.
    
    Args:
        top_senders: List of (email, name, count) tuples
        filename: Output filename
    """
    results = [
        {
            'rank': rank,
            'email': email,
            'name': name,
            'count': count
        }
        for rank, (email, name, count) in enumerate(top_senders, 1)
    ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {filename}")


def main():
    """Main function to run the sender analysis."""
    # Load emails
    emails = load_emails('emails.json')
    
    if not emails:
        print("No emails to analyze. Exiting.")
        return
    
    # Analyze senders
    print("\nAnalyzing senders...")
    top_senders = analyze_senders(emails, top_n=20)
    
    # Display results
    display_results(top_senders, len(emails))
    
    # Save results
    save_results(top_senders, 'sender_analysis.json')


if __name__ == '__main__':
    main()
