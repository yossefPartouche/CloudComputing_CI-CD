import requests
import sys
import time
from tests.test_data import (
    STORE1, STORE2,
    PET_TYPE1, PET_TYPE2, PET_TYPE3, PET_TYPE4,
    PET1_TYPE1, PET2_TYPE1, PET3_TYPE1, PET4_TYPE2,
    PET5_TYPE3, PET6_TYPE3, PET7_TYPE4, PET8_TYPE4
)

def wait_for_service(url, max_retries=10, delay=2):
    """Wait for a service to be ready"""
    for i in range(max_retries):
        try:
            r = requests.get(f"{url}/pet-types", timeout=5)
            if r.status_code in [200, 404]:  # Service is responding
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"Waiting for {url} to be ready... (attempt {i+1}/{max_retries})")
        time.sleep(delay)
    return False

def post_pet_type(store_url, payload):
    """POST a pet-type and return its ID"""
    try:
        r = requests.post(f"{store_url}/pet-types", json=payload, timeout=10)
        if r.status_code != 201:
            print(f"Error posting pet-type to {store_url}: {r.status_code} - {r.text}")
            sys.exit(1)
        return r.json()["id"]
    except Exception as e:
        print(f"Exception posting pet-type: {e}")
        sys.exit(1)

def post_pet(store_url, type_id, payload):
    """POST a pet to a specific pet-type"""
    try:
        r = requests.post(f"{store_url}/pet-types/{type_id}/pets", json=payload, timeout=10)
        if r.status_code != 201:
            print(f"Error posting pet to {store_url}/pet-types/{type_id}/pets: {r.status_code} - {r.text}")
            sys.exit(1)
    except Exception as e:
        print(f"Exception posting pet: {e}")
        sys.exit(1)

def main():
    # Wait for services to be ready
    print("Waiting for services to be ready...")
    if not wait_for_service(STORE1):
        print("Store 1 failed to start")
        sys.exit(1)
    if not wait_for_service(STORE2):
        print("Store 2 failed to start")
        sys.exit(1)
    
    print("Services are ready, starting seeding...")
    
    # Store 1
    print("Creating pet types for Store 1...")
    id1 = post_pet_type(STORE1, PET_TYPE1)
    print(f"Created pet-type {id1}: Golden Retriever")
    id2 = post_pet_type(STORE1, PET_TYPE2)
    print(f"Created pet-type {id2}: Australian Shepherd")
    id3 = post_pet_type(STORE1, PET_TYPE3)
    print(f"Created pet-type {id3}: Abyssinian")

    # Store 2
    print("Creating pet types for Store 2...")
    id4 = post_pet_type(STORE2, PET_TYPE1)
    print(f"Created pet-type {id4}: Golden Retriever")
    id5 = post_pet_type(STORE2, PET_TYPE2)
    print(f"Created pet-type {id5}: Australian Shepherd")
    id6 = post_pet_type(STORE2, PET_TYPE4)
    print(f"Created pet-type {id6}: bulldog")

    # Add pets to Store 1
    print("Adding pets to Store 1...")
    post_pet(STORE1, id1, PET1_TYPE1)
    post_pet(STORE1, id1, PET2_TYPE1)
    post_pet(STORE1, id3, PET5_TYPE3)
    post_pet(STORE1, id3, PET6_TYPE3)

    # Add pets to Store 2
    print("Adding pets to Store 2...")
    post_pet(STORE2, id4, PET3_TYPE1)
    post_pet(STORE2, id5, PET4_TYPE2)
    post_pet(STORE2, id6, PET7_TYPE4)
    post_pet(STORE2, id6, PET8_TYPE4)

    print("✓ Successfully seeded all data")

if __name__ == "__main__":
    main()