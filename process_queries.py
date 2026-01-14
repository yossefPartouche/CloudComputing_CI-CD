import requests
import json
import os

STORE1 = "http://localhost:5001"
STORE2 = "http://localhost:5002"
ORDER_SERVICE = "http://localhost:5003"  # Adjust port as needed

def parse_query_line(line):
    """Parse a line from query.txt"""
    line = line.strip()
    if not line:
        return None, None
    
    if line.startswith("query:"):
        query_part = line[6:].strip()
        if query_part.endswith(";"):
            query_part = query_part[:-1]
        
        # Split on first comma
        parts = query_part.split(",", 1)
        if len(parts) != 2:
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
        except json.JSONDecodeError:
            return None, None
    
    return None, None

def execute_query(store_num, query_string):
    """Execute a GET query on pet-types"""
    store_url = STORE1 if store_num == "1" else STORE2
    
    url = f"{store_url}/pet-types?{query_string}"
    
    try:
        r = requests.get(url, timeout=10)
        status_code = r.status_code
        
        if status_code == 200:
            payload = r.json()
            return status_code, json.dumps(payload, indent=2)
        else:
            return status_code, "NONE"
    except Exception as e:
        print(f"Error executing query: {e}")
        return 500, "NONE"

def execute_purchase(purchase_data):
    """Execute a POST purchase"""
    url = f"{ORDER_SERVICE}/purchases"
    
    try:
        r = requests.post(url, json=purchase_data, timeout=10)
        status_code = r.status_code
        
        if status_code == 201:
            payload = r.json()
            return status_code, json.dumps(payload, indent=2)
        else:
            return status_code, "NONE"
    except Exception as e:
        print(f"Error executing purchase: {e}")
        return 500, "NONE"

def main():
    query_file = "query.txt"
    response_file = "response.txt"
    
    if not os.path.exists(query_file):
        print(f"Warning: {query_file} not found. Creating empty response.txt")
        with open(response_file, 'w') as f:
            f.write("")
        return
    
    with open(query_file, 'r') as f:
        lines = f.readlines()
    
    results = []
    
    for line in lines:
        entry_type, data = parse_query_line(line)
        
        if entry_type == "query":
            status_code, payload = execute_query(data["store"], data["query"])
            results.append(f"{status_code}\n{payload}\n;")
        
        elif entry_type == "purchase":
            status_code, payload = execute_purchase(data)
            results.append(f"{status_code}\n{payload}\n;")
    
    # Write results to response.txt
    with open(response_file, 'w') as f:
        for result in results:
            f.write(result + "\n")
    
    print(f"Successfully processed {len(results)} entries")
    print(f"Response written to {response_file}")

if __name__ == "__main__":
    main()