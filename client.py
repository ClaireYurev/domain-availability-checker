from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging
import time

import requests

from .config import Settings
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class DomainAvailabilityResult:
    """
    Result of a domain availability check.
    """

    domain: str
    available: Optional[bool]
    status: str
    http_status: Optional[int]
    raw: Optional[Dict[str, Any]]


class DomainAvailabilityClient:
    """
    Thin wrapper around a RapidAPI domain-availability-style API.

    The concrete API endpoint and JSON response format can vary between
    providers; the defaults here work for many common services, but you
    may need to adjust `_params` and `_parse_availability` for your
    specific API.
    """

    def __init__(self, settings: Settings, session: Optional[requests.Session] = None) -> None:
        self.settings = settings
        self.session = session or requests.Session()
        self.rate_limiter = RateLimiter(
            max_calls=settings.rate_limit_per_minute,
            period=settings.rate_limit_period_seconds,
        )

    def close(self) -> None:
        self.session.close()

    # --- Request construction -------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "x-rapidapi-key": self.settings.rapidapi_key,
            "x-rapidapi-host": self.settings.rapidapi_host,
            "accept": "application/json",
        }

    def _params(self, domain: str) -> Dict[str, str]:
        """
        Build query parameters for the API call.

        Many RapidAPI domain services accept a `domain` or `domainName`
        query parameter. Adjust this method if your chosen API uses a
        different name.
        """
        return {
            "domain": domain,
        }

    # --- Response parsing -----------------------------------------------------

    def _parse_availability(self, domain: str, payload: Dict[str, Any]) -> DomainAvailabilityResult:
        """
        Attempt to infer availability from several common response shapes.

        If the API you are using returns a different structure, you can
        change this method accordingly.
        """
        available: Optional[bool] = None
        status = "unknown"

        # Pattern 1: {"DomainInfo": {"domainName": "...", "domainAvailability": "AVAILABLE"}}
        domain_info = None
        if isinstance(payload.get("DomainInfo"), dict):
            domain_info = payload["DomainInfo"]
        elif isinstance(payload.get("domainInfo"), dict):
            domain_info = payload["domainInfo"]

        if domain_info:
            value = domain_info.get("domainAvailability") or domain_info.get("availability")
            if isinstance(value, str):
                value_upper = value.upper()
                if "AVAILABLE" in value_upper:
                    available = True
                    status = value_upper
                elif "UNAVAILABLE" in value_upper or "TAKEN" in value_upper:
                    available = False
                    status = value_upper

        # Pattern 2: {"available": true}
        if available is None and "available" in payload:
            val = payload["available"]
            if isinstance(val, bool):
                available = val
                status = "AVAILABLE" if val else "UNAVAILABLE"

        return DomainAvailabilityResult(
            domain=domain,
            available=available,
            status=status,
            http_status=200,
            raw=payload,
        )

    # --- Public API -----------------------------------------------------------

    def check_domain(self, domain: str) -> DomainAvailabilityResult:
        """
        Check a single domain, with rate limiting and retries.
        """
        self.rate_limiter.acquire()
        url = f"{self.settings.rapidapi_base_url}{self.settings.rapidapi_endpoint_path}"

        backoff = 1.0
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.settings.max_retries + 1):
            try:
                resp = self.session.get(
                    url,
                    headers=self._headers(),
                    params=self._params(domain),
                    timeout=self.settings.request_timeout_seconds,
                )
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                last_exc = exc
                logger.warning("Network error on attempt %s for %s: %s", attempt, domain, exc)
                time.sleep(backoff)
                backoff *= self.settings.backoff_factor
                continue

            # Handle throttling
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                try:
                    wait_seconds = float(retry_after) if retry_after is not None else backoff
                except ValueError:
                    wait_seconds = backoff
                logger.warning("Received 429 for %s, sleeping for %.1fs", domain, wait_seconds)
                time.sleep(wait_seconds)
                backoff *= self.settings.backoff_factor
                continue

            # Handle transient server errors
            if 500 <= resp.status_code < 600:
                logger.warning(
                    "Server error %s for %s on attempt %s",
                    resp.status_code,
                    domain,
                    attempt,
                )
                time.sleep(backoff)
                backoff *= self.settings.backoff_factor
                continue

            # Non-error or client error response: parse once and return
            try:
                payload = resp.json()
            except ValueError:
                logger.error("Non-JSON response (%s) for %s", resp.status_code, domain)
                return DomainAvailabilityResult(
                    domain=domain,
                    available=None,
                    status="invalid-json",
                    http_status=resp.status_code,
                    raw=None,
                )

            result = self._parse_availability(domain, payload)
            result.http_status = resp.status_code
            return result

        # Exhausted retries
        status = "error"
        if last_exc is not None:
            status = f"error: {last_exc.__class__.__name__}"

        return DomainAvailabilityResult(
            domain=domain,
            available=None,
            status=status,
            http_status=None,
            raw=None,
        )
