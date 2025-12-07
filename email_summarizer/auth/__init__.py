"""OAuth authentication module."""

from .authenticator import (GmailAuthenticator, OAuthAuthenticator,
                            OutlookAuthenticator, create_authenticator)

__all__ = [
    "OAuthAuthenticator",
    "GmailAuthenticator",
    "OutlookAuthenticator",
    "create_authenticator",
]
