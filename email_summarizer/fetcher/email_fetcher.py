"""Email fetching from Gmail and Outlook."""

import base64
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List

import requests
from googleapiclient.discovery import build

from email_summarizer.models import (Attachment, Credentials, FetchRules,
                                     RawEmail)


class EmailFetcher(ABC):
    """Base class for email fetching."""

    def __init__(self, credentials: Credentials):
        """Initialize email fetcher.

        Args:
            credentials: OAuth credentials
        """
        self.credentials = credentials

    @abstractmethod
    def fetch_emails(self, rules: FetchRules, dry_run: bool = False) -> List[RawEmail]:
        """Fetch emails based on rules.

        Args:
            rules: Fetch rules
            dry_run: If True, don't persist any data

        Returns:
            List of RawEmail objects
        """
        pass

    @abstractmethod
    def get_email_body(self, message_id: str) -> str:
        """Get full email body.

        Args:
            message_id: Message ID

        Returns:
            Email body as string
        """
        pass

    @abstractmethod
    def get_attachments_metadata(self, message_id: str) -> List[Attachment]:
        """Get attachment metadata.

        Args:
            message_id: Message ID

        Returns:
            List of Attachment objects
        """
        pass


class GmailFetcher(EmailFetcher):
    """Gmail email fetcher."""

    def __init__(self, credentials: Credentials):
        """Initialize Gmail fetcher.

        Args:
            credentials: Gmail OAuth credentials
        """
        super().__init__(credentials)
        self.service = None

    def _get_service(self):
        """Get or create Gmail API service."""
        if self.service is None:
            from google.oauth2.credentials import \
                Credentials as GoogleCredentials

            google_creds = GoogleCredentials(
                token=self.credentials.access_token,
                refresh_token=self.credentials.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=self.credentials.scopes,
            )

            self.service = build("gmail", "v1", credentials=google_creds)

        return self.service

    def fetch_emails(self, rules: FetchRules, dry_run: bool = False) -> List[RawEmail]:
        """Fetch emails from Gmail.

        Args:
            rules: Fetch rules
            dry_run: If True, don't persist any data

        Returns:
            List of RawEmail objects
        """
        service = self._get_service()

        # Build query
        query_parts = []

        if rules.mode == "unread":
            query_parts.append("is:unread")
        elif rules.mode == "last_n_days":
            date_str = (datetime.now() - timedelta(days=rules.days_back)).strftime(
                "%Y/%m/%d"
            )
            query_parts.append(f"after:{date_str}")

        query = " ".join(query_parts) if query_parts else None

        # Fetch message list
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=rules.max_messages)
            .execute()
        )

        messages = results.get("messages", [])

        # Fetch full message details
        emails = []
        for msg in messages[: rules.max_messages]:
            try:
                email = self._fetch_message_details(msg["id"])
                emails.append(email)
            except Exception as e:
                print(f"Error fetching message {msg['id']}: {e}")
                continue

        return emails

    def _fetch_message_details(self, message_id: str) -> RawEmail:
        """Fetch full message details.

        Args:
            message_id: Gmail message ID

        Returns:
            RawEmail object
        """
        service = self._get_service()

        message = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        # Extract headers
        headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}

        sender = headers.get("From", "Unknown")
        subject = headers.get("Subject", "No Subject")
        date_str = headers.get("Date", "")

        # Parse date
        try:
            from email.utils import parsedate_to_datetime

            received_at = parsedate_to_datetime(date_str)
        except:
            received_at = datetime.now()

        # Extract body
        body_html, body_text = self._extract_body(message["payload"])

        # Extract attachments
        attachments = self._extract_attachments(message["payload"])

        # Extract labels
        labels = message.get("labelIds", [])

        return RawEmail(
            message_id=message_id,
            sender=sender,
            subject=subject,
            received_at=received_at,
            body_html=body_html,
            body_text=body_text,
            attachments=attachments,
            labels=labels,
        )

    def _extract_body(self, payload: dict) -> tuple[str, str]:
        """Extract email body from payload.

        Args:
            payload: Gmail message payload

        Returns:
            Tuple of (html_body, text_body)
        """
        html_body = ""
        text_body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")

                if mime_type == "text/plain" and "data" in part.get("body", {}):
                    text_body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
                elif mime_type == "text/html" and "data" in part.get("body", {}):
                    html_body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
                elif "parts" in part:
                    # Recursive for nested parts
                    nested_html, nested_text = self._extract_body(part)
                    if nested_html:
                        html_body = nested_html
                    if nested_text:
                        text_body = nested_text
        elif "body" in payload and "data" in payload["body"]:
            mime_type = payload.get("mimeType", "")
            data = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

            if mime_type == "text/html":
                html_body = data
            else:
                text_body = data

        return html_body, text_body

    def _extract_attachments(self, payload: dict) -> List[Attachment]:
        """Extract attachment metadata from payload.

        Args:
            payload: Gmail message payload

        Returns:
            List of Attachment objects
        """
        attachments = []

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    attachment = Attachment(
                        filename=part["filename"],
                        size=part["body"].get("size", 0),
                        mime_type=part.get("mimeType", "application/octet-stream"),
                    )
                    attachments.append(attachment)

                # Check nested parts
                if "parts" in part:
                    attachments.extend(self._extract_attachments(part))

        return attachments

    def get_email_body(self, message_id: str) -> str:
        """Get full email body.

        Args:
            message_id: Gmail message ID

        Returns:
            Email body as string
        """
        email = self._fetch_message_details(message_id)
        return email.body_html or email.body_text

    def get_attachments_metadata(self, message_id: str) -> List[Attachment]:
        """Get attachment metadata.

        Args:
            message_id: Gmail message ID

        Returns:
            List of Attachment objects
        """
        email = self._fetch_message_details(message_id)
        return email.attachments


class OutlookFetcher(EmailFetcher):
    """Outlook/Office365 email fetcher."""

    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

    def __init__(self, credentials: Credentials):
        """Initialize Outlook fetcher.

        Args:
            credentials: Outlook OAuth credentials
        """
        super().__init__(credentials)

    def _get_headers(self) -> dict:
        """Get authorization headers.

        Returns:
            Headers dict with authorization
        """
        return {
            "Authorization": f"Bearer {self.credentials.access_token}",
            "Content-Type": "application/json",
        }

    def fetch_emails(self, rules: FetchRules, dry_run: bool = False) -> List[RawEmail]:
        """Fetch emails from Outlook.

        Args:
            rules: Fetch rules
            dry_run: If True, don't persist any data

        Returns:
            List of RawEmail objects
        """
        # Build filter
        filters = []

        if rules.mode == "unread":
            filters.append("isRead eq false")
        elif rules.mode == "last_n_days":
            date_str = (datetime.now() - timedelta(days=rules.days_back)).isoformat()
            filters.append(f"receivedDateTime ge {date_str}")

        filter_str = " and ".join(filters) if filters else None

        # Build URL
        url = f"{self.GRAPH_API_ENDPOINT}/me/messages"
        params = {"$top": rules.max_messages, "$orderby": "receivedDateTime desc"}
        if filter_str:
            params["$filter"] = filter_str

        # Fetch messages
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        messages = response.json().get("value", [])

        # Convert to RawEmail objects
        emails = []
        for msg in messages:
            try:
                email = self._convert_message(msg)
                emails.append(email)
            except Exception as e:
                print(f"Error converting message {msg.get('id')}: {e}")
                continue

        return emails

    def _convert_message(self, message: dict) -> RawEmail:
        """Convert Outlook message to RawEmail.

        Args:
            message: Outlook message dict

        Returns:
            RawEmail object
        """
        sender = (
            message.get("from", {}).get("emailAddress", {}).get("address", "Unknown")
        )
        subject = message.get("subject", "No Subject")

        # Parse date
        date_str = message.get("receivedDateTime", "")
        try:
            received_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            received_at = datetime.now()

        # Extract body
        body_content = message.get("body", {})
        body_html = (
            body_content.get("content", "")
            if body_content.get("contentType") == "html"
            else ""
        )
        body_text = (
            body_content.get("content", "")
            if body_content.get("contentType") == "text"
            else ""
        )

        # Extract attachments
        attachments = []
        if message.get("hasAttachments"):
            for att in message.get("attachments", []):
                attachment = Attachment(
                    filename=att.get("name", "unknown"),
                    size=att.get("size", 0),
                    mime_type=att.get("contentType", "application/octet-stream"),
                )
                attachments.append(attachment)

        # Categories as labels
        labels = message.get("categories", [])

        return RawEmail(
            message_id=message["id"],
            sender=sender,
            subject=subject,
            received_at=received_at,
            body_html=body_html,
            body_text=body_text,
            attachments=attachments,
            labels=labels,
        )

    def get_email_body(self, message_id: str) -> str:
        """Get full email body.

        Args:
            message_id: Outlook message ID

        Returns:
            Email body as string
        """
        url = f"{self.GRAPH_API_ENDPOINT}/me/messages/{message_id}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        message = response.json()
        body_content = message.get("body", {})
        return body_content.get("content", "")

    def get_attachments_metadata(self, message_id: str) -> List[Attachment]:
        """Get attachment metadata.

        Args:
            message_id: Outlook message ID

        Returns:
            List of Attachment objects
        """
        url = f"{self.GRAPH_API_ENDPOINT}/me/messages/{message_id}/attachments"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        attachments_data = response.json().get("value", [])

        attachments = []
        for att in attachments_data:
            attachment = Attachment(
                filename=att.get("name", "unknown"),
                size=att.get("size", 0),
                mime_type=att.get("contentType", "application/octet-stream"),
            )
            attachments.append(attachment)

        return attachments


def create_fetcher(provider: str, credentials: Credentials) -> EmailFetcher:
    """Factory function to create appropriate email fetcher.

    Args:
        provider: Email provider ("gmail" or "outlook")
        credentials: OAuth credentials

    Returns:
        EmailFetcher instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider == "gmail":
        return GmailFetcher(credentials)
    elif provider == "outlook":
        return OutlookFetcher(credentials)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
