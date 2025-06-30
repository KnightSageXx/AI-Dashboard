# Gmail Auto-Verification System

A complete Python-based Gmail auto-verification system that automates the process of verifying OpenRouter accounts using Gmail aliases.

## Features

- Uses the Gmail API (OAuth2) to read inbox messages
- Finds and opens OpenRouter verification emails
- Extracts verification links from email content
- Visits verification links using headless Chrome (Selenium)
- Tracks which Gmail aliases have been used via `used_emails.json`
- Automatically generates the next unused alias (e.g., `myemail+1@gmail.com`, `myemail+2@gmail.com`, etc.)
- Logs all alias usage and API key results to a file (`email_log.txt`)
- Modular code structure with separate components for each functionality

## Project Structure

```
├── gmail_verification.py     # Main script
├── credentials.json          # Gmail API credentials
├── token.json                # Gmail API token (auto-generated)
├── used_emails.json          # Tracks used aliases
├── email_log.txt             # Logs alias usage and API keys
├── utils/                    # Utility modules
│   ├── GmailReader.py        # Gmail API integration
│   ├── AliasManager.py       # Gmail alias management
│   └── Verifier.py           # Selenium-based verification
└── logs/                     # Log directory
    └── gmail_verification.log # Application logs
```

## Prerequisites

1. Python 3.8 or higher
2. A Gmail account
3. Chrome browser (for Selenium)
4. Gmail API credentials

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Gmail API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Gmail API for your project
4. Create OAuth 2.0 credentials:
   - Application type: Desktop application
   - Name: Gmail Verification
5. Download the credentials JSON file and save it as `credentials.json` in the project root directory

### 3. Configure the System

Edit the main script or use command-line arguments to configure the system:

```bash
python gmail_verification.py --base-email your.email@gmail.com
```

Available command-line arguments:

- `--base-email`: Your Gmail address (default: knightsagexf@gmail.com)
- `--credentials-path`: Path to the credentials.json file (default: credentials.json)
- `--token-path`: Path to the token.json file (default: token.json)
- `--used-emails-path`: Path to the JSON file tracking used aliases (default: used_emails.json)
- `--log-path`: Path to the log file for email usage (default: email_log.txt)
- `--headless`: Run Chrome in headless mode (flag, no value needed)
- `--max-retries`: Maximum number of retries for checking emails (default: 5)
- `--retry-delay`: Delay between retries in seconds (default: 60)

### 4. First Run Authentication

The first time you run the script, it will open a browser window asking you to authenticate with your Google account. Follow these steps:

1. Sign in with the Gmail account you want to use
2. Grant the requested permissions
3. The authentication token will be saved to `token.json` for future use

## Usage

Run the script to start the verification process:

```bash
python gmail_verification.py
```

The script will:

1. Generate a new Gmail alias
2. Check for verification emails
3. Extract the verification link
4. Visit the link using Selenium
5. Extract the API key
6. Log the results

## Integration with Other Systems

To integrate this system with other components:

1. Import the `GmailVerificationSystem` class from `gmail_verification.py`
2. Create an instance with your desired configuration
3. Call the `run()` method to start the verification process

Example:

```python
from gmail_verification import GmailVerificationSystem

system = GmailVerificationSystem(
    base_email='your.email@gmail.com',
    headless=True,
    max_retries=3
)

result = system.run()

if result['success']:
    api_key = result['api_key']
    # Use the API key as needed
```

## Limitations

- Gmail has a limit of approximately 500 aliases per day
- The Gmail API has usage quotas that may limit the number of API calls
- The verification process may break if OpenRouter changes their email format or website structure

## Troubleshooting

- If you encounter authentication issues, delete the `token.json` file and run the script again
- Check the logs in the `logs` directory for detailed error messages
- Make sure your Chrome browser is up to date for Selenium compatibility
- If the verification link extraction fails, you may need to update the regex pattern in `GmailReader.py`