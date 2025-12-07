"""Email processing orchestration."""

import logging
from typing import List
from email_summarizer.models import (
    Config, ProcessingResult, ProcessingError, EmailSummary
)
from email_summarizer.fetcher import EmailFetcher
from email_summarizer.preprocessor import EmailPreprocessor
from email_summarizer.summarizer import SummarizerEngine
from email_summarizer.storage import StorageManager

logger = logging.getLogger(__name__)


class EmailOrchestrator:
    """Coordinates the end-to-end email processing pipeline."""
    
    def __init__(
        self,
        config: Config,
        fetcher: EmailFetcher,
        preprocessor: EmailPreprocessor,
        summarizer: SummarizerEngine,
        storage: StorageManager
    ):
        """Initialize orchestrator.
        
        Args:
            config: Application configuration
            fetcher: Email fetcher instance
            preprocessor: Email preprocessor instance
            summarizer: Summarizer engine instance
            storage: Storage manager instance
        """
        self.config = config
        self.fetcher = fetcher
        self.preprocessor = preprocessor
        self.summarizer = summarizer
        self.storage = storage
    
    def process_emails(self, dry_run: bool = False) -> ProcessingResult:
        """Process emails through the full pipeline.
        
        Args:
            dry_run: If True, don't persist summaries or send to summarizer
            
        Returns:
            ProcessingResult with statistics
        """
        logger.info(f"Starting email processing (dry_run={dry_run})")
        
        errors: List[ProcessingError] = []
        processed_count = 0
        failed_count = 0
        
        try:
            # Fetch emails
            logger.info("Fetching emails...")
            raw_emails = self.fetcher.fetch_emails(
                self.config.fetch_rules,
                dry_run=dry_run
            )
            total_fetched = len(raw_emails)
            logger.info(f"Fetched {total_fetched} emails")
            
            # Process each email
            for raw_email in raw_emails:
                try:
                    # Preprocess
                    logger.debug(f"Preprocessing email {raw_email.message_id}")
                    cleaned_email = self.preprocessor.clean_email(raw_email)
                    
                    if dry_run:
                        # In dry-run, just count as processed
                        logger.info(f"[DRY-RUN] Would process: {cleaned_email.subject}")
                        processed_count += 1
                        continue
                    
                    # Summarize
                    logger.debug(f"Summarizing email {raw_email.message_id}")
                    summary = self.summarizer.summarize(cleaned_email)
                    
                    # Store
                    logger.debug(f"Storing summary for {raw_email.message_id}")
                    self.storage.save_summary(summary)
                    
                    processed_count += 1
                    logger.info(f"Successfully processed email {raw_email.message_id}")
                
                except Exception as e:
                    failed_count += 1
                    error = ProcessingError(
                        message_id=raw_email.message_id,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                    errors.append(error)
                    logger.error(f"Error processing email {raw_email.message_id}: {e}")
            
            result = ProcessingResult(
                total_fetched=total_fetched,
                total_processed=processed_count,
                total_failed=failed_count,
                dry_run=dry_run,
                errors=errors
            )
            
            logger.info(f"Processing complete: {processed_count}/{total_fetched} successful")
            return result
        
        except Exception as e:
            logger.error(f"Fatal error during processing: {e}")
            return ProcessingResult(
                total_fetched=0,
                total_processed=0,
                total_failed=0,
                dry_run=dry_run,
                errors=[ProcessingError(
                    message_id=None,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )]
            )
    
    def process_single_email(self, message_id: str) -> EmailSummary:
        """Process a single email by message ID.
        
        Args:
            message_id: Message ID to process
            
        Returns:
            EmailSummary object
            
        Raises:
            ValueError: If email not found or processing fails
        """
        logger.info(f"Processing single email: {message_id}")
        
        try:
            # Fetch the specific email
            raw_email = self.fetcher.get_email_body(message_id)
            
            if not raw_email:
                raise ValueError(f"Email {message_id} not found")
            
            # Preprocess
            cleaned_email = self.preprocessor.clean_email(raw_email)
            
            # Summarize
            summary = self.summarizer.summarize(cleaned_email)
            
            # Store
            self.storage.save_summary(summary)
            
            logger.info(f"Successfully processed email {message_id}")
            return summary
        
        except Exception as e:
            logger.error(f"Error processing email {message_id}: {e}")
            raise
