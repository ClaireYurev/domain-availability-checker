import itertools
import requests
import time

def generate_combinations():
    characters = 'abcdefghijklmnopqrstuvwxyz'
    combinations = [''.join(p) for p in itertools.product(characters, repeat=4)]
    return combinations

def check_domain_availability(domain, api_key):
    url = "https://domainstatus.p.rapidapi.com/v1/domain/available"
    payload = {
        "name": domain,
        "tld": "com"
    }
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "domainstatus.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    return result.get('available', False)

def check_all_domains(api_key):
    combinations = generate_combinations()
    available_domains = []
    requests_per_hour = 999
    delay_between_requests = 3600 / requests_per_hour  # 3600 seconds in an hour

    for i, combination in enumerate(combinations):
        domain = combination
        try:
            if check_domain_availability(domain, api_key):
                available_domains.append(f"{domain}.com")
        except Exception as e:
            print(f"Error checking {domain}.com: {e}")

        time.sleep(delay_between_requests)  # Wait to avoid hitting the rate limit

        # If we reach the rate limit, wait for the next hour
        if (i + 1) % requests_per_hour == 0:
            print("Reached rate limit. Waiting for the next hour...")
            time.sleep(3600)  # Wait for an hour

    return available_domains

# Your RapidAPI key
api_key = "YOUR_RAPIDAPI_KEY"

available_domains = check_all_domains(api_key)

# Save the available domains to a file
with open('available_domains.txt', 'w') as f:
    for domain in available_domains:
        f.write(f"{domain}\n")

print(f"Available domains saved to available_domains.txt")
