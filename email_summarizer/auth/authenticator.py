"""OAuth authentication for email providers."""

import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as GoogleCredentials
from msal import ConfidentialClientApplication
from email_summarizer.models import Credentials, OAuthConfig
from email_summarizer.crypto import get_encryption_manager


class OAuthAuthenticator(ABC):
    """Base class for OAuth authentication."""
    
    def __init__(self, config: OAuthConfig, token_file: Path):
        """Initialize authenticator.
        
        Args:
            config: OAuth configuration
            token_file: Path to store encrypted tokens
        """
        self.config = config
        self.token_file = token_file
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def get_authorization_url(self) -> str:
        """Get OAuth authorization URL.
        
        Returns:
            Authorization URL for user to visit
        """
        pass
    
    @abstractmethod
    def handle_callback(self, code: str) -> Credentials:
        """Handle OAuth callback and exchange code for tokens.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Credentials object
        """
        pass
    
    @abstractmethod
    def refresh_token(self, credentials: Credentials) -> Credentials:
        """Refresh access token using refresh token.
        
        Args:
            credentials: Current credentials
            
        Returns:
            Updated credentials
        """
        pass
    
    def is_token_valid(self, credentials: Credentials) -> bool:
        """Check if token is still valid.
        
        Args:
            credentials: Credentials to check
            
        Returns:
            True if valid, False otherwise
        """
        return not credentials.is_expired()
    
    def save_credentials(self, credentials: Credentials) -> None:
        """Save credentials to encrypted file.
        
        Args:
            credentials: Credentials to save
        """
        # Serialize credentials
        data = {
            'provider': credentials.provider,
            'access_token': credentials.access_token,
            'refresh_token': credentials.refresh_token,
            'expiry': credentials.expiry.isoformat(),
            'scopes': credentials.scopes
        }
        json_data = json.dumps(data)
        
        # Encrypt and save
        encryption_manager = get_encryption_manager()
        encrypted_data = encryption_manager.encrypt(json_data)
        
        with open(self.token_file, 'w') as f:
            f.write(encrypted_data)
    
    def load_credentials(self) -> Optional[Credentials]:
        """Load credentials from encrypted file.
        
        Returns:
            Credentials object or None if file doesn't exist
        """
        if not self.token_file.exists():
            return None
        
        try:
            # Read and decrypt
            with open(self.token_file, 'r') as f:
                encrypted_data = f.read()
            
            encryption_manager = get_encryption_manager()
            json_data = encryption_manager.decrypt(encrypted_data)
            
            # Deserialize
            data = json.loads(json_data)
            return Credentials(
                provider=data['provider'],
                access_token=data['access_token'],
                refresh_token=data['refresh_token'],
                expiry=datetime.fromisoformat(data['expiry']),
                scopes=data['scopes']
            )
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None
    
    def revoke_token(self, credentials: Credentials) -> None:
        """Revoke OAuth token.
        
        Args:
            credentials: Credentials to revoke
        """
        # Delete token file
        if self.token_file.exists():
            self.token_file.unlink()


class GmailAuthenticator(OAuthAuthenticator):
    """Gmail OAuth authenticator."""
    
    def __init__(self, config: OAuthConfig, client_id: str, client_secret: str, 
                 token_file: Path):
        """Initialize Gmail authenticator.
        
        Args:
            config: OAuth configuration
            client_id: OAuth client ID
            client_secret: OAuth client secret
            token_file: Path to store tokens
        """
        super().__init__(config, token_file)
        self.client_id = client_id
        self.client_secret = client_secret
        self._flow: Optional[Flow] = None
    
    def _get_flow(self) -> Flow:
        """Get or create OAuth flow.
        
        Returns:
            Google OAuth flow
        """
        if self._flow is None:
            client_config = {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.config.redirect_uri]
                }
            }
            
            self._flow = Flow.from_client_config(
                client_config,
                scopes=self.config.scopes,
                redirect_uri=self.config.redirect_uri
            )
        
        return self._flow
    
    def get_authorization_url(self) -> str:
        """Get Gmail OAuth authorization URL.
        
        Returns:
            Authorization URL
        """
        flow = self._get_flow()
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url
    
    def handle_callback(self, code: str) -> Credentials:
        """Handle OAuth callback for Gmail.
        
        Args:
            code: Authorization code
            
        Returns:
            Credentials object
        """
        flow = self._get_flow()
        flow.fetch_token(code=code)
        
        google_creds = flow.credentials
        
        credentials = Credentials(
            provider='gmail',
            access_token=google_creds.token,
            refresh_token=google_creds.refresh_token,
            expiry=google_creds.expiry,
            scopes=google_creds.scopes
        )
        
        self.save_credentials(credentials)
        return credentials
    
    def refresh_token(self, credentials: Credentials) -> Credentials:
        """Refresh Gmail access token.
        
        Args:
            credentials: Current credentials
            
        Returns:
            Updated credentials
        """
        google_creds = GoogleCredentials(
            token=credentials.access_token,
            refresh_token=credentials.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=credentials.scopes
        )
        
        google_creds.refresh(Request())
        
        updated_credentials = Credentials(
            provider='gmail',
            access_token=google_creds.token,
            refresh_token=google_creds.refresh_token,
            expiry=google_creds.expiry,
            scopes=google_creds.scopes
        )
        
        self.save_credentials(updated_credentials)
        return updated_credentials


class OutlookAuthenticator(OAuthAuthenticator):
    """Outlook/Office365 OAuth authenticator."""
    
    AUTHORITY = "https://login.microsoftonline.com/common"
    
    def __init__(self, config: OAuthConfig, client_id: str, client_secret: str,
                 token_file: Path):
        """Initialize Outlook authenticator.
        
        Args:
            config: OAuth configuration
            client_id: OAuth client ID
            client_secret: OAuth client secret
            token_file: Path to store tokens
        """
        super().__init__(config, token_file)
        self.client_id = client_id
        self.client_secret = client_secret
        self._app: Optional[ConfidentialClientApplication] = None
    
    def _get_app(self) -> ConfidentialClientApplication:
        """Get or create MSAL application.
        
        Returns:
            MSAL application
        """
        if self._app is None:
            self._app = ConfidentialClientApplication(
                self.client_id,
                authority=self.AUTHORITY,
                client_credential=self.client_secret
            )
        return self._app
    
    def get_authorization_url(self) -> str:
        """Get Outlook OAuth authorization URL.
        
        Returns:
            Authorization URL
        """
        app = self._get_app()
        auth_url = app.get_authorization_request_url(
            scopes=self.config.scopes,
            redirect_uri=self.config.redirect_uri
        )
        return auth_url
    
    def handle_callback(self, code: str) -> Credentials:
        """Handle OAuth callback for Outlook.
        
        Args:
            code: Authorization code
            
        Returns:
            Credentials object
        """
        app = self._get_app()
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=self.config.scopes,
            redirect_uri=self.config.redirect_uri
        )
        
        if "error" in result:
            raise ValueError(f"OAuth error: {result.get('error_description', result['error'])}")
        
        # Calculate expiry
        expires_in = result.get('expires_in', 3600)
        expiry = datetime.now() + timedelta(seconds=expires_in)
        
        credentials = Credentials(
            provider='outlook',
            access_token=result['access_token'],
            refresh_token=result.get('refresh_token', ''),
            expiry=expiry,
            scopes=self.config.scopes
        )
        
        self.save_credentials(credentials)
        return credentials
    
    def refresh_token(self, credentials: Credentials) -> Credentials:
        """Refresh Outlook access token.
        
        Args:
            credentials: Current credentials
            
        Returns:
            Updated credentials
        """
        app = self._get_app()
        result = app.acquire_token_by_refresh_token(
            credentials.refresh_token,
            scopes=self.config.scopes
        )
        
        if "error" in result:
            raise ValueError(f"Token refresh error: {result.get('error_description', result['error'])}")
        
        # Calculate expiry
        expires_in = result.get('expires_in', 3600)
        expiry = datetime.now() + timedelta(seconds=expires_in)
        
        updated_credentials = Credentials(
            provider='outlook',
            access_token=result['access_token'],
            refresh_token=result.get('refresh_token', credentials.refresh_token),
            expiry=expiry,
            scopes=credentials.scopes
        )
        
        self.save_credentials(updated_credentials)
        return updated_credentials


def create_authenticator(provider: str, config: OAuthConfig, 
                        client_id: str, client_secret: str,
                        token_file: Path) -> OAuthAuthenticator:
    """Factory function to create appropriate authenticator.
    
    Args:
        provider: Email provider ("gmail" or "outlook")
        config: OAuth configuration
        client_id: OAuth client ID
        client_secret: OAuth client secret
        token_file: Path to store tokens
        
    Returns:
        OAuthAuthenticator instance
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider == "gmail":
        return GmailAuthenticator(config, client_id, client_secret, token_file)
    elif provider == "outlook":
        return OutlookAuthenticator(config, client_id, client_secret, token_file)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
