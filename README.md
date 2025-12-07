# Email Summarizer

A privacy-focused local application that automates email triage by fetching emails via OAuth, cleaning content, generating AI-powered summaries with actionable insights, and presenting them through a beautiful web interface.

## Features

- 🔐 **Secure OAuth Authentication** - Connect to Gmail or Outlook without storing passwords
- 🤖 **AI-Powered Summaries** - Choose between local models (fully private) or remote LLMs (higher quality)
- 📧 **Smart Email Processing** - Automatically removes signatures, quoted replies, and HTML noise
- ✅ **Action Items & Deadlines** - Extracts actionable tasks and important dates
- 🌐 **Beautiful Web UI** - Clean, modern interface with filtering and search
- 🔒 **Privacy First** - All data stored locally, encryption by default
- 🏃 **Dry-Run Mode** - Preview what will happen before committing
- 💾 **Local Storage** - JSON files with optional SQLite indexing

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd email-summarizer
```

2. Create a virtual environment:
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Unix/macOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Setup

Run the interactive setup wizard:

```bash
python -m email_summarizer setup
```

The wizard will guide you through:
1. Choosing your email provider (Gmail or Outlook)
2. Entering OAuth credentials
3. Selecting summarizer engine (local or remote)
4. Configuring server settings

### OAuth Setup

#### Gmail

1. Visit [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app or Web app)
5. Set redirect URI to `http://localhost:8080/oauth2callback`
6. Request scope: `gmail.readonly`
7. Copy Client ID and Client Secret

#### Outlook/Office365

1. Visit [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
2. Register a new application
3. Add delegated permission: `Mail.Read`
4. Set redirect URI to `http://localhost:8080/oauth2callback`
5. Copy Application (client) ID and Client Secret

### Running the Application

Start the web server:

```bash
python -m email_summarizer serve
```

Then open your browser to `http://localhost:8080`

## Usage

### Web Interface

1. **Authorize** - Click "Authorize" to connect your email account
2. **Process Emails** - Click "Process Emails" to fetch and summarize
3. **View Summaries** - Browse your email digest with summaries, actions, and deadlines
4. **Provide Feedback** - Use thumbs up/down to rate summaries
5. **Filter & Search** - Find specific emails by sender, subject, or criteria

### Command Line

Process emails from CLI:
```bash
python -m email_summarizer process
```

Preview without saving (dry-run):
```bash
python -m email_summarizer process --dry-run
```

Erase all data:
```bash
python -m email_summarizer erase
```

## Configuration

Configuration is stored in `~/.email-summarizer/config.yaml`

### Email Provider
- `gmail` - Google Gmail
- `outlook` - Microsoft Outlook/Office365

### Fetch Rules
- `mode` - "unread", "last_n_days", or "all"
- `max_messages` - Maximum emails to fetch per run
- `days_back` - Days to look back (for last_n_days mode)

### Summarizer Engine

**Remote LLM** (OpenAI):
- Higher quality summaries
- Requires API key
- Sends email content to third-party service
- Requires explicit consent

**Local Model** (Hugging Face):
- Fully private (runs on your machine)
- No internet required for summarization
- May be slower
- Recommended models: `facebook/bart-large-cnn`, `google/pegasus-xsum`

### Storage
- `summaries_dir` - Directory for storing summaries
- `encrypt_bodies` - Encrypt email bodies (recommended)
- `use_sqlite_index` - Enable SQLite indexing for faster retrieval

## Privacy & Security

### Data Protection
- OAuth tokens encrypted with Fernet (symmetric encryption)
- Encryption keys stored in OS keyring
- Optional email body encryption
- Read-only email access by default

### What's Stored Locally
- Email summaries (sender, subject, summary, actions, deadlines)
- Optionally: encrypted email bodies
- OAuth refresh tokens (encrypted)
- Application logs (rotated after 7 days)

### Remote LLM Considerations
If using a remote LLM:
- Email content is sent to third-party service
- Explicit consent required
- Review provider's privacy policy
- Can switch to local model anytime

### Data Deletion
Use the "Erase All Data" button in the UI or run:
```bash
python -m email_summarizer erase
```

This removes:
- All summaries
- OAuth tokens
- Cached email content
- Application logs

## Project Structure

```
email-summarizer/
├── email_summarizer/
│   ├── auth/              # OAuth authentication
│   ├── config/            # Configuration management
│   ├── fetcher/           # Email fetching (Gmail/Outlook)
│   ├── preprocessor/      # Email cleaning
│   ├── summarizer/        # AI summarization
│   ├── storage/           # Data persistence
│   ├── orchestrator/      # Pipeline coordination
│   ├── web/               # Flask server & UI
│   ├── utils/             # Utilities (retry, logging)
│   ├── models.py          # Data models
│   ├── crypto.py          # Encryption utilities
│   └── cli.py             # Command-line interface
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

The project follows PEP 8 style guidelines.

## Troubleshooting

### OAuth Redirect Failing
- Ensure redirect URI in OAuth console exactly matches `http://localhost:8080/oauth2callback`
- Check that the port in config matches the server port

### Token Expired
- The app will automatically refresh expired tokens
- If refresh fails, re-authorize through the web UI

### Summarization Errors
- Check API key is correct (for remote LLM)
- Ensure sufficient disk space (for local model)
- Review logs in `~/.email-summarizer/logs/app.log`

### Empty Summaries
- Email may have been too short after cleaning
- Check preprocessor settings
- Try with different emails

## License

[Your License Here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
