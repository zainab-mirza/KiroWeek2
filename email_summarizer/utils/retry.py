"""Retry logic and error handling utilities."""

import time
import logging
from typing import Callable, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


def retry_with_backoff(
    config: Optional[RetryConfig] = None, exceptions: tuple = (Exception,)
):
    """Decorator for retrying functions with exponential backoff.

    Args:
        config: Retry configuration
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed. Last error: {e}"
                        )

            # If we get here, all attempts failed
            raise last_exception

        return wrapper

    return decorator


class RateLimitError(Exception):
    """Exception raised when rate limit is hit."""

    pass


def handle_rate_limit(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle rate limiting with exponential backoff.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    config = RetryConfig(
        max_attempts=5, initial_delay=1.0, max_delay=60.0, exponential_base=2.0
    )

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        for attempt in range(config.max_attempts):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                if attempt < config.max_attempts - 1:
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Rate limit hit. Waiting {delay:.1f}s before retry "
                        f"(attempt {attempt + 1}/{config.max_attempts})"
                    )
                    time.sleep(delay)
                else:
                    logger.error("Rate limit: all retry attempts exhausted")
                    raise
            except Exception as e:
                # Don't retry on other exceptions
                raise

        raise RateLimitError("Rate limit: all retry attempts exhausted")

    return wrapper


def log_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to log errors with detailed information.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {type(e).__name__}: {str(e)}", exc_info=True
            )
            raise

    return wrapper


def user_friendly_error(error: Exception) -> str:
    """Convert exception to user-friendly error message.

    Args:
        error: Exception object

    Returns:
        User-friendly error message
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Map common errors to friendly messages
    friendly_messages = {
        "ConnectionError": "Unable to connect to the service. Please check your internet connection.",
        "TimeoutError": "The request timed out. Please try again.",
        "RateLimitError": "Rate limit exceeded. Please wait a moment and try again.",
        "AuthenticationError": "Authentication failed. Please check your credentials.",
        "PermissionError": "Permission denied. Please check file permissions.",
        "FileNotFoundError": "File not found. Please check the path.",
        "ValueError": f"Invalid value: {error_msg}",
        "KeyError": f"Missing required field: {error_msg}",
        "JSONDecodeError": "Invalid JSON format. Please check the data.",
    }

    return friendly_messages.get(error_type, f"An error occurred: {error_msg}")
