"""Core data models for the Email Summarizer application."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


class EmailProvider(Enum):
    """Supported email providers."""

    GMAIL = "gmail"
    OUTLOOK = "outlook"


class SummarizerEngine(Enum):
    """Supported summarizer engines."""

    LOCAL = "local"
    REMOTE = "remote"


class FetchMode(Enum):
    """Email fetch modes."""

    UNREAD = "unread"
    LAST_N_DAYS = "last_n_days"
    ALL = "all"


@dataclass
class OAuthConfig:
    """OAuth configuration."""

    client_id_ref: str
    client_secret_ref: str
    redirect_uri: str
    scopes: List[str]

    def validate(self) -> List[str]:
        """Validate OAuth configuration."""
        errors = []
        if not self.client_id_ref:
            errors.append("client_id_ref is required")
        if not self.client_secret_ref:
            errors.append("client_secret_ref is required")
        if not self.redirect_uri:
            errors.append("redirect_uri is required")
        if not self.scopes:
            errors.append("scopes list cannot be empty")
        return errors


@dataclass
class FetchRules:
    """Email fetching rules."""

    mode: str  # "unread", "last_n_days", "all"
    max_messages: int = 20
    days_back: int = 7

    def validate(self) -> List[str]:
        """Validate fetch rules."""
        errors = []
        if self.mode not in ["unread", "last_n_days", "all"]:
            errors.append(f"Invalid fetch mode: {self.mode}")
        if self.max_messages <= 0:
            errors.append("max_messages must be positive")
        if self.days_back <= 0:
            errors.append("days_back must be positive")
        return errors


@dataclass
class SummarizerConfig:
    """Summarizer configuration."""

    engine: str  # "local" or "remote"
    local_model: Optional[str] = None
    remote_provider: Optional[str] = None
    remote_api_key_ref: Optional[str] = None
    max_input_tokens: int = 512

    def validate(self) -> List[str]:
        """Validate summarizer configuration."""
        errors = []
        if self.engine not in ["local", "remote"]:
            errors.append(f"Invalid engine: {self.engine}")
        if self.engine == "local" and not self.local_model:
            errors.append("local_model is required for local engine")
        if self.engine == "remote" and not self.remote_provider:
            errors.append("remote_provider is required for remote engine")
        if self.engine == "remote" and not self.remote_api_key_ref:
            errors.append("remote_api_key_ref is required for remote engine")
        if self.max_input_tokens <= 0:
            errors.append("max_input_tokens must be positive")
        return errors


@dataclass
class ServerConfig:
    """Web server configuration."""

    port: int = 8080
    host: str = "localhost"

    def validate(self) -> List[str]:
        """Validate server configuration."""
        errors = []
        if self.port < 1 or self.port > 65535:
            errors.append("port must be between 1 and 65535")
        if not self.host:
            errors.append("host is required")
        return errors


@dataclass
class StorageConfig:
    """Storage configuration."""

    summaries_dir: str = "./summaries"
    encrypt_bodies: bool = True
    use_sqlite_index: bool = True

    def validate(self) -> List[str]:
        """Validate storage configuration."""
        errors = []
        if not self.summaries_dir:
            errors.append("summaries_dir is required")
        return errors


@dataclass
class PrivacyConfig:
    """Privacy and security configuration."""

    remote_llm_consent: bool = False
    log_rotation_days: int = 7

    def validate(self) -> List[str]:
        """Validate privacy configuration."""
        errors = []
        if self.log_rotation_days <= 0:
            errors.append("log_rotation_days must be positive")
        return errors


@dataclass
class Config:
    """Main application configuration."""

    email_provider: str
    oauth: OAuthConfig
    fetch_rules: FetchRules
    summarizer: SummarizerConfig
    server: ServerConfig
    storage: StorageConfig
    privacy: PrivacyConfig

    def validate(self) -> List[str]:
        """Validate entire configuration."""
        errors = []

        if self.email_provider not in ["gmail", "outlook"]:
            errors.append(f"Invalid email_provider: {self.email_provider}")

        errors.extend(self.oauth.validate())
        errors.extend(self.fetch_rules.validate())
        errors.extend(self.summarizer.validate())
        errors.extend(self.server.validate())
        errors.extend(self.storage.validate())
        errors.extend(self.privacy.validate())

        return errors


@dataclass
class Credentials:
    """OAuth credentials."""

    provider: str
    access_token: str
    refresh_token: str
    expiry: datetime
    scopes: List[str]

    def is_expired(self) -> bool:
        """Check if credentials are expired."""
        return datetime.now() >= self.expiry


@dataclass
class Attachment:
    """Email attachment metadata."""

    filename: str
    size: int
    mime_type: str


@dataclass
class RawEmail:
    """Raw email data from provider."""

    message_id: str
    sender: str
    subject: str
    received_at: datetime
    body_html: str
    body_text: str
    attachments: List[Attachment]
    labels: List[str]

    def validate(self) -> List[str]:
        """Validate raw email has required fields."""
        errors = []
        if not self.message_id:
            errors.append("message_id is required")
        if not self.sender:
            errors.append("sender is required")
        if not self.subject:
            errors.append("subject is required")
        if not self.received_at:
            errors.append("received_at is required")
        if not self.body_html and not self.body_text:
            errors.append("at least one of body_html or body_text is required")
        return errors


@dataclass
class CleanedEmail:
    """Cleaned and preprocessed email."""

    message_id: str
    sender: str
    subject: str
    received_at: datetime
    cleaned_body: str
    attachments: List[str]  # filenames only
    original_length: int
    cleaned_length: int

    def validate(self) -> List[str]:
        """Validate cleaned email."""
        errors = []
        if not self.message_id:
            errors.append("message_id is required")
        if not self.sender:
            errors.append("sender is required")
        if not self.subject:
            errors.append("subject is required")
        if not self.received_at:
            errors.append("received_at is required")
        if self.original_length < 0:
            errors.append("original_length cannot be negative")
        if self.cleaned_length < 0:
            errors.append("cleaned_length cannot be negative")
        return errors


@dataclass
class EmailSummary:
    """Email summary with extracted information."""

    message_id: str
    sender: str
    subject: str
    received_at: datetime
    summary: str
    actions: List[str]
    deadlines: List[date]
    created_at: datetime
    model_used: str
    feedback: Optional["Feedback"] = None

    def validate(self) -> List[str]:
        """Validate email summary."""
        errors = []
        if not self.message_id:
            errors.append("message_id is required")
        if not self.sender:
            errors.append("sender is required")
        if not self.subject:
            errors.append("subject is required")
        if not self.received_at:
            errors.append("received_at is required")
        if not self.summary:
            errors.append("summary is required")
        if not self.created_at:
            errors.append("created_at is required")
        if not self.model_used:
            errors.append("model_used is required")
        return errors


@dataclass
class Feedback:
    """User feedback on a summary."""

    rating: int  # 1 for thumbs up, -1 for thumbs down
    comment: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> List[str]:
        """Validate feedback."""
        errors = []
        if self.rating not in [1, -1]:
            errors.append("rating must be 1 (thumbs up) or -1 (thumbs down)")
        if not self.created_at:
            errors.append("created_at is required")
        return errors


@dataclass
class ProcessingError:
    """Error that occurred during processing."""

    message_id: Optional[str]
    error_type: str
    error_message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingResult:
    """Result of email processing operation."""

    total_fetched: int
    total_processed: int
    total_failed: int
    dry_run: bool
    errors: List[ProcessingError] = field(default_factory=list)

    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_fetched == 0:
            return 0.0
        return self.total_processed / self.total_fetched
