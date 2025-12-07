# Implementation Plan

- [x] 1. Set up project structure and dependencies



  - Create Python package structure with modules for config, auth, fetcher, preprocessor, summarizer, storage, orchestrator, and web
  - Create requirements.txt with dependencies: Flask, google-auth-oauthlib, google-api-python-client, msal, beautifulsoup4, cryptography, transformers, openai, pyyaml, hypothesis
  - Create .gitignore to exclude config files with secrets, tokens, summaries, logs, and virtual environment
  - Set up basic package __init__.py files
  - _Requirements: 2.5_

- [x] 2. Implement core data models


  - Create dataclasses for Config, Credentials, RawEmail, CleanedEmail, EmailSummary, Feedback, ProcessingResult
  - Implement validation methods for each model
  - _Requirements: 1.3, 2.3, 3.4, 4.4, 5.2, 6.1_

- [ ]* 2.1 Write property test for configuration persistence
  - **Property 2: Configuration persistence**
  - **Validates: Requirements 2.3**



- [ ] 3. Implement Configuration Manager
  - Create ConfigManager class with load_config, save_config, get_secret, set_secret, validate_config methods
  - Implement YAML config file parsing and writing
  - Integrate with OS keyring using keyring library for secret storage
  - Implement config validation with clear error messages
  - Create default config template
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 3.1 Write property test for encryption round-trip
  - **Property 1: Encryption round-trip consistency**


  - **Validates: Requirements 1.3, 2.2, 2.4, 6.2, 8.2**

- [ ] 4. Implement encryption utilities
  - Create encryption module using cryptography library with Fernet



  - Implement encrypt and decrypt functions for tokens and sensitive data
  - Implement key derivation from OS keyring or user passphrase
  - _Requirements: 1.3, 2.2, 2.4, 6.2, 8.2_

- [x] 5. Implement OAuth Authentication Module


  - Create OAuthAuthenticator base class with abstract methods
  - Implement GmailAuthenticator with get_authorization_url, handle_callback, refresh_token methods
  - Implement OutlookAuthenticator with MSAL integration
  - Implement token storage and retrieval with encryption
  - Implement token validation and expiry checking
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1, 8.2_

- [ ] 6. Implement Email Fetcher
  - Create EmailFetcher base class with abstract methods
  - Implement GmailFetcher using google-api-python-client
  - Implement OutlookFetcher using Microsoft Graph API
  - Implement fetch_emails method with support for fetch rules (unread, date range, max messages)
  - Implement dry-run mode that skips persistence
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.1, 9.4_

- [ ]* 6.1 Write property test for fetch rule filtering
  - **Property 3: Fetch rule filtering**
  - **Validates: Requirements 3.1, 3.2**

- [ ]* 6.2 Write property test for fetch limit enforcement
  - **Property 4: Fetch limit enforcement**
  - **Validates: Requirements 3.3**



- [ ]* 6.3 Write property test for required field extraction
  - **Property 5: Required field extraction**
  - **Validates: Requirements 3.4**

- [ ]* 6.4 Write property test for dry-run side effects
  - **Property 6: Dry-run has no side effects**
  - **Validates: Requirements 3.5, 9.1, 9.2, 9.4**

- [ ] 7. Implement Email Preprocessor
  - Create EmailPreprocessor class with clean_email method
  - Implement html_to_text using beautifulsoup4 to convert HTML to plain text while preserving paragraphs
  - Implement remove_quoted_replies to detect and remove lines starting with > and "On ... wrote:" patterns
  - Implement remove_signature to detect and remove signature blocks (-- delimiter, "Regards,", contact info)
  - Implement extract_main_content to normalize whitespace
  - Handle empty body edge case with logging
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x]* 7.1 Write property test for HTML to text conversion


  - **Property 7: HTML to text preserves structure**
  - **Validates: Requirements 4.1**

- [ ]* 7.2 Write property test for content cleaning
  - **Property 8: Content cleaning removes noise**
  - **Validates: Requirements 4.2, 4.3**

- [ ]* 7.3 Write property test for attachment metadata
  - **Property 9: Attachment metadata preservation**
  - **Validates: Requirements 4.4**

- [ ] 8. Implement Summarizer Engine
  - Create SummarizerEngine abstract base class
  - Implement LocalSummarizer using transformers library (BART/Pegasus/T5)
  - Implement RemoteSummarizer using OpenAI SDK
  - Implement prompt template formatting with all required fields
  - Implement JSON response parsing and validation
  - Implement retry logic for JSON parsing failures
  - Implement input truncation for token limits
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_


- [x]* 8.1 Write property test for summarizer input structure


  - **Property 10: Summarizer receives structured input**
  - **Validates: Requirements 5.1**

- [ ]* 8.2 Write property test for summary output validation
  - **Property 11: Summary output structure validation**
  - **Validates: Requirements 5.2**

- [ ]* 8.3 Write property test for input truncation
  - **Property 12: Input truncation respects limits**
  - **Validates: Requirements 5.4**

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement Storage Manager
  - Create StorageManager class with save_summary, get_summary, list_summaries, delete_summary, delete_all methods
  - Implement JSON file writing with consistent naming convention (YYYY-MM-DD_msgid.json)
  - Implement directory structure creation (~/.email-summarizer/summaries/)
  - Implement optional SQLite index for efficient retrieval


  - Implement save_feedback and retrieve feedback functionality
  - Implement encryption for stored email bodies if configured
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.5_

- [ ]* 10.1 Write property test for summary persistence
  - **Property 13: Summary persistence round-trip**
  - **Validates: Requirements 6.1**

- [ ]* 10.2 Write property test for file naming
  - **Property 14: File naming consistency**
  - **Validates: Requirements 6.3**



- [ ]* 10.3 Write property test for feedback persistence
  - **Property 19: Feedback persistence round-trip**
  - **Validates: Requirements 7.5**

- [ ] 11. Implement Email Processing Orchestrator
  - Create EmailOrchestrator class that coordinates fetcher, preprocessor, summarizer, and storage
  - Implement process_emails method that runs the full pipeline
  - Implement process_single_email for individual email processing
  - Implement dry-run mode support that skips persistence and summarization
  - Implement error handling for each pipeline stage
  - Return ProcessingResult with statistics
  - _Requirements: 3.5, 9.1, 9.2, 9.3, 9.4, 9.5_



- [ ]* 11.1 Write property test for dry-run statistics
  - **Property 20: Dry-run provides preview statistics**
  - **Validates: Requirements 9.3**

- [ ] 12. Implement error handling and retry logic
  - Implement exponential backoff for rate limiting errors
  - Implement token refresh error handling with re-authentication prompt
  - Implement logging for all errors with detailed information
  - Implement user-friendly error messages
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_


- [ ]* 12.1 Write property test for retry backoff
  - **Property 21: Retry backoff increases delays**
  - **Validates: Requirements 10.2**

- [ ]* 12.2 Write property test for error logging
  - **Property 22: Errors produce logs and user messages**
  - **Validates: Requirements 10.5**

- [ ] 13. Implement Web Server with Flask
  - Create Flask application with routes for digest, OAuth callback, API endpoints
  - Implement GET / endpoint to serve digest homepage
  - Implement GET /oauth2callback endpoint to handle OAuth redirect
  - Implement GET /api/summaries endpoint to list summaries as JSON
  - Implement GET /api/summaries/:id endpoint to get single summary
  - Implement POST /api/summaries/:id/feedback endpoint to submit feedback
  - Implement POST /api/process endpoint to trigger email processing
  - Implement POST /api/authorize endpoint to initiate OAuth flow
  - Implement DELETE /api/data endpoint to erase all data
  - Implement GET /config and POST /api/config endpoints for configuration management
  - _Requirements: 1.1, 1.2, 6.4, 7.1, 7.5, 8.5_

- [ ] 14. Implement Digest UI (HTML/CSS/JavaScript)
  - Create HTML template for digest homepage with list of summaries
  - Implement summary card display with sender, subject, summary preview
  - Implement expandable detail view with full summary, actions as bullets, deadlines


  - Implement feedback buttons (thumbs up/down) for each summary
  - Implement filters for date, sender, has-actions, has-deadlines
  - Implement dry-run mode toggle indicator
  - Implement "Process Now" button
  - Add settings panel for configuration
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 9.5_



- [ ]* 14.1 Write property test for digest display completeness
  - **Property 15: Digest displays all summaries**
  - **Validates: Requirements 7.1**



- [ ]* 14.2 Write property test for summary display fields
  - **Property 16: Summary display completeness**
  - **Validates: Requirements 7.2**

- [ ]* 14.3 Write property test for email links
  - **Property 17: Email links are valid**
  - **Validates: Requirements 7.3**

- [ ]* 14.4 Write property test for feedback UI elements
  - **Property 18: Feedback UI presence**
  - **Validates: Requirements 7.4**

- [ ] 15. Implement CLI and setup wizard
  - Create CLI entry point with commands: setup, serve, process, erase
  - Implement setup wizard that prompts for email provider, OAuth credentials, summarizer choice, API key
  - Implement serve command to start web server
  - Implement process command to run email processing from CLI
  - Implement erase command to delete all data
  - _Requirements: 2.1, 8.5_

- [ ] 16. Implement privacy and consent features
  - Add consent prompt for remote LLM usage before first use
  - Store consent flag in config
  - Display warning in UI when remote LLM is configured
  - Implement log rotation based on configured days
  - _Requirements: 8.3, 8.4_

- [ ] 17. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 18. Create integration tests
  - Write integration test for OAuth flow with mock provider
  - Write integration test for full email processing pipeline
  - Write integration test for web interface endpoints
  - Write integration test for dry-run mode
  - Write integration test for error recovery scenarios

- [ ]* 19. Create documentation
  - Write README.md with installation instructions, usage guide, and configuration reference
  - Write SECURITY.md with security considerations and threat model
  - Write example config.yaml with comments
  - Create user guide for OAuth setup with Gmail and Outlook
