from __future__ import annotations

import argparse
import logging
import sys
from typing import Iterable

from .config import Settings
from .client import DomainAvailabilityClient
from .batch import iter_domains_from_file, check_domains, write_results_to_csv


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch domain availability checker using RapidAPI.",
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Path to text file containing one domain per line. Use '-' to read from stdin.",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to write CSV results. Use '-' for stdout.",
        default="-",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the input and print how many domains would be checked, without calling the API.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args(list(argv))


def _iter_domains_from_stdin() -> Iterable[str]:
    for line in sys.stdin:
        domain = line.strip()
        if not domain or domain.startswith("#"):
            continue
        yield domain


def main(argv: Iterable[str] | None = None) -> int:
    ns = parse_args(sys.argv[1:] if argv is None else argv)
    configure_logging(ns.verbose)

    if ns.input == "-":
        domains = list(_iter_domains_from_stdin())
    else:
        domains = list(iter_domains_from_file(ns.input))

    logging.getLogger(__name__).info("Loaded %d domains", len(domains))

    if ns.dry_run:
        print(f"Would check {len(domains)} domains.")
        return 0

    settings = Settings.from_env()
    client = DomainAvailabilityClient(settings)

    try:
        results_iter = check_domains(client, domains)
        if ns.output == "-":
            out = sys.stdout
        else:
            out = open(ns.output, "w", encoding="utf-8", newline="")

        with out:
            write_results_to_csv(results_iter, out)
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
