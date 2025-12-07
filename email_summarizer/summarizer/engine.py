"""Email summarization engines."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional
from email_summarizer.models import CleanedEmail, EmailSummary

logger = logging.getLogger(__name__)


class SummarizerEngine(ABC):
    """Base class for email summarization."""
    
    PROMPT_TEMPLATE = """You are an email summarization assistant. Analyze the following email and produce a JSON object with these keys:
- "summary": 1-3 sentences describing the email's purpose and any requested next steps
- "actions": array of short action strings (what the recipient should do)
- "deadlines": array of ISO date strings (YYYY-MM-DD) or empty array if no deadlines

Email Details:
Subject: {subject}
From: {sender}
Date: {received_at}
Attachments: {attachment_list}

Email Body:
{cleaned_body}

Output only valid JSON. No additional text."""
    
    def __init__(self, max_tokens: int = 512):
        """Initialize summarizer.
        
        Args:
            max_tokens: Maximum input tokens
        """
        self.max_tokens = max_tokens
    
    @abstractmethod
    def summarize(self, email: CleanedEmail) -> EmailSummary:
        """Generate summary for email.
        
        Args:
            email: Cleaned email
            
        Returns:
            EmailSummary object
        """
        pass
    
    def _build_prompt(self, email: CleanedEmail) -> str:
        """Build prompt for summarization.
        
        Args:
            email: Cleaned email
            
        Returns:
            Formatted prompt string
        """
        attachment_list = ", ".join(email.attachments) if email.attachments else "None"
        
        return self.PROMPT_TEMPLATE.format(
            subject=email.subject,
            sender=email.sender,
            received_at=email.received_at.strftime('%Y-%m-%d %H:%M'),
            attachment_list=attachment_list,
            cleaned_body=self._truncate_body(email.cleaned_body)
        )
    
    def _truncate_body(self, body: str) -> str:
        """Truncate body to fit token limit.
        
        Args:
            body: Email body
            
        Returns:
            Truncated body
        """
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = self.max_tokens * 4
        
        if len(body) <= max_chars:
            return body
        
        # Truncate and add indicator
        truncated = body[:max_chars]
        # Try to cut at sentence boundary
        last_period = truncated.rfind('.')
        if last_period > max_chars * 0.8:
            truncated = truncated[:last_period + 1]
        
        return truncated + "\n\n[Email truncated...]"
    
    def _parse_response(self, response_text: str, email: CleanedEmail) -> EmailSummary:
        """Parse JSON response into EmailSummary.
        
        Args:
            response_text: JSON response from model
            email: Original cleaned email
            
        Returns:
            EmailSummary object
            
        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Try to extract JSON from response
            # Sometimes models add extra text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            if 'summary' not in data:
                raise ValueError("Missing 'summary' field")
            if 'actions' not in data:
                data['actions'] = []
            if 'deadlines' not in data:
                data['deadlines'] = []
            
            # Parse deadlines
            deadlines = []
            for deadline_str in data['deadlines']:
                try:
                    deadline = date.fromisoformat(deadline_str)
                    deadlines.append(deadline)
                except:
                    logger.warning(f"Invalid deadline format: {deadline_str}")
            
            return EmailSummary(
                message_id=email.message_id,
                sender=email.sender,
                subject=email.subject,
                received_at=email.received_at,
                summary=data['summary'],
                actions=data['actions'],
                deadlines=deadlines,
                created_at=datetime.now(),
                model_used=self._get_model_name()
            )
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")
    
    @abstractmethod
    def _get_model_name(self) -> str:
        """Get model name for tracking."""
        pass


class RemoteSummarizer(SummarizerEngine):
    """Remote LLM-based summarizer (OpenAI, etc.)."""
    
    def __init__(self, provider: str, api_key: str, max_tokens: int = 512):
        """Initialize remote summarizer.
        
        Args:
            provider: LLM provider ("openai", etc.)
            api_key: API key
            max_tokens: Maximum input tokens
        """
        super().__init__(max_tokens)
        self.provider = provider
        self.api_key = api_key
        
        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-3.5-turbo"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def summarize(self, email: CleanedEmail) -> EmailSummary:
        """Generate summary using remote LLM.
        
        Args:
            email: Cleaned email
            
        Returns:
            EmailSummary object
        """
        prompt = self._build_prompt(email)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful email summarization assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            return self._parse_response(response_text, email)
        
        except json.JSONDecodeError:
            # Retry with explicit JSON fix instruction
            logger.warning("JSON parsing failed, retrying with fix instruction")
            return self._retry_with_json_fix(email, response_text)
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            raise
    
    def _retry_with_json_fix(self, email: CleanedEmail, previous_response: str) -> EmailSummary:
        """Retry summarization with JSON fix instruction.
        
        Args:
            email: Cleaned email
            previous_response: Previous failed response
            
        Returns:
            EmailSummary object
        """
        fix_prompt = f"""The previous response was not valid JSON:
{previous_response}

Please provide ONLY a valid JSON object with these exact keys:
- "summary": string (1-3 sentences)
- "actions": array of strings
- "deadlines": array of date strings in YYYY-MM-DD format

No additional text, just the JSON object."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Respond with valid JSON only."},
                    {"role": "user", "content": fix_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            return self._parse_response(response_text, email)
        
        except Exception as e:
            logger.error(f"Retry failed: {e}")
            # Return a basic summary as fallback
            return EmailSummary(
                message_id=email.message_id,
                sender=email.sender,
                subject=email.subject,
                received_at=email.received_at,
                summary=f"Email from {email.sender} regarding: {email.subject}",
                actions=[],
                deadlines=[],
                created_at=datetime.now(),
                model_used=self._get_model_name()
            )
    
    def _get_model_name(self) -> str:
        """Get model name."""
        return f"{self.provider}/{self.model}"


class LocalSummarizer(SummarizerEngine):
    """Local transformer-based summarizer."""
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn", max_tokens: int = 512):
        """Initialize local summarizer.
        
        Args:
            model_name: Hugging Face model name
            max_tokens: Maximum input tokens
        """
        super().__init__(max_tokens)
        self.model_name = model_name
        
        try:
            from transformers import pipeline
            self.summarizer = pipeline("summarization", model=model_name)
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            raise
    
    def summarize(self, email: CleanedEmail) -> EmailSummary:
        """Generate summary using local model.
        
        Args:
            email: Cleaned email
            
        Returns:
            EmailSummary object
        """
        # For local models, we'll use a simpler approach
        # since they typically don't support structured JSON output
        
        input_text = f"Subject: {email.subject}\n\n{self._truncate_body(email.cleaned_body)}"
        
        try:
            result = self.summarizer(
                input_text,
                max_length=150,
                min_length=30,
                do_sample=False
            )
            
            summary_text = result[0]['summary_text']
            
            # Simple action extraction (look for imperative verbs)
            actions = self._extract_actions(email.cleaned_body)
            
            # Simple deadline extraction (look for dates)
            deadlines = self._extract_deadlines(email.cleaned_body)
            
            return EmailSummary(
                message_id=email.message_id,
                sender=email.sender,
                subject=email.subject,
                received_at=email.received_at,
                summary=summary_text,
                actions=actions,
                deadlines=deadlines,
                created_at=datetime.now(),
                model_used=self._get_model_name()
            )
        
        except Exception as e:
            logger.error(f"Local summarization error: {e}")
            raise
    
    def _extract_actions(self, text: str) -> List[str]:
        """Extract potential action items from text.
        
        Args:
            text: Email body
            
        Returns:
            List of action strings
        """
        import re
        
        actions = []
        action_keywords = ['please', 'could you', 'can you', 'need to', 'should', 'must', 'review', 'send', 'update']
        
        sentences = re.split(r'[.!?]\s+', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in action_keywords):
                actions.append(sentence.strip())
        
        return actions[:5]  # Limit to 5 actions
    
    def _extract_deadlines(self, text: str) -> List[date]:
        """Extract potential deadlines from text.
        
        Args:
            text: Email body
            
        Returns:
            List of date objects
        """
        import re
        from dateutil import parser
        
        deadlines = []
        
        # Look for date patterns
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    parsed_date = parser.parse(match).date()
                    if parsed_date not in deadlines and parsed_date >= date.today():
                        deadlines.append(parsed_date)
                except:
                    continue
        
        return sorted(deadlines)[:3]  # Limit to 3 deadlines
    
    def _get_model_name(self) -> str:
        """Get model name."""
        return f"local/{self.model_name}"


def create_summarizer(engine: str, **kwargs) -> SummarizerEngine:
    """Factory function to create appropriate summarizer.
    
    Args:
        engine: Engine type ("local" or "remote")
        **kwargs: Additional arguments for the summarizer
        
    Returns:
        SummarizerEngine instance
        
    Raises:
        ValueError: If engine type is not supported
    """
    if engine == "remote":
        provider = kwargs.get('provider', 'openai')
        api_key = kwargs.get('api_key')
        max_tokens = kwargs.get('max_tokens', 512)
        
        if not api_key:
            raise ValueError("api_key is required for remote summarizer")
        
        return RemoteSummarizer(provider, api_key, max_tokens)
    
    elif engine == "local":
        model_name = kwargs.get('model_name', 'facebook/bart-large-cnn')
        max_tokens = kwargs.get('max_tokens', 512)
        
        return LocalSummarizer(model_name, max_tokens)
    
    else:
        raise ValueError(f"Unsupported engine: {engine}")
