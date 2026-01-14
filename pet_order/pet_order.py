from flask import Flask, jsonify, request
import requests
import os
from pymongo import MongoClient
import random
import uuid

app = Flask(__name__)

# -----------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------
# Connect to MongoDB
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)

db = client['order_db']
transactions_col = db['transactions']

# Store Service URLs
STORE1_URL = "http://pet-store1:8000"
STORE2_URL = "http://pet-store2:8000"

# -----------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------


def get_type_id(store_url, pet_type_name):
    """ Helper function to retrieve the numeric ID of a given pet type string from the specified store.
    Args:
        store_url: Base URL of the pet store service.
        pet_type_name: The name of the pet type whose ID is needed.
    Returns:
        String ID of the pet type if found, otherwise None.
    """
    try:
        response = requests.get(f"{store_url}/pet-types", timeout=2)
        if response.status_code == 200:
            for t in response.json():
                if t.get('type', '').lower() == pet_type_name.lower():
                    return str(t.get('id'))
    except:
        pass
    return None


def find_available_pet(pet_type_name, store_id=None, pet_name=None):
    """
    Helper to find an available pet matching the criteria.
    
    Selection rules:
    1. If store AND pet-name given: pet must exist in that specific store
    2. If store given but NO pet-name: choose random pet from that store
    3. If NO store given: choose random pet from ANY store
    
    Args:
        pet_type_name: Type of pet to find
        store_id: Optional store ID (1 or 2)
        pet_name: Optional specific pet name
    
    Returns:
        Tuple of (pet_object, store_id, store_url, type_id) or (None, None, None, None)
    """
    store_map = {1: STORE1_URL, 2: STORE2_URL}
    
    # If store_id is provided, only check that store
    if store_id is not None:
        store_ids = [store_id]
    else:
        # If no store_id, check both stores
        store_ids = [1, 2]
        random.shuffle(store_ids)  # Randomize for fairness
    
    # Search through stores
    for sid in store_ids:
        # Get the store URL for the current store
        store_url = store_map[sid]
        
        # Get the type ID for this pet type
        type_id = get_type_id(store_url, pet_type_name)
        if not type_id:
            continue  # This store doesn't have this pet type
        
        try:
            # Get all pets of this type from the store
            pets_response = requests.get(f"{store_url}/pet-types/{type_id}/pets", timeout=5)
            
            if pets_response.status_code != 200:
                continue  # This store doesn't have this pet type
            
            pets = pets_response.json()
            if not isinstance(pets, list) or len(pets) == 0:
                continue  # No pets available
            
            # Select pet based on criteria
            if pet_name:
                # Find specific pet by name (case-insensitive)
                pet_name_lower = pet_name.lower().strip()
                selected_pet = next((p for p in pets if p.get("name", "").lower().strip() == pet_name_lower), None)
            else:
                # Choose random pet from available ones
                selected_pet = random.choice(pets)
            
            # If a pet is found, return it, the store ID, the store URL, and the type ID
            if selected_pet:
                return selected_pet, sid, store_url, type_id
        
        except Exception as e:
            print(f"Error checking store {sid}: {e}")
            continue
    
    # No matching pet found
    return None, None, None, None

# -----------------------------------------------------------
# ROUTES
# -----------------------------------------------------------

@app.route('/purchases', methods=['POST'])
def purchase_pet():
    """
     Create a purchase transaction.
    
    Required JSON fields:
      - purchaser (string): Name of the purchaser
      - pet-type (string): Type of pet to purchase
    
    Optional JSON fields:
      - store (1 or 2): Specific store to purchase from
      - pet-name (string): Specific pet name [ONLY if store is provided]
    
    Success:
      - 201 with purchase object including: purchase-id, purchaser, pet-type, store, pet-name
    
    Errors:
      - 415: Request is not application/json
      - 400: Malformed data, missing required fields, or no pet available
    """
    
    # validate request content type
    if not request.content_type or "application/json" not in request.content_type:
        return jsonify({"error": "Expected application/json media type"}), 415
    
    #extract data from json request
    try:
        data = request.get_json(force=False, silent=False)
    except Exception:
        return jsonify({"error": "Malformed data"}), 400
    
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Malformed data"}), 400
    
    #extract and validate fields
    purchaser = data.get("purchaser")
    pet_type = data.get("pet-type")
    store = data.get("store")
    pet_name = data.get("pet-name")
    
    
    # Validate inputs
    
    if not purchaser or not isinstance(purchaser, str):
        return jsonify({"error": "Malformed data"}), 400
    if not pet_type or not isinstance(pet_type, str):
        return jsonify({"error": "No pet of this type is available"}), 400

    #pet_name can ONLY be supplied if store is supplied
    if pet_name is not None and store is None:
        return jsonify({"error": "Malformed data"}), 400
    
    #validate store value
    if store is not None:
        if not isinstance(store, int) or store not in [1, 2]:
            return jsonify({"error": "Malformed data"}), 400
        
    # validate pet_name is str if provided
    if pet_name is not None and not isinstance(pet_name, str):
        return jsonify({"error": "Malformed data"}), 400
        
    
    #FIND the pet in the store
    selected_pet, target_store_id, target_store_url, target_type_id = find_available_pet(
        pet_type_name=pet_type,
        store_id=store,
        pet_name=pet_name
    )
    
    if not selected_pet:
        return jsonify({"error": "No pet of this type is available"}), 400
    
    #DELETE the pet from the store
    actual_pet_name = selected_pet.get("name")
    delete_url = f"{target_store_url}/pet-types/{target_type_id}/pets/{actual_pet_name}"
    
    try:
        delete_response = requests.delete(delete_url, timeout=5)
        if delete_response.status_code not in [200, 204]:
            print(f"Failed to delete pet: Status {delete_response.status_code}")
            return jsonify({"error": "No pet of this type is available"}), 400
        
    except Exception as e:
        print(f"Error deleting pet: {e}")
        return jsonify({"error": "No pet of this type is available"}), 400
    
    #Generate purchase ID
    purchase_id = str(uuid.uuid4())
    
    #  Build transaction document
    transaction_doc = {
        "purchase-id": purchase_id,
        "purchaser": purchaser,
        "pet-type": pet_type,
        "store": target_store_id
    }
    
    
    # Store MONGODB
    try:
        transactions_col.insert_one(transaction_doc)
    except Exception as e:
        print(f"Error storing transaction in MongoDB: {e}")
        
    # Create and return purchase response
    purchase_response = {
        "purchaser": purchaser,
        "pet-type": pet_type,
        "store": target_store_id,
        "pet-name": actual_pet_name,
        "purchase-id": purchase_id
    }
    
    return jsonify(purchase_response), 201


@app.route('/transactions', methods=['GET'])
def get_transactions():
    """
    Return a list of transactions.

    Response items are normalized to contain ONLY:
      - purchaser (string)
      - pet-type (string)
      - store (number)
      - purchase-id (string)
    """
    #Check Header
    owner_pc = request.headers.get('OwnerPC')
    if owner_pc != "LovesPetsL2M3n4":
        return jsonify({"error": "unauthorized"}), 401

    #Build Filter from Query String 
    filter_query = {}
    for key, value in request.args.items():
        if key == 'store':
            try:
                filter_query[key] = int(value)
            except:
                pass 
        else:
            filter_query[key] = value

    # Query Mongo
    try:
        raw_txs = list(transactions_col.find(filter_query))

        # Normalize each transaction to the public schema
        txs = []
        for t in raw_txs:
            txs.append({
                "purchaser": t.get("purchaser"),
                "pet-type": t.get("pet-type"),
                "store": t.get("store"),
                "purchase-id": t.get("purchase-id")
            })

        return jsonify(txs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/kill', methods=['GET'])
def kill_container():
    """
    For grading purposes: Crash the container.
    """
    os._exit(1)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)