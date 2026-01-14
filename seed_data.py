import requests
import sys

STORE1 = "http://localhost:5001"
STORE2 = "http://localhost:5002"

# Pet types from your test file
PET_TYPE1 = {"type": "Golden Retriever"}
PET_TYPE2 = {"type": "Australian Shepherd"}
PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE4 = {"type": "bulldog"}

# Pets
PET1_TYPE1 = {"name": "Lander", "birthdate": "05-14-2020"}
PET2_TYPE1 = {"name": "Lanky"}
PET3_TYPE1 = {"name": "Shelly", "birthdate": "07-07-2019"}
PET4_TYPE2 = {"name": "Felicity", "birthdate": "27-11-2011"}
PET5_TYPE3 = {"name": "Muscles"}
PET6_TYPE3 = {"name": "Junior"}
PET7_TYPE4 = {"name": "Lazy", "birthdate": "07-08-2018"}
PET8_TYPE4 = {"name": "Lemon", "birthdate": "27-03-2020"}

def post_pet_type(store_url, payload):
    """POST a pet-type and return its ID"""
    r = requests.post(f"{store_url}/pet-types", json=payload, timeout=10)
    if r.status_code != 201:
        print(f"Error posting pet-type to {store_url}: {r.status_code}")
        sys.exit(1)
    return r.json()["id"]

def post_pet(store_url, type_id, payload):
    """POST a pet to a specific pet-type"""
    r = requests.post(f"{store_url}/pet-types/{type_id}/pets", json=payload, timeout=10)
    if r.status_code != 201:
        print(f"Error posting pet to {store_url}/pet-types/{type_id}/pets: {r.status_code}")
        sys.exit(1)

def main():
    # Store 1
    id1 = post_pet_type(STORE1, PET_TYPE1)
    id2 = post_pet_type(STORE1, PET_TYPE2)
    id3 = post_pet_type(STORE1, PET_TYPE3)

    # Store 2
    id4 = post_pet_type(STORE2, PET_TYPE1)
    id5 = post_pet_type(STORE2, PET_TYPE2)
    id6 = post_pet_type(STORE2, PET_TYPE4)

    # Add pets to Store 1
    post_pet(STORE1, id1, PET1_TYPE1)
    post_pet(STORE1, id1, PET2_TYPE1)
    post_pet(STORE1, id3, PET5_TYPE3)
    post_pet(STORE1, id3, PET6_TYPE3)

    # Add pets to Store 2
    post_pet(STORE2, id4, PET3_TYPE1)
    post_pet(STORE2, id5, PET4_TYPE2)
    post_pet(STORE2, id6, PET7_TYPE4)
    post_pet(STORE2, id6, PET8_TYPE4)

    print("Successfully seeded all data")

if __name__ == "__main__":
    main()