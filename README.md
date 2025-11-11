# Gmail Email Fetcher

This Python script uses the Gmail API to fetch all emails from your Gmail account.

## Setup Instructions

### 1. Enable Gmail API and Get Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on it and press "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - Choose "External" user type
     - Fill in the required fields (app name, user support email, developer email)
     - Add your email as a test user
   - Choose "Desktop app" as the application type
   - Download the credentials and save as `credentials.json` in this directory

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Script

```bash
python gmail_fetcher.py
```

On first run:
- A browser window will open asking you to authorize the application
- Sign in with your Google account
- Grant the requested permissions
- A `token.pickle` file will be created to store your credentials for future runs

## Features

- Authenticates using OAuth 2.0
- Fetches all emails (or a specified number)
- Extracts key information: subject, sender, date, snippet
- Saves results to `emails.json`
- Progress tracking during fetch
- Token caching for faster subsequent runs

## Usage

### Fetch Limited Number of Emails

Edit `gmail_fetcher.py` and change:
```python
emails = fetch_all_emails(max_emails=100)  # Fetch only 100 emails
```

### Fetch All Emails

Edit `gmail_fetcher.py` and change:
```python
emails = fetch_all_emails(max_emails=None)  # Fetch all emails
```

## Output

The script generates:
- `emails.json`: JSON file containing all fetched email details
- Console output showing sample emails and progress

## Security Notes

- Keep `credentials.json` and `token.pickle` secure and never commit them to version control
- The script uses read-only scope (`gmail.readonly`)
- Add these files to `.gitignore`

## Troubleshooting

- **"credentials.json not found"**: Download OAuth credentials from Google Cloud Console
- **Authentication errors**: Delete `token.pickle` and re-authenticate
- **API quota exceeded**: Gmail API has usage limits; consider implementing rate limiting for very large mailboxes
