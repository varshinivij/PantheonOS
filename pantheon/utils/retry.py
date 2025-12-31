"""Retry utilities for handling transient failures."""

import asyncio
import random
from typing import TypeVar, Callable

from .log import logger

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed)."""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add ±25% jitter to prevent thundering herd
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


async def retry_on_condition(
    func: Callable[..., T],
    *args,
    config: RetryConfig | None = None,
    should_retry: Callable[[Exception], bool] = lambda e: True,
    log_prefix: str = "",
    **kwargs
) -> T:
    """Retry an async function with exponential backoff based on condition.
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        config: Retry configuration (uses defaults if None)
        should_retry: Function to check if exception should trigger retry
        log_prefix: Prefix for log messages
        **kwargs: Keyword arguments for func
    
    Returns:
        Result from successful function call
    
    Raises:
        Last exception if all retries fail or exception is not retryable
    """
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            # Check if we should retry this exception
            if not should_retry(e):
                logger.debug(f"{log_prefix}Exception not retryable: {type(e).__name__}")
                raise
            
            if attempt < config.max_attempts - 1:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"{log_prefix}Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"{log_prefix}All {config.max_attempts} attempts failed. "
                    f"Last error: {e}"
                )
                raise
    
    # This should never be reached, but for type safety
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry loop completed without result or exception")


def is_rate_limit_error(exception: Exception) -> bool:
    """Check if exception is a rate limit error."""
    # Check for litellm RateLimitError by class name
    exception_type = type(exception).__name__
    if "RateLimitError" in exception_type:
        return True
    
    # Check error message for common rate limit indicators
    error_msg = str(exception).lower()
    rate_limit_indicators = [
        "rate limit",
        "rate_limit",
        "quota",
        "too many requests",
        "429",
        "resource exhausted",
        "exceeded your current quota",
    ]
    
    return any(indicator in error_msg for indicator in rate_limit_indicators)


# Preset configs for common scenarios
RATE_LIMIT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)

NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True,
)
