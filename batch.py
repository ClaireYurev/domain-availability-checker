from __future__ import annotations

from typing import Iterable, TextIO
import logging
import csv

from .client import DomainAvailabilityClient, DomainAvailabilityResult

logger = logging.getLogger(__name__)


def iter_domains_from_file(path: str) -> Iterable[str]:
    """
    Yield domain names from a text file, skipping blank lines and comments.
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            domain = line.strip()
            if not domain or domain.startswith("#"):
                continue
            yield domain


def write_results_to_csv(results: Iterable[DomainAvailabilityResult], out: TextIO) -> None:
    """
    Write a sequence of DomainAvailabilityResult objects to a CSV file-like object.
    """
    writer = csv.writer(out)
    writer.writerow(["domain", "available", "status", "http_status"])
    for r in results:
        writer.writerow(
            [
                r.domain,
                "" if r.available is None else str(r.available).lower(),
                r.status,
                "" if r.http_status is None else r.http_status,
            ]
        )


def check_domains(client: DomainAvailabilityClient, domains: Iterable[str]) -> Iterable[DomainAvailabilityResult]:
    """
    Iterate over domains, checking each one and yielding DomainAvailabilityResult objects.
    """
    for idx, domain in enumerate(domains, start=1):
        result = client.check_domain(domain)
        logger.info(
            "[%d] %s -> %s (available=%s)",
            idx,
            result.domain,
            result.status,
            result.available,
        )
        yield result
