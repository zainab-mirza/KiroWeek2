"""OAuth authentication module."""

from .authenticator import (
    OAuthAuthenticator,
    GmailAuthenticator,
    OutlookAuthenticator,
    create_authenticator,
)

__all__ = [
    "OAuthAuthenticator",
    "GmailAuthenticator",
    "OutlookAuthenticator",
    "create_authenticator",
]
