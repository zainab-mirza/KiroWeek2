"""Email fetching module."""

from .email_fetcher import EmailFetcher, GmailFetcher, OutlookFetcher, create_fetcher

__all__ = ['EmailFetcher', 'GmailFetcher', 'OutlookFetcher', 'create_fetcher']
