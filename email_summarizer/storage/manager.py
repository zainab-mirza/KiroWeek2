"""Storage management for email summaries."""

import json
import logging
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from email_summarizer.crypto import get_encryption_manager
from email_summarizer.models import EmailSummary, Feedback, StorageConfig

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages storage and retrieval of email summaries."""

    def __init__(self, config: StorageConfig):
        """Initialize storage manager.

        Args:
            config: Storage configuration
        """
        self.config = config
        self.summaries_dir = Path(config.summaries_dir)
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = (
            self.summaries_dir / "index.db" if config.use_sqlite_index else None
        )

        if self.db_path:
            self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database for indexing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                message_id TEXT PRIMARY KEY,
                sender TEXT,
                subject TEXT,
                received_at TEXT,
                created_at TEXT,
                file_path TEXT,
                has_actions INTEGER,
                has_deadlines INTEGER
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                message_id TEXT PRIMARY KEY,
                rating INTEGER,
                comment TEXT,
                created_at TEXT,
                FOREIGN KEY (message_id) REFERENCES summaries(message_id)
            )
        """
        )

        conn.commit()
        conn.close()

    def save_summary(self, summary: EmailSummary) -> None:
        """Save email summary to storage.

        Args:
            summary: EmailSummary to save
        """
        # Generate filename
        date_str = summary.received_at.strftime("%Y-%m-%d")
        filename = f"{date_str}_{summary.message_id}.json"
        file_path = self.summaries_dir / filename

        # Convert to dict
        data = self._summary_to_dict(summary)

        # Save JSON file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved summary for {summary.message_id} to {file_path}")

        # Update index if enabled
        if self.db_path:
            self._index_summary(summary, str(file_path))

    def get_summary(self, message_id: str) -> Optional[EmailSummary]:
        """Retrieve summary by message ID.

        Args:
            message_id: Message ID

        Returns:
            EmailSummary or None if not found
        """
        # Try to find via index first
        if self.db_path:
            file_path = self._get_file_path_from_index(message_id)
            if file_path:
                return self._load_summary_from_file(Path(file_path))

        # Fall back to scanning directory
        for file_path in self.summaries_dir.glob("*.json"):
            if message_id in file_path.name:
                return self._load_summary_from_file(file_path)

        return None

    def list_summaries(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[EmailSummary]:
        """List all summaries.

        Args:
            limit: Maximum number of summaries to return
            offset: Number of summaries to skip

        Returns:
            List of EmailSummary objects
        """
        summaries = []

        # Get all JSON files
        json_files = sorted(
            self.summaries_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Apply offset and limit
        if offset:
            json_files = json_files[offset:]
        if limit:
            json_files = json_files[:limit]

        # Load summaries
        for file_path in json_files:
            try:
                summary = self._load_summary_from_file(file_path)
                if summary:
                    summaries.append(summary)
            except Exception as e:
                logger.error(f"Error loading summary from {file_path}: {e}")
                continue

        return summaries

    def delete_summary(self, message_id: str) -> None:
        """Delete summary by message ID.

        Args:
            message_id: Message ID
        """
        # Find and delete file
        for file_path in self.summaries_dir.glob("*.json"):
            if message_id in file_path.name:
                file_path.unlink()
                logger.info(f"Deleted summary {message_id}")
                break

        # Remove from index
        if self.db_path:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM summaries WHERE message_id = ?", (message_id,))
            cursor.execute("DELETE FROM feedback WHERE message_id = ?", (message_id,))
            conn.commit()
            conn.close()

    def delete_all(self) -> None:
        """Delete all summaries and feedback."""
        # Delete all JSON files
        for file_path in self.summaries_dir.glob("*.json"):
            file_path.unlink()

        # Clear database
        if self.db_path:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM summaries")
            cursor.execute("DELETE FROM feedback")
            conn.commit()
            conn.close()

        logger.info("Deleted all summaries")

    def save_feedback(self, message_id: str, feedback: Feedback) -> None:
        """Save feedback for a summary.

        Args:
            message_id: Message ID
            feedback: Feedback object
        """
        # Update summary file
        summary = self.get_summary(message_id)
        if summary:
            summary.feedback = feedback
            self.save_summary(summary)

        # Update database
        if self.db_path:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO feedback (message_id, rating, comment, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    message_id,
                    feedback.rating,
                    feedback.comment,
                    feedback.created_at.isoformat(),
                ),
            )

            conn.commit()
            conn.close()

        logger.info(f"Saved feedback for {message_id}")

    def _summary_to_dict(self, summary: EmailSummary) -> dict:
        """Convert EmailSummary to dictionary.

        Args:
            summary: EmailSummary object

        Returns:
            Dictionary representation
        """
        data = {
            "message_id": summary.message_id,
            "sender": summary.sender,
            "subject": summary.subject,
            "received_at": summary.received_at.isoformat(),
            "summary": summary.summary,
            "actions": summary.actions,
            "deadlines": [d.isoformat() for d in summary.deadlines],
            "created_at": summary.created_at.isoformat(),
            "model_used": summary.model_used,
        }

        if summary.feedback:
            data["feedback"] = {
                "rating": summary.feedback.rating,
                "comment": summary.feedback.comment,
                "created_at": summary.feedback.created_at.isoformat(),
            }

        return data

    def _dict_to_summary(self, data: dict) -> EmailSummary:
        """Convert dictionary to EmailSummary.

        Args:
            data: Dictionary representation

        Returns:
            EmailSummary object
        """
        feedback = None
        if "feedback" in data and data["feedback"]:
            feedback = Feedback(
                rating=data["feedback"]["rating"],
                comment=data["feedback"].get("comment"),
                created_at=datetime.fromisoformat(data["feedback"]["created_at"]),
            )

        return EmailSummary(
            message_id=data["message_id"],
            sender=data["sender"],
            subject=data["subject"],
            received_at=datetime.fromisoformat(data["received_at"]),
            summary=data["summary"],
            actions=data["actions"],
            deadlines=[date.fromisoformat(d) for d in data["deadlines"]],
            created_at=datetime.fromisoformat(data["created_at"]),
            model_used=data["model_used"],
            feedback=feedback,
        )

    def _load_summary_from_file(self, file_path: Path) -> Optional[EmailSummary]:
        """Load summary from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            EmailSummary or None if error
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return self._dict_to_summary(data)
        except Exception as e:
            logger.error(f"Error loading summary from {file_path}: {e}")
            return None

    def _index_summary(self, summary: EmailSummary, file_path: str) -> None:
        """Add summary to database index.

        Args:
            summary: EmailSummary object
            file_path: Path to JSON file
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO summaries 
            (message_id, sender, subject, received_at, created_at, file_path, has_actions, has_deadlines)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                summary.message_id,
                summary.sender,
                summary.subject,
                summary.received_at.isoformat(),
                summary.created_at.isoformat(),
                file_path,
                1 if summary.actions else 0,
                1 if summary.deadlines else 0,
            ),
        )

        conn.commit()
        conn.close()

    def _get_file_path_from_index(self, message_id: str) -> Optional[str]:
        """Get file path from database index.

        Args:
            message_id: Message ID

        Returns:
            File path or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT file_path FROM summaries WHERE message_id = ?", (message_id,)
        )
        result = cursor.fetchone()

        conn.close()

        return result[0] if result else None
