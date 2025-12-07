# Quick Start Guide

Get up and running with Email Summarizer in 5 minutes!

## Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Get OAuth Credentials

### For Gmail:

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new project (or select existing)
3. Click "Create Credentials" → "OAuth client ID"
4. Choose "Desktop app" or "Web application"
5. Add redirect URI: `http://localhost:8080/oauth2callback`
6. Enable Gmail API in the API Library
7. Copy your Client ID and Client Secret

### For Outlook:

1. Go to https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps
2. Click "New registration"
3. Add redirect URI: `http://localhost:8080/oauth2callback`
4. Go to "API permissions" → Add "Mail.Read" (delegated)
5. Go to "Certificates & secrets" → Create new client secret
6. Copy your Application (client) ID and Client Secret

## Step 3: Run Setup

```bash
python -m email_summarizer setup
```

Follow the prompts:
- Choose email provider (Gmail or Outlook)
- Enter OAuth Client ID and Secret
- Choose summarizer:
  - **Remote (OpenAI)**: Better quality, needs API key
  - **Local**: Fully private, runs on your machine
- Set server port (default: 8080)

## Step 4: Start the Server

```bash
python -m email_summarizer serve
```

## Step 5: Use the Web Interface

1. Open http://localhost:8080 in your browser
2. Click **"Authorize"** to connect your email
3. Grant read-only access when prompted
4. Click **"Process Emails"** to fetch and summarize
5. View your email digest!

## Tips

### Dry-Run Mode
Test without saving:
1. Click "Toggle Dry-Run" in the UI
2. Click "Process Emails"
3. See what would happen without committing

### Filtering
- Use the search box to find emails by sender or subject
- Filter by "Has Actions" or "Has Deadlines"
- Filter by date

### Feedback
- Click 👍 or 👎 on summaries to rate them
- Helps improve future summaries

### Privacy
- All data stored in `~/.email-summarizer/`
- OAuth tokens are encrypted
- Use "Erase All Data" to delete everything

## Troubleshooting

**"Configuration not found"**
→ Run `python -m email_summarizer setup` first

**"Not authenticated"**
→ Click "Authorize" in the web UI

**"Rate limit exceeded"**
→ Wait a moment and try again (automatic retry with backoff)

**Empty summaries**
→ Try with different emails or check logs in `~/.email-summarizer/logs/`

## Next Steps

- Configure fetch rules in `~/.email-summarizer/config.yaml`
- Switch between local and remote summarizers
- Set up scheduled processing (cron job)
- Review privacy settings

## Getting Help

- Check the full README.md for detailed documentation
- Review logs: `~/.email-summarizer/logs/app.log`
- Open an issue on GitHub

Enjoy your AI-powered email digest! 📧✨
