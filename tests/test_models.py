"""Tests for data models."""

import pytest
from datetime import datetime, date
from email_summarizer.models import (
    Config, OAuthConfig, FetchRules, SummarizerConfig,
    ServerConfig, StorageConfig, PrivacyConfig,
    Credentials, RawEmail, CleanedEmail, EmailSummary,
    Feedback, Attachment
)


class TestOAuthConfig:
    """Tests for OAuthConfig model."""
    
    def test_valid_config(self):
        """Test valid OAuth configuration."""
        config = OAuthConfig(
            client_id_ref="keyring:test_id",
            client_secret_ref="keyring:test_secret",
            redirect_uri="http://localhost:8080/callback",
            scopes=["gmail.readonly"]
        )
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_missing_client_id(self):
        """Test validation fails with missing client ID."""
        config = OAuthConfig(
            client_id_ref="",
            client_secret_ref="keyring:test_secret",
            redirect_uri="http://localhost:8080/callback",
            scopes=["gmail.readonly"]
        )
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("client_id_ref" in error for error in errors)
    
    def test_empty_scopes(self):
        """Test validation fails with empty scopes."""
        config = OAuthConfig(
            client_id_ref="keyring:test_id",
            client_secret_ref="keyring:test_secret",
            redirect_uri="http://localhost:8080/callback",
            scopes=[]
        )
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("scopes" in error for error in errors)


class TestFetchRules:
    """Tests for FetchRules model."""
    
    def test_valid_unread_mode(self):
        """Test valid unread fetch mode."""
        rules = FetchRules(mode="unread", max_messages=10)
        errors = rules.validate()
        assert len(errors) == 0
    
    def test_invalid_mode(self):
        """Test validation fails with invalid mode."""
        rules = FetchRules(mode="invalid", max_messages=10)
        errors = rules.validate()
        assert len(errors) > 0
        assert any("mode" in error for error in errors)
    
    def test_negative_max_messages(self):
        """Test validation fails with negative max messages."""
        rules = FetchRules(mode="unread", max_messages=-5)
        errors = rules.validate()
        assert len(errors) > 0
        assert any("max_messages" in error for error in errors)


class TestCredentials:
    """Tests for Credentials model."""
    
    def test_is_expired_future(self):
        """Test token is not expired when expiry is in future."""
        future_time = datetime(2099, 1, 1)
        creds = Credentials(
            provider="gmail",
            access_token="token",
            refresh_token="refresh",
            expiry=future_time,
            scopes=["gmail.readonly"]
        )
        
        assert not creds.is_expired()
    
    def test_is_expired_past(self):
        """Test token is expired when expiry is in past."""
        past_time = datetime(2020, 1, 1)
        creds = Credentials(
            provider="gmail",
            access_token="token",
            refresh_token="refresh",
            expiry=past_time,
            scopes=["gmail.readonly"]
        )
        
        assert creds.is_expired()


class TestEmailSummary:
    """Tests for EmailSummary model."""
    
    def test_valid_summary(self):
        """Test valid email summary."""
        summary = EmailSummary(
            message_id="msg123",
            sender="test@example.com",
            subject="Test Email",
            received_at=datetime.now(),
            summary="This is a test summary",
            actions=["Review document"],
            deadlines=[date.today()],
            created_at=datetime.now(),
            model_used="gpt-3.5-turbo"
        )
        
        errors = summary.validate()
        assert len(errors) == 0
    
    def test_missing_required_fields(self):
        """Test validation fails with missing fields."""
        summary = EmailSummary(
            message_id="",
            sender="",
            subject="",
            received_at=datetime.now(),
            summary="",
            actions=[],
            deadlines=[],
            created_at=datetime.now(),
            model_used=""
        )
        
        errors = summary.validate()
        assert len(errors) > 0


class TestFeedback:
    """Tests for Feedback model."""
    
    def test_valid_thumbs_up(self):
        """Test valid thumbs up feedback."""
        feedback = Feedback(rating=1)
        errors = feedback.validate()
        assert len(errors) == 0
    
    def test_valid_thumbs_down(self):
        """Test valid thumbs down feedback."""
        feedback = Feedback(rating=-1)
        errors = feedback.validate()
        assert len(errors) == 0
    
    def test_invalid_rating(self):
        """Test validation fails with invalid rating."""
        feedback = Feedback(rating=5)
        errors = feedback.validate()
        assert len(errors) > 0
        assert any("rating" in error for error in errors)


if __name__ == "__main__":
    pytest.main([__file__])
