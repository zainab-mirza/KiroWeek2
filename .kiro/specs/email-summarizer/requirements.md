# Requirements Document

## Introduction

The Email Summarizer is a local application that connects to email providers (Gmail or Outlook) via OAuth, fetches emails, cleans their content, generates AI-powered summaries with actionable insights, and presents them through a local web interface. The system prioritizes user privacy by operating locally, encrypting sensitive data, and providing read-only access by default.

## Glossary

- **Email Summarizer**: The local application system that fetches, processes, and summarizes emails
- **OAuth Client**: The registered application credentials used to authenticate with email providers
- **Cleaned Email Body**: Email content with HTML stripped, signatures removed, and quoted replies eliminated
- **Summarizer Engine**: The AI component (local model or remote LLM) that generates email summaries
- **Digest**: A web-based view displaying summarized emails with metadata and actions
- **Dry-Run Mode**: A preview mode that fetches and processes emails without persisting data or modifying mailbox state
- **Refresh Token**: An encrypted credential stored locally that allows the application to access email without repeated user authentication
- **Action Item**: A specific task or next step extracted from an email
- **Deadline**: A date extracted from an email indicating when something is due

## Requirements

### Requirement 1: OAuth Authentication

**User Story:** As a user, I want to securely authenticate with my email provider using OAuth, so that the application can access my emails without storing my password.

#### Acceptance Criteria

1. WHEN the user initiates authentication, THE Email Summarizer SHALL open a browser window directing the user to the email provider's OAuth consent page
2. WHEN the user grants read-only access, THE Email Summarizer SHALL receive an authorization code via the configured redirect URI
3. WHEN an authorization code is received, THE Email Summarizer SHALL exchange it for a refresh token and store the token in encrypted form locally
4. WHEN the refresh token expires or is revoked, THE Email Summarizer SHALL prompt the user to re-authenticate
5. WHERE the user selects Gmail as the provider, THE Email Summarizer SHALL request the gmail.readonly scope

### Requirement 2: Configuration Management

**User Story:** As a user, I want to configure the application settings locally, so that I can control email provider selection, summarizer choice, and security preferences.

#### Acceptance Criteria

1. WHEN the application starts for the first time, THE Email Summarizer SHALL create a local configuration file with default values
2. THE Email Summarizer SHALL store OAuth client credentials in encrypted form or OS keyring
3. WHEN the user selects a summarizer engine, THE Email Summarizer SHALL persist the choice in the local configuration file
4. WHERE a remote LLM is selected, THE Email Summarizer SHALL store the API key in encrypted form
5. THE Email Summarizer SHALL prevent configuration files containing secrets from being committed to version control systems

### Requirement 3: Email Fetching

**User Story:** As a user, I want to fetch emails based on configurable rules, so that I can control which emails are processed for summarization.

#### Acceptance Criteria

1. WHEN the user initiates a fetch operation, THE Email Summarizer SHALL retrieve emails matching the configured fetch rules from the email provider
2. WHERE the fetch mode is set to unread, THE Email Summarizer SHALL retrieve only unread messages
3. WHERE a maximum message limit is configured, THE Email Summarizer SHALL retrieve no more than the specified number of messages
4. WHEN fetching emails, THE Email Summarizer SHALL extract subject, sender, date, and body content for each message
5. WHERE dry-run mode is enabled, THE Email Summarizer SHALL preview email metadata without persisting email bodies

### Requirement 4: Email Preprocessing

**User Story:** As a user, I want email content to be cleaned and normalized, so that summaries focus on the actual message content without noise.

#### Acceptance Criteria

1. WHEN processing an email body, THE Email Summarizer SHALL convert HTML content to plain text while preserving paragraph structure
2. WHEN processing an email body, THE Email Summarizer SHALL remove quoted reply sections identified by lines starting with greater-than symbols or reply headers
3. WHEN processing an email body, THE Email Summarizer SHALL remove signature blocks identified by common delimiters or contact information patterns
4. WHEN processing an email with attachments, THE Email Summarizer SHALL extract and preserve attachment filenames as metadata
5. WHEN cleaning produces an empty body, THE Email Summarizer SHALL handle the condition gracefully and log a warning

### Requirement 5: Summarization

**User Story:** As a user, I want emails to be automatically summarized with extracted actions and deadlines, so that I can quickly understand what requires my attention.

#### Acceptance Criteria

1. WHEN a cleaned email is ready for summarization, THE Email Summarizer SHALL send the content to the configured summarizer engine with a structured prompt
2. WHEN the summarizer engine returns a response, THE Email Summarizer SHALL parse the output as JSON containing summary, actions, and deadlines fields
3. WHERE the summarizer engine is a remote LLM, THE Email Summarizer SHALL include the API key in the request and handle rate limiting errors
4. WHERE the summarizer engine is a local model, THE Email Summarizer SHALL truncate input to the model's maximum token limit
5. WHEN JSON parsing fails, THE Email Summarizer SHALL retry the summarization request with an instruction to fix the JSON format

### Requirement 6: Data Storage

**User Story:** As a user, I want email summaries and metadata stored locally in a secure manner, so that I can review them later while maintaining privacy.

#### Acceptance Criteria

1. WHEN a summary is generated, THE Email Summarizer SHALL save a JSON file containing message_id, sender, subject, received_at, summary, actions, deadlines, and created_at
2. WHERE raw email bodies are stored, THE Email Summarizer SHALL encrypt them before writing to disk
3. THE Email Summarizer SHALL organize summary files in a dedicated local directory with consistent naming conventions
4. WHEN the user requests data deletion, THE Email Summarizer SHALL remove all stored summaries, tokens, and cached email content
5. THE Email Summarizer SHALL maintain a local database or file index to enable efficient retrieval of summaries

### Requirement 7: Web Digest Interface

**User Story:** As a user, I want to view summarized emails in a local web interface, so that I can quickly scan my email digest and take action.

#### Acceptance Criteria

1. WHEN the user accesses the digest URL, THE Email Summarizer SHALL serve a web page displaying all processed email summaries
2. WHEN displaying a summary, THE Email Summarizer SHALL show sender, subject, summary text, action items as bullets, and extracted deadlines
3. WHEN the user clicks on an email in the digest, THE Email Summarizer SHALL provide a link to open the original message in the email client
4. WHERE feedback is enabled, THE Email Summarizer SHALL display thumbs up and thumbs down buttons for each summary
5. WHEN the user provides feedback, THE Email Summarizer SHALL store the feedback locally associated with the message_id

### Requirement 8: Privacy and Security

**User Story:** As a user, I want my email data to remain private and secure, so that sensitive information is not exposed to unauthorized parties.

#### Acceptance Criteria

1. THE Email Summarizer SHALL request only read-only email access scopes by default
2. THE Email Summarizer SHALL encrypt all OAuth refresh tokens before storing them locally
3. WHERE a remote LLM is configured, THE Email Summarizer SHALL require explicit user consent before sending email content to the third-party service
4. THE Email Summarizer SHALL store application logs locally and rotate them to prevent unbounded disk usage
5. THE Email Summarizer SHALL provide a mechanism to erase all stored data including summaries, tokens, and logs

### Requirement 9: Dry-Run Mode

**User Story:** As a user, I want to preview what the application will do without making changes, so that I can verify behavior before committing to operations.

#### Acceptance Criteria

1. WHERE dry-run mode is enabled, THE Email Summarizer SHALL fetch and display email metadata without persisting summaries
2. WHERE dry-run mode is enabled, THE Email Summarizer SHALL preview cleaned email bodies without sending them to the summarizer engine
3. WHEN dry-run mode completes, THE Email Summarizer SHALL display a summary of what would have been processed
4. WHERE dry-run mode is enabled, THE Email Summarizer SHALL not modify any mailbox state or labels
5. THE Email Summarizer SHALL clearly indicate in the user interface when dry-run mode is active

### Requirement 10: Error Handling and Resilience

**User Story:** As a user, I want the application to handle errors gracefully, so that temporary failures do not result in data loss or require manual intervention.

#### Acceptance Criteria

1. WHEN an OAuth token refresh fails, THE Email Summarizer SHALL prompt the user to re-authenticate rather than crashing
2. WHEN the email provider API returns a rate limit error, THE Email Summarizer SHALL wait and retry the request with exponential backoff
3. WHEN the summarizer engine is unavailable, THE Email Summarizer SHALL queue emails for later processing and notify the user
4. WHEN network connectivity is lost, THE Email Summarizer SHALL cache partial results and resume processing when connectivity is restored
5. WHEN an unexpected error occurs, THE Email Summarizer SHALL log detailed error information and display a user-friendly error message
