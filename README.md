# Domain Availability Checker - RapidAPI Integration

`domain-availability-checker` is a Python tool for **batch checking domain name availability** using a RapidAPI-powered domain service.

It is designed for **long-running jobs** that may process tens or hundreds of thousands of domains, with:

- Explicit configuration for API keys & endpoints
- Rate limiting to stay under RapidAPI quotas
- Retry logic with exponential backoff (including 429 handling)
- Robust error handling for network and server issues

You can point it at any RapidAPI "domain availability" API, such as:
- WhoisXMLAPI's *Domain Availability* service exposed via RapidAPI   
- Other domain APIs listed in RapidAPI's domain category (e.g. *Domain Availability*, *Domain Checker*, or bulk domain checkers)   

> **Note:** Different providers use slightly different paths and JSON fields. This project makes those parts configurable and keeps the "batch & reliability" logic reusable.

---

## Features

- **RapidAPI integration**
  - Uses standard RapidAPI headers: `x-rapidapi-key` and `x-rapidapi-host`   
- **Rate limiting**
  - Sliding-window limiter with configurable `RATE_LIMIT_PER_MINUTE` / `RATE_LIMIT_PERIOD_SECONDS`
- **Resilient against throttling**
  - Handles HTTP `429` with `Retry-After` if provided, otherwise exponential backoff
- **Retries for transient errors**
  - Retries network timeouts and 5xx status codes
- **Batch-friendly CLI**
  - Read domains from a file or stdin, emit CSV results
- **Extensible parsing**
  - Works with common response formats (e.g. `DomainInfo.domainAvailability` or a top-level `available` flag), and can be customized for your particular API.   

---

## Requirements

- Python 3.10+
- A RapidAPI account & subscription to a domain availability API (e.g. WhoisXMLAPI Domain Availability on RapidAPI)   
- Dependencies (installed via `requirements.txt`):
  - [`requests`](https://pypi.org/project/requests/)
  - [`python-dotenv`](https://pypi.org/project/python-dotenv/) (optional, for `.env` support)

---

## Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/<your-username>/domain-availability-checker.git
cd domain-availability-checker
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
