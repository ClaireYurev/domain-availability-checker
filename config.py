from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


def _load_dotenv_if_present() -> None:
    """
    Load variables from a .env file if python-dotenv is installed.

    Failing to import the package is treated as a no-op.
    """
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    else:
        load_dotenv()


@dataclass
class Settings:
    """
    Configuration settings for the RapidAPI client and runtime behavior.
    """

    rapidapi_key: str
    rapidapi_host: str
    rapidapi_base_url: str
    rapidapi_endpoint_path: str = "/api/v1"
    rate_limit_per_minute: int = 50
    rate_limit_period_seconds: int = 60
    max_retries: int = 5
    request_timeout_seconds: int = 10
    backoff_factor: float = 2.0

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Construct Settings from environment variables.

        Required:
          * RAPIDAPI_KEY
          * RAPIDAPI_HOST

        Optional:
          * RAPIDAPI_BASE_URL (defaults to https://<RAPIDAPI_HOST>)
          * RAPIDAPI_ENDPOINT_PATH (defaults to /api/v1)
          * RATE_LIMIT_PER_MINUTE (defaults to 50)
          * RATE_LIMIT_PERIOD_SECONDS (defaults to 60)
          * MAX_RETRIES (defaults to 5)
          * REQUEST_TIMEOUT_SECONDS (defaults to 10)
          * BACKOFF_FACTOR (defaults to 2.0)
        """
        _load_dotenv_if_present()

        key = os.getenv("RAPIDAPI_KEY")
        host = os.getenv("RAPIDAPI_HOST")
        base_url = os.getenv("RAPIDAPI_BASE_URL")

        if not key:
            raise RuntimeError("RAPIDAPI_KEY environment variable is required.")
        if not host:
            raise RuntimeError("RAPIDAPI_HOST environment variable is required.")

        if not base_url:
            base_url = f"https://{host}"

        def _int_env(name: str, default: int) -> int:
            val = os.getenv(name)
            if val is None:
                return default
            try:
                return int(val)
            except ValueError:
                logger.warning(
                    "Invalid integer for %s=%r, falling back to %d", name, val, default
                )
                return default

        def _float_env(name: str, default: float) -> float:
            val = os.getenv(name)
            if val is None:
                return default
            try:
                return float(val)
            except ValueError:
                logger.warning(
                    "Invalid float for %s=%r, falling back to %f", name, val, default
                )
                return default

        return cls(
            rapidapi_key=key,
            rapidapi_host=host,
            rapidapi_base_url=base_url.rstrip("/"),
            rapidapi_endpoint_path=os.getenv("RAPIDAPI_ENDPOINT_PATH", "/api/v1"),
            rate_limit_per_minute=_int_env("RATE_LIMIT_PER_MINUTE", 50),
            rate_limit_period_seconds=_int_env("RATE_LIMIT_PERIOD_SECONDS", 60),
            max_retries=_int_env("MAX_RETRIES", 5),
            request_timeout_seconds=_int_env("REQUEST_TIMEOUT_SECONDS", 10),
            backoff_factor=_float_env("BACKOFF_FACTOR", 2.0),
        )
