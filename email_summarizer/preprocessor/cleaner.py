"""Email preprocessing and cleaning."""

import logging
import re

from bs4 import BeautifulSoup

from email_summarizer.models import CleanedEmail, RawEmail

logger = logging.getLogger(__name__)


class EmailPreprocessor:
    """Cleans and normalizes email content."""

    # Common signature delimiters
    SIGNATURE_PATTERNS = [
        r"--\s*$",  # Double dash
        r"^--\s*\n",
        r"Sent from my",
        r"Get Outlook for",
        r"^Regards,?\s*$",
        r"^Best regards,?\s*$",
        r"^Thanks,?\s*$",
        r"^Thank you,?\s*$",
        r"^Sincerely,?\s*$",
        r"^Cheers,?\s*$",
        r"^Best,?\s*$",
    ]

    # Quote reply patterns
    QUOTE_PATTERNS = [
        r"^On .+ wrote:",  # "On Mon, Jan 1, 2024 at 10:00 AM, John wrote:"
        r"^From:.+Sent:.+To:.+Subject:",  # Outlook-style quote header
        r"^\d{4}-\d{2}-\d{2}.+<.+@.+>:",  # Date + email format
    ]

    def clean_email(self, raw_email: RawEmail) -> CleanedEmail:
        """Clean and preprocess raw email.

        Args:
            raw_email: Raw email from provider

        Returns:
            CleanedEmail object
        """
        # Use HTML body if available, otherwise text
        body = raw_email.body_html if raw_email.body_html else raw_email.body_text
        original_length = len(body)

        # Convert HTML to text
        if raw_email.body_html:
            body = self.html_to_text(raw_email.body_html)

        # Remove quoted replies
        body = self.remove_quoted_replies(body)

        # Remove signature
        body = self.remove_signature(body)

        # Extract main content (normalize whitespace)
        body = self.extract_main_content(body)

        cleaned_length = len(body)

        # Handle empty body
        if not body.strip():
            logger.warning(
                f"Email {raw_email.message_id} has empty body after cleaning"
            )
            body = "[Empty email body]"

        # Extract attachment filenames
        attachment_names = [att.filename for att in raw_email.attachments]

        return CleanedEmail(
            message_id=raw_email.message_id,
            sender=raw_email.sender,
            subject=raw_email.subject,
            received_at=raw_email.received_at,
            cleaned_body=body,
            attachments=attachment_names,
            original_length=original_length,
            cleaned_length=cleaned_length,
        )

    def html_to_text(self, html: str) -> str:
        """Convert HTML to plain text while preserving structure.

        Args:
            html: HTML content

        Returns:
            Plain text with preserved paragraphs
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, "lxml")

            # Remove script and style elements
            for element in soup(["script", "style", "head", "meta"]):
                element.decompose()

            # Get text
            text = soup.get_text(separator="\n")

            return text
        except Exception as e:
            logger.error(f"Error converting HTML to text: {e}")
            return html

    def remove_quoted_replies(self, text: str) -> str:
        """Remove quoted reply sections.

        Args:
            text: Email text

        Returns:
            Text without quoted replies
        """
        lines = text.split("\n")
        cleaned_lines = []
        in_quote = False

        for line in lines:
            # Check for quote header patterns
            is_quote_header = any(
                re.search(pattern, line, re.IGNORECASE | re.MULTILINE)
                for pattern in self.QUOTE_PATTERNS
            )

            if is_quote_header:
                in_quote = True
                continue

            # Check for lines starting with >
            if line.strip().startswith(">"):
                continue

            # If we hit a non-quoted line after being in a quote, we're out
            if in_quote and line.strip() and not line.strip().startswith(">"):
                # Check if it's still part of the quote (indented or short)
                if len(line.strip()) < 5 or line.startswith("    "):
                    continue
                else:
                    in_quote = False

            if not in_quote:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def remove_signature(self, text: str) -> str:
        """Remove email signature blocks.

        Args:
            text: Email text

        Returns:
            Text without signature
        """
        lines = text.split("\n")

        # Find signature start
        signature_start = None

        for i, line in enumerate(lines):
            # Check for signature patterns
            for pattern in self.SIGNATURE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE | re.MULTILINE):
                    signature_start = i
                    break

            if signature_start is not None:
                break

            # Check for contact info patterns (phone, email in signature)
            if i > len(lines) * 0.6:  # Only check last 40% of email
                # Look for phone numbers
                if re.search(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", line):
                    # Check if next few lines also look like contact info
                    next_lines = lines[i : i + 3]
                    contact_indicators = sum(
                        1
                        for l in next_lines
                        if re.search(
                            r"@|www\.|http|phone|mobile|office", l, re.IGNORECASE
                        )
                    )
                    if contact_indicators >= 2:
                        signature_start = i
                        break

        if signature_start is not None:
            return "\n".join(lines[:signature_start])

        return text

    def extract_main_content(self, text: str) -> str:
        """Normalize whitespace and extract main content.

        Args:
            text: Email text

        Returns:
            Normalized text
        """
        # Collapse multiple newlines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]

        # Remove empty lines at start and end
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()

        # Join back
        text = "\n".join(lines)

        # Trim overall
        text = text.strip()

        return text
