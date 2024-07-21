# domain-availability-checker
A simple program that uses RapidAPI's domain name availability API for checking the availability of domain names.

# How it works
Generate Combinations: The generate_combinations function generates all 4-character combinations of the English alphabet.
Check Domain Availability: The check_domain_availability function uses the RapidAPI endpoint to check if a domain is available.
Check All Domains: The check_all_domains function iterates over all combinations, checks their availability, and stores available domains in a list. It includes:
Rate Limiting Logic: It waits for delay_between_requests seconds between each request.
Hourly Reset: After 999 requests, it waits for an hour before continuing.
Save Results: The script saves all available domains to a file named available_domains.txt.
By including the delay_between_requests and the hourly reset, this script ensures that it doesn't exceed the 999 requests per hour limit. You can run this script to generate and check the availability of 4-character .com domains efficiently within the given constraints.
