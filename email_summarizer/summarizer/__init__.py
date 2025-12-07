"""Email summarization engine module."""

from .engine import (
    SummarizerEngine,
    RemoteSummarizer,
    LocalSummarizer,
    create_summarizer,
)

__all__ = [
    "SummarizerEngine",
    "RemoteSummarizer",
    "LocalSummarizer",
    "create_summarizer",
]
