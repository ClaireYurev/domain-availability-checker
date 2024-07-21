import itertools
import requests
import time
import threading
import os
import sys

def generate_combinations(length=5):
    characters = 'abcdefghijklmnopqrstuvwxyz'
    combinations = [''.join(p) for p in itertools.product(characters, repeat=length)]
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

def input_with_timeout(prompt, timeout):
    print(prompt, end='\n', flush=True)
    result = [None]

    def on_input():
        result[0] = input()
    
    thread = threading.Thread(target=on_input)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None
    return result[0]

def load_existing_domains(output_path):
    existing_domains = set()
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            for line in f:
                domain = line.split(':')[0].strip()
                existing_domains.add(domain)
    return existing_domains

def check_all_domains(api_key, output_path, stop_event):
    combinations = generate_combinations()
    existing_domains = load_existing_domains(output_path)
    combinations = [combo for combo in combinations if f"{combo}.com" not in existing_domains]
    
    requests_per_hour = 999
    delay_between_requests = 3600 / requests_per_hour  # 3600 seconds in an hour
    counter = 0

    with open(output_path, 'a') as f:  # Open file in append mode
        for i, combination in enumerate(combinations):
            if stop_event.is_set():
                print("\nExited at user's request. Progress saved in the results file.")
                break

            domain = combination
            try:
                is_available = check_domain_availability(domain, api_key)
                result = f"{domain}.com: {'Available,' if is_available else 'NA,'}"
                print(result)
                f.write(result + '\n')
                f.flush()  # Ensure data is written to the file immediately
            except Exception as e:
                print(f"Error checking {domain}.com: {e}")

            time.sleep(delay_between_requests)  # Wait to avoid hitting the rate limit

            # If we reach the rate limit, wait for the next hour
            if (i + 1) % requests_per_hour == 0:
                print("Reached rate limit. Waiting for the next hour...")
                time.sleep(3600)  # Wait for an hour

            # After every 10 checks, offer the user the opportunity to pause
            counter += 1
            if counter % 10 == 0:
                user_input = input_with_timeout("Press 'p' to pause or any other key to continue.", 2)
                if user_input and user_input.strip().lower() == 'p':
                    print("Execution paused. Press any key to resume.")
                    input()

def check_for_exit(stop_event):
    while True:
        if input().strip().lower() == 'q':
            stop_event.set()
            break

# Get the directory of the current script
script_dir = os.path.dirname(__file__)
output_path = os.path.join(script_dir, 'available_domains.txt')

# Your RapidAPI key
api_key = "Your Key"

stop_event = threading.Event()
exit_thread = threading.Thread(target=check_for_exit, args=(stop_event,))
exit_thread.daemon = True
exit_thread.start()

print("Welcome to domain name checker. Connecting to RapidApi.com to check available names.")
print("Press Q and then hit Enter at any time to save progress and exit.")

try:
    check_all_domains(api_key, output_path, stop_event)
except SystemExit:
    print("Exited at user's request. Finished updating the results file.")
    sys.exit(0)
