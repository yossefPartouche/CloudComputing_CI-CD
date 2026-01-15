import requests
import json
import os
import sys
import time

STORE1 = "http://localhost:5001"
STORE2 = "http://localhost:5002"
ORDER_SERVICE = "http://localhost:5003"

def wait_for_service(url, max_retries=10, delay=2):
    """Wait for a service to be ready"""
    for i in range(max_retries):
        try:
            r = requests.get(f"{url}/pet-types", timeout=5)
            if r.status_code in [200, 404]:
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"Waiting for {url} to be ready... (attempt {i+1}/{max_retries})")
        time.sleep(delay)
    return False

def parse_query_line(line):
    """Parse a line from query.txt"""
    line = line.strip()
    if not line or line.startswith('#'):  # Skip empty lines and comments
        return None, None
    
    if line.startswith("query:"):
        query_part = line[6:].strip()
        if query_part.endswith(";"):
            query_part = query_part[:-1]
        
        # Split on first comma
        parts = query_part.split(",", 1)
        if len(parts) != 2:
            print(f"Invalid query format: {line}")
            return None, None
        
        store_num = parts[0].strip()
        query_string = parts[1].strip()
        
        return "query", {"store": store_num, "query": query_string}
    
    elif line.startswith("purchase:"):
        purchase_part = line[9:].strip()
        if purchase_part.endswith(";"):
            purchase_part = purchase_part[:-1]
        
        try:
            purchase_json = json.loads(purchase_part)
            return "purchase", purchase_json
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in purchase: {e}")
            return None, None
    
    return None, None

def execute_query(store_num, query_string):
    """Execute a GET query on pet-types"""
    store_url = STORE1 if store_num == "1" else STORE2
    
    url = f"{store_url}/pet-types?{query_string}"
    print(f"Executing query: GET {url}")
    
    try:
        r = requests.get(url, timeout=10)
        status_code = r.status_code
        
        if status_code == 200:
            payload = r.json()
            # Format JSON nicely
            payload_str = json.dumps(payload, indent=2)
            print(f"Response: {status_code}\n{payload_str}")
            return status_code, payload_str
        else:
            print(f"Response: {status_code} - NONE")
            return status_code, "NONE"
    except Exception as e:
        print(f"Error executing query: {e}")
        return 500, "NONE"

def execute_purchase(purchase_data):
    """Execute a POST purchase"""
    url = f"{ORDER_SERVICE}/purchases"
    print(f"Executing purchase: POST {url}")
    print(f"Payload: {json.dumps(purchase_data, indent=2)}")
    
    try:
        r = requests.post(url, json=purchase_data, timeout=10)
        status_code = r.status_code
        
        if status_code == 201:
            payload = r.json()
            payload_str = json.dumps(payload, indent=2)
            print(f"Response: {status_code}\n{payload_str}")
            return status_code, payload_str
        else:
            print(f"Response: {status_code} - NONE")
            return status_code, "NONE"
    except Exception as e:
        print(f"Error executing purchase: {e}")
        return 500, "NONE"

def main():
    query_file = "query.txt"
    response_file = "response.txt"
    
    # Wait for services
    print("Waiting for services to be ready...")
    if not wait_for_service(STORE1) or not wait_for_service(STORE2):
        print("Services failed to start")
        sys.exit(1)
    
    if not os.path.exists(query_file):
        print(f"Warning: {query_file} not found. Creating empty response.txt")
        with open(response_file, 'w') as f:
            f.write("")
        return
    
    with open(query_file, 'r') as f:
        lines = f.readlines()
    
    print(f"Processing {len(lines)} lines from {query_file}...")
    results = []
    
    for line_num, line in enumerate(lines, 1):
        print(f"\n--- Processing line {line_num}: {line.strip()} ---")
        entry_type, data = parse_query_line(line)
        
        if entry_type == "query":
            status_code, payload = execute_query(data["store"], data["query"])
            results.append(f"{status_code}\n{payload}\n;")
        
        elif entry_type == "purchase":
            status_code, payload = execute_purchase(data)
            results.append(f"{status_code}\n{payload}\n;")
        
        elif line.strip():  # Non-empty line that couldn't be parsed
            print(f"Warning: Could not parse line {line_num}")
    
    # Write results to response.txt
    with open(response_file, 'w') as f:
        for result in results:
            f.write(result + "\n")
    
    print(f"\n✓ Successfully processed {len(results)} entries")
    print(f"✓ Response written to {response_file}")

if __name__ == "__main__":
    main()