from flask import Flask, jsonify, request, make_response, send_from_directory
from pymongo import MongoClient
import requests
import uuid
import re 
import os
from datetime import datetime

"""
------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------
JSON for pet-type  -------------------> Example pet-type
{                                       {
“id”: string,                           “id”: “2”,
“type”: string,                         “type”: “Poodle” ,
“family”: string,                       “family”: “Canidae”,
“genus”: string,                        “genus”: “Canis”,
“attributes”: array (of string),        “attribute ”: [“Intelligent”, “alert”,“active”],
“lifespan”: int,                        “lifespan”: 16,
“pets”: array (of string)               “pets”: [“Tony”, “Lian”, “Jamie”]
// attributes may be empty.             }
// lifespan may be null.
}
------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------
JSON for a pet  ------------------->    Example pet
{                                       {
“name”: string,                         “name”: “Jamie” ,
“birthdate”: string,                    “birthdate”: “24-10-2023”,
“picture”: string // name of file       “picture”: “Jamie-poodle.jpg”
// storing the image                    }
// birthdate & picture may have
// the value “NA”
}
------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------
"""

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongo-store:27017")
STORE_ID = os.environ.get("STORE_ID", "1") # Default to 1

client = MongoClient(MONGO_URI)
db = client.petstore

pet_types_col = db[f"pet_types_store{STORE_ID}"]
pets_col = db[f"pets_store{STORE_ID}"]

IMAGES_DIR = "pet_images"
os.makedirs(IMAGES_DIR, exist_ok=True)

app = Flask(__name__)

#---------------------HELPERS-----------------------
def get_petInfo(petType):
    """
    Helper function to get pet information from the API-Ninjas API.
    """
    api_key = os.environ.get("NINJA_API_KEY")
    url = f"https://api.api-ninjas.com/v1/animals?name={petType}"
    headers = {"X-Api-Key": api_key}
    r = requests.get(url, headers=headers)
    return r.json()

def find_exact_animal(data, target):
    """
    Helper function to find an exact animal in the data.
    """
    target = target.strip()
    for animal in data:
        if animal.get("name") == target:
            return animal
    return None

def get_lifespan(value):
    """
    Helper function to get the lifespan of an animal.
    """
    if not value:
        return None
    # Extract all numbers from the string
    numbers = re.findall(r"\d+", value)
    if not numbers:
        return None
    # Convert all numbers to integers
    numbers = list(map(int, numbers))
    # Always return the minimum number
    return min(numbers)
#--------------------------ROUTES----------------
@app.route('/kill', methods=['GET'])
def kill_container():
    os._exit(1)

@app.route('/pet-types', methods=['POST'])
def add_pet_type():
    try:
        content_type = request.headers.get('Content-Type')
        if content_type != 'application/json':
            return jsonify({"error": "Expected application/json"}), 415
        
        post_data = request.get_json() or {}
        raw_type = post_data.get("type")
        if not raw_type:
            return jsonify({"error": "Missing 'type' field in JSON"}), 400

        # Normalise type for storage / lookup
        animal_type = raw_type.title()
        
        if pet_types_col.find_one({"type": animal_type}):
            return jsonify({"error": f"{animal_type} already exists"}), 400
        
        api_data = get_petInfo(animal_type)
        animal = find_exact_animal(api_data, animal_type)
        
        if not animal:
            return jsonify({"error": "Not found"}), 400
        
        taxonomy = animal.get("taxonomy") or {}
        characteristics = animal.get("characteristics") or {}

        temperament = characteristics.get("temperament") or ""
        group_behavior = characteristics.get("group_behavior") or ""
        attribute_val = temperament or group_behavior


        if attribute_val:
            attribute = [x.strip() for x in re.split(r'[,]', attribute_val) if x.strip()]
        else: 
            attribute = []


        # Find current max numeric id and increment (per-store collection)
        last = pet_types_col.find_one(sort=[("id", -1)])
        next_id = (last["id"] + 1) if last and "id" in last else 1

        pet_type_doc = {
            "id": next_id,  # simple integer ID exposed via API
            "type": animal_type,
            "family": taxonomy.get("family", "NA"),
            "genus": taxonomy.get("genus", "NA"),
            "lifespan": get_lifespan(characteristics.get("lifespan", None)),
            "attribute": attribute,
            "pets": []
        }

        pet_types_col.insert_one(pet_type_doc)

        # Clean response: do not expose Mongo _id, just our numeric id
        response_doc = {
            "id": pet_type_doc["id"],
            "type": pet_type_doc["type"],
            "family": pet_type_doc["family"],
            "genus": pet_type_doc["genus"],
            "lifespan": pet_type_doc["lifespan"],
            "attribute": pet_type_doc["attribute"],
            "pets": pet_type_doc["pets"],
        }
        return jsonify(response_doc), 201
    except Exception as e: 
        return jsonify({"server error": str(e)}), 500
    
@app.route('/pet-types/<string:id>/pets', methods=['POST'])
def add_pet(id):
    # id in path is our numeric pet-type id (per-store)
    try:
        type_id = int(id)
    except ValueError:
        return jsonify({"error": "Pet type not found"}), 404

    pet_type = pet_types_col.find_one({"id": type_id})
    if not pet_type:
        return jsonify({"error": "Pet type not found"}), 404
    
    if request.content_type != 'application/json':
        return jsonify({"error": "Unsupported Media Type"}), 415
    
    data = request.get_json()
    name = data.get("name")

    birthdate = data.get("birthdate") or "NA"
    pic_url = data.get('picture-url')

    if not name: 
        return jsonify({"Error": "name field is required"}), 400
    
    if pets_col.find_one({"type_id" : type_id, "name" : name}):
        return jsonify({"error": "Pet exists"}), 400
    
    filename = "NA"
    if pic_url:
        try:
            image = requests.get(pic_url)
            if image.status_code == 200:
                filename = f"{id}_{name}.jpg"
                os.makedirs(IMAGES_DIR, exist_ok=True)
                filepath = os.path.join(IMAGES_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(image.content)
            else:
                return jsonify({"error": "Invalid picture URL"}), 400
        except requests.exceptions.RequestException:
            return jsonify({"error": "Invalid URL format or connection failed"}), 400
    
    new_pet = {
        "_id" : f"{type_id}_{name}", 
        "type_id" : type_id,
        "name" : name,
        "birthdate" : birthdate,
        "picture" : filename
    }
    pets_col.insert_one(new_pet)
    pet_types_col.update_one({"id": type_id}, {"$push": {"pets": name}})

    #Return only clean fields, no Mongo ID
    response_payload = {
        "name": new_pet["name"],
        "birthdate": new_pet["birthdate"],
        "picture": new_pet["picture"]
    }

    return jsonify(response_payload), 201

@app.route('/pet-types', methods=['GET'])
def get_pet_by():
    """
    Return a list of pet types.
    """
    query = {}
    pet_id = request.args.get("id")
    type_name = request.args.get("type")
    family = request.args.get('family')
    genus = request.args.get('genus')
    lifespan = request.args.get('lifespan')
    attribute = request.args.get('hasAttribute')

    try:
        if pet_id:
            try:
                query["id"] = int(pet_id)
            except ValueError:
                return jsonify({"error": "Invalid id"}), 400
        if type_name: query["type"] = type_name.title()
        if family: query["family"] = family.title()
        if genus:  query["genus"] = genus.title()
        if lifespan: query["lifespan"] = int(lifespan)
        if attribute:
            #Searches for attributes in the list
            query["attribute"] = {"$regex": f"^{attribute}", "$options": "i"}

        results = list(pet_types_col.find(query))
        clean_results = []
        for doc in results:
            # Build a clean object without internal _id
            clean_doc = {k: v for k, v in doc.items() if k != "_id"}
            clean_results.append(clean_doc)

        return jsonify(clean_results), 200
    
    except Exception as e: 
        return jsonify({"server error":str(e)}), 500
    
  
@app.route('/pet-types/<string:id>', methods=['GET'])
def get_pet_type(id):
    """
    Return a pet type.
    """
    try:
        type_id = int(id)
    except ValueError:
        return jsonify({"error": "Not found"}), 404

    try:
        pet = pet_types_col.find_one({"id": type_id})
        if not pet:
            return jsonify({"error": "Not found"}), 404

        clean_pet = {k: v for k, v in pet.items() if k != "_id"}
        return jsonify(clean_pet), 200
    except Exception as e:
        return jsonify({"server error": str(e)}), 500
    

@app.route('/pet-types/<string:id>/pets', methods=['GET'])
def get_pet_date(id):
    """
    Return a list of pets.
    """
    try:
        type_id = int(id)
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 404

    #Validate Pet Type exists using the INTEGER ID and "id" field
    if not pet_types_col.find_one({"id": type_id}): 
        return jsonify({"error": "Pet type not found"}), 404

    # Retrieve pets
    pets = list(pets_col.find({"type_id": type_id}))

    # Handle Filters (Date logic remains the same)
    dateGT = request.args.get('birthdateGT')
    dateLT = request.args.get('birthdateLT')

    def parse_date(s):
        try:
            return datetime.strptime(s, "%d-%m-%Y").timestamp()
        except Exception:
            return None

    dGT = parse_date(dateGT) if dateGT else None
    dLT = parse_date(dateLT) if dateLT else None

    # Validate date format in query params
    if (dateGT and dGT is None) or (dateLT and dLT is None):
        return jsonify({"error": "Date must be in DD-MM-YYYY format"}), 400

    results = []

    for pet in pets:
        # Create the cleaned object
        pet_obj = {
            "name": pet.get("name"),
            "birthdate": pet.get("birthdate"),
            "picture": pet.get("picture")
        }

        # If no filters, add everyone
        if not dateGT and not dateLT:
            results.append(pet_obj)
            continue

        # Filter Logic
        birthdate = pet.get("birthdate")
        if not birthdate or birthdate == "NA":
            continue # Skip pets with no birthdate if filtering is active

        try:
            pet_ts = datetime.strptime(birthdate, "%d-%m-%Y").timestamp()
        except ValueError:
            continue

        if dGT is not None and not (pet_ts > dGT):
            continue
        if dLT is not None and not (pet_ts < dLT):
            continue

        results.append(pet_obj)

    #  Return 200 (even if list is empty)
    return jsonify(results), 200


@app.route('/pet-types/<string:id>/pets/<string:name>', methods=['GET'])
def get_pet_by_name(id, name):
    """
    Return a pet by name.
    """
    try:
        type_id = int(id)
    except ValueError:
        return jsonify({"error": "Invalid ID"}), 404


    if not pet_types_col.find_one({"id": type_id}):
        return jsonify({"error": "Pet type ID not found"}), 404
    
    pet_data = pets_col.find_one({"type_id": type_id, "name": name})
    if not pet_data:
        return jsonify({"error": "Pet name not found"}), 404
    
    clean_response = {
        "name": pet_data["name"],
        "birthdate": pet_data["birthdate"],
        "picture": pet_data["picture"]
    }

    return jsonify(clean_response), 200



@app.route('/pictures/<string:filename>', methods=['GET'])
def get_picture(filename):
    """
    Return a picture.
    """
    full_path = os.path.join(IMAGES_DIR, filename)

    if not os.path.exists(full_path):
        return jsonify({"error" : "Picture not found"}), 404
    
    return send_from_directory(IMAGES_DIR, filename)


@app.route('/pet-types/<string:id>/pets/<string:name>', methods=['PUT'])
def update_pet(id, name):
    try:
        type_id = int(id)
    except ValueError:
        return jsonify({"error": "Invalid ID"}), 404

    if not pet_types_col.find_one({"id": type_id}):
        return jsonify({"error" : "Pet type ID not found"}), 404
    
    current_pet_data = pets_col.find_one({"type_id": type_id, "name": name})
    if not current_pet_data:
        return jsonify({"error" : "Pet name not found"}), 404
    
    if request.content_type != 'application/json':
        return jsonify({"error": "Unsupported Media Type"}), 415
    
    data = request.get_json()

    new_name = data.get("name")
    if not new_name:
        return jsonify({"error" : "Name field required"}), 400
    
    new_birthdate = data.get("birthdate", "NA")
    new_pic_url = data.get("picture-url")

    old_filename = current_pet_data.get("picture")
    new_filename = "NA"

    if new_pic_url:
        try:
            response = requests.get(new_pic_url)
            if response.status_code == 200:
                # Delete the OLD image if it exists
                if old_filename and old_filename != "NA":
                    old_path = os.path.join(IMAGES_DIR, old_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                new_filename = f"{id}_{new_name}.jpg"
                new_path = os.path.join(IMAGES_DIR, new_filename)
                with open(new_path, "wb") as f:
                    f.write(response.content)
                
            else:
                return jsonify({"error": "Invalid picture URL"}), 400
        except:
             return jsonify({"error": "Could not connect to picture URL"}), 400
    else:
        if old_filename and old_filename != "NA":
             old_path = os.path.join(IMAGES_DIR, old_filename)
             if os.path.exists(old_path):
                 os.remove(old_path)
        new_filename = "NA"

    new_pet_doc = {
        "_id": f"{type_id}_{new_name}", 
        "type_id": type_id,
        "name": new_name,
        "birthdate": new_birthdate,
        "picture": new_filename
    }
    
    try:
        if new_name != name:
            # Check if new name already exists to avoid overwriting/duplicates
            if pets_col.find_one({"type_id": type_id, "name": new_name}):
                 return jsonify({"error": "Pet with new name already exists"}), 400

            pets_col.insert_one(new_pet_doc)
            pets_col.delete_one({"_id": current_pet_data["_id"]})
            
            pet_types_col.update_one({"id": type_id}, {"$pull": {"pets": name}})
            pet_types_col.update_one({"id": type_id}, {"$push": {"pets": new_name}})
        else:
            pets_col.update_one(
                    {"_id": current_pet_data["_id"]},
                    {"$set": {
                        "birthdate": new_birthdate,
                        "picture": new_filename
                    }}
                )
        
        response_json = {
                "name": new_name,
                "birthdate": new_birthdate,
                "picture": new_filename
        }
        return jsonify(response_json), 200
    
    except Exception as e:
        return jsonify({"error": f"Database update failed: {str(e)}"}), 500
    

@app.route('/pet-types/<string:id>', methods=['DELETE'])
def delete_pet(id):
    """
    Delete a pet type.
    """
    try:
        type_id = int(id)
    except ValueError:
        return jsonify({"error": "Invalid ID"}), 404

    pet = pet_types_col.find_one({"id": type_id})
    if not pet:
        return jsonify({"error": "Not found"}), 404
    
    if pet.get("pets") and len(pet["pets"]) > 0:
        return jsonify({"error": "Still has pets"}), 400
    
    pet_types_col.delete_one({"id": type_id})
    return "", 204

@app.route('/pet-types/<string:id>/pets/<string:name>', methods=['DELETE'])
def delete_pet_name(id, name):
    """
    Delete a pet by name.
    """
    try:
        type_id = int(id)
    except ValueError:
        return jsonify({"error": "Invalid ID"}), 404

    if not pet_types_col.find_one({"id": type_id}):
        return jsonify({"error": "Pet type ID not found"}), 404
    
    pet = pets_col.find_one({"type_id": type_id, "name": name})
    if not pet:
        return jsonify({"error": "Pet name not found"}), 404
    
    if pet.get("picture") and pet.get("picture") != "NA":
        path = os.path.join(IMAGES_DIR, pet["picture"])
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    pets_col.delete_one({"_id": pet["_id"]})
    
    pet_types_col.update_one(
        {"id": type_id},
        {"$pull": {"pets": name}}
    )
    return "", 204
    
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
        
    