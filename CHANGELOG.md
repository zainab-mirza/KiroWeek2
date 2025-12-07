# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Email Summarizer
- OAuth authentication for Gmail and Outlook
- Email fetching with configurable rules
- Email preprocessing (HTML cleaning, signature removal, quote removal)
- AI-powered summarization (local and remote)
- Action item and deadline extraction
- Beautiful web UI with filtering and search
- Feedback system for summaries
- Dry-run mode for previewing
- Privacy-focused design with local storage
- Encryption for sensitive data
- CLI with interactive setup wizard
- Consent system for remote LLM usage
- Comprehensive logging with rotation
- Error handling with retry logic

### Security
- OAuth tokens encrypted with Fernet
- Secrets stored in OS keyring
- Optional email body encryption
- Read-only email access by default

## [0.1.0] - 2025-12-07

### Added
- Initial alpha release
- Core functionality implemented
- Documentation and setup guides

[Unreleased]: https://github.com/yourusername/email-summarizer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/email-summarizer/releases/tag/v0.1.0
