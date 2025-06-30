# AI Control Dashboard

A web-based dashboard to manage and automate switching between different AI providers (OpenRouter, Phind, Ollama) with automatic key rotation.

## Features

- Auto-rotate OpenRouter API keys
- Switch between Claude (OpenRouter), Phind, and Ollama
- Monitor usage logs & key failures
- Manage temp emails to generate new OpenRouter accounts
- Automated workflow with zero manual intervention once set up

## Project Structure

```
├── README.md                 # Project documentation
├── app.py                    # Main Flask application
├── static/                   # Static files (CSS, JS)
│   ├── css/
│   │   └── style.css         # Custom styles
│   └── js/
│       └── dashboard.js      # Dashboard functionality
├── templates/                # HTML templates
│   ├── index.html            # Dashboard main page
│   └── logs.html             # Log viewer page
├── utils/                    # Utility modules
│   ├── __init__.py           # Package initialization
│   ├── config_manager.py     # Continue config management
│   ├── key_rotator.py        # OpenRouter key rotation
│   ├── provider_switch.py    # Provider switching logic
│   └── temp_email.py         # Temp email automation
├── config.json               # Application configuration
└── requirements.txt          # Python dependencies
```

## Setup Instructions

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure your settings in `config.json`:
   - Set your OpenRouter API keys (if you have any)
   - Configure your email in the `temp_email.user_email` field to use for OpenRouter signup
   - Adjust auto-rotation settings as needed

3. Run the application:
   ```
   python app.py
   ```

4. Access the dashboard at http://localhost:5000

## Troubleshooting

If you encounter any issues with the dashboard, please refer to the [Troubleshooting Guide](TROUBLESHOOTING.md) for solutions to common problems.

## Technologies Used

- **Frontend**: HTML, JavaScript, Bootstrap
- **Backend**: Python (Flask)
- **Continue Control**: Python file I/O
- **Temp Mail Script**: Selenium for browser automation
- **Logs & Fallback**: Python logging, subprocess, watchdog