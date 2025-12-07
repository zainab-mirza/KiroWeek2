"""Email summarization engine module."""

from .engine import (LocalSummarizer, RemoteSummarizer, SummarizerEngine,
                     create_summarizer)

__all__ = [
    "SummarizerEngine",
    "RemoteSummarizer",
    "LocalSummarizer",
    "create_summarizer",
]
