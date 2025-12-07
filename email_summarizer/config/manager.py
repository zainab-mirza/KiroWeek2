"""Configuration management with secure credential storage."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import keyring
import yaml

from email_summarizer.models import (Config, FetchRules, OAuthConfig,
                                     PrivacyConfig, ServerConfig,
                                     StorageConfig, SummarizerConfig)


class ConfigManager:
    """Manages application configuration with secure secret storage."""

    DEFAULT_CONFIG_PATH = Path.home() / ".email-summarizer" / "config.yaml"
    SERVICE_NAME = "email-summarizer"

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config file. Defaults to ~/.email-summarizer/config.yaml
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Config:
        """Load configuration from file.

        Returns:
            Config object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        config = self._dict_to_config(data)

        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        return config

    def save_config(self, config: Config) -> None:
        """Save configuration to file.

        Args:
            config: Config object to save

        Raises:
            ValueError: If config is invalid
        """
        # Validate before saving
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        data = self._config_to_dict(config)

        with open(self.config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_secret(self, key: str) -> str:
        """Retrieve secret from OS keyring.

        Args:
            key: Secret key name

        Returns:
            Secret value

        Raises:
            KeyError: If secret not found
        """
        value = keyring.get_password(self.SERVICE_NAME, key)
        if value is None:
            raise KeyError(f"Secret not found: {key}")
        return value

    def set_secret(self, key: str, value: str) -> None:
        """Store secret in OS keyring.

        Args:
            key: Secret key name
            value: Secret value
        """
        keyring.set_password(self.SERVICE_NAME, key, value)

    def delete_secret(self, key: str) -> None:
        """Delete secret from OS keyring.

        Args:
            key: Secret key name
        """
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
        except keyring.errors.PasswordDeleteError:
            pass  # Secret doesn't exist, that's fine

    def create_default_config(self, email_provider: str = "gmail") -> Config:
        """Create default configuration.

        Args:
            email_provider: Email provider ("gmail" or "outlook")

        Returns:
            Default Config object
        """
        oauth_config = OAuthConfig(
            client_id_ref="keyring:oauth_client_id",
            client_secret_ref="keyring:oauth_client_secret",
            redirect_uri="http://localhost:8080/oauth2callback",
            scopes=["gmail.readonly"] if email_provider == "gmail" else ["Mail.Read"],
        )

        fetch_rules = FetchRules(mode="unread", max_messages=20, days_back=7)

        summarizer_config = SummarizerConfig(
            engine="remote",
            remote_provider="openai",
            remote_api_key_ref="keyring:openai_api_key",
            max_input_tokens=512,
        )

        server_config = ServerConfig(port=8080, host="localhost")

        storage_config = StorageConfig(
            summaries_dir=str(Path.home() / ".email-summarizer" / "summaries"),
            encrypt_bodies=True,
            use_sqlite_index=True,
        )

        privacy_config = PrivacyConfig(remote_llm_consent=False, log_rotation_days=7)

        return Config(
            email_provider=email_provider,
            oauth=oauth_config,
            fetch_rules=fetch_rules,
            summarizer=summarizer_config,
            server=server_config,
            storage=storage_config,
            privacy=privacy_config,
        )

    def _dict_to_config(self, data: Dict[str, Any]) -> Config:
        """Convert dictionary to Config object."""
        oauth = OAuthConfig(**data["oauth"])
        fetch_rules = FetchRules(**data["fetch_rules"])
        summarizer = SummarizerConfig(**data["summarizer"])
        server = ServerConfig(**data["server"])
        storage = StorageConfig(**data["storage"])
        privacy = PrivacyConfig(**data["privacy"])

        return Config(
            email_provider=data["email_provider"],
            oauth=oauth,
            fetch_rules=fetch_rules,
            summarizer=summarizer,
            server=server,
            storage=storage,
            privacy=privacy,
        )

    def _config_to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert Config object to dictionary."""
        return {
            "email_provider": config.email_provider,
            "oauth": {
                "client_id_ref": config.oauth.client_id_ref,
                "client_secret_ref": config.oauth.client_secret_ref,
                "redirect_uri": config.oauth.redirect_uri,
                "scopes": config.oauth.scopes,
            },
            "fetch_rules": {
                "mode": config.fetch_rules.mode,
                "max_messages": config.fetch_rules.max_messages,
                "days_back": config.fetch_rules.days_back,
            },
            "summarizer": {
                "engine": config.summarizer.engine,
                "local_model": config.summarizer.local_model,
                "remote_provider": config.summarizer.remote_provider,
                "remote_api_key_ref": config.summarizer.remote_api_key_ref,
                "max_input_tokens": config.summarizer.max_input_tokens,
            },
            "server": {"port": config.server.port, "host": config.server.host},
            "storage": {
                "summaries_dir": config.storage.summaries_dir,
                "encrypt_bodies": config.storage.encrypt_bodies,
                "use_sqlite_index": config.storage.use_sqlite_index,
            },
            "privacy": {
                "remote_llm_consent": config.privacy.remote_llm_consent,
                "log_rotation_days": config.privacy.log_rotation_days,
            },
        }

    def resolve_secret_ref(self, ref: str) -> str:
        """Resolve a secret reference to its actual value.

        Args:
            ref: Reference string (e.g., "keyring:oauth_client_id")

        Returns:
            Actual secret value

        Raises:
            ValueError: If reference format is invalid
            KeyError: If secret not found
        """
        if not ref.startswith("keyring:"):
            raise ValueError(f"Invalid secret reference format: {ref}")

        key = ref.replace("keyring:", "")
        return self.get_secret(key)
