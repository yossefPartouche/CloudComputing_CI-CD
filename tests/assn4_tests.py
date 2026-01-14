import requests
import pytest

# ------------------------------------------------------
# Configuration (MANDATED PORTS)
# ------------------------------------------------------
STORE1 = "http://localhost:5001"
STORE2 = "http://localhost:5002"

# ------------------------------------------------------
# PET TYPES
# ------------------------------------------------------
PET_TYPE1 = {"type": "Golden Retriever"}
PET_TYPE1_VAL = {
    "type": "Golden Retriever",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": [],
    "lifespan": 12
}

PET_TYPE2 = {"type": "Australian Shepherd"}
PET_TYPE2_VAL = {
    "type": "Australian Shepherd",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": ["Loyal", "outgoing", "and", "friendly"],
    "lifespan": 15
}

PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE3_VAL = {
    "type": "Abyssinian",
    "family": "Felidae",
    "genus": "Felis",
    "attributes": ["Intelligent", "and", "curious"],
    "lifespan": 13
}

PET_TYPE4 = {"type": "bulldog"}
PET_TYPE4_VAL = {
    "type": "bulldog",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": ["Gentle", "calm", "and", "affectionate"],
    "lifespan": None
}

# ------------------------------------------------------
# PET PAYLOADS
# ------------------------------------------------------
PET1_TYPE1 = {"name": "Lander", "birthdate": "05-14-2020"}
PET2_TYPE1 = {"name": "Lanky"}
PET3_TYPE1 = {"name": "Shelly", "birthdate": "07-07-2019"}
PET4_TYPE2 = {"name": "Felicity", "birthdate": "27-11-2011"}
PET5_TYPE3 = {"name": "Muscles"}
PET6_TYPE3 = {"name": "Junior"}
PET7_TYPE4 = {"name": "Lazy", "birthdate": "07-08-2018"}
PET8_TYPE4 = {"name": "Lemon", "birthdate": "27-03-2020"}

# ------------------------------------------------------
# HELPERS
# ------------------------------------------------------
def post_type(store, payload):
    r = requests.post(f"{store}/pet-types", json=payload)
    assert r.status_code == 201
    body = r.json()
    return body["id"], body

# ------------------------------------------------------
# FIXTURE (shared state)
# ------------------------------------------------------
@pytest.fixture(scope="module")
def pet_type_ids():
    ids = {}

    ids["s1_id1"], v1 = post_type(STORE1, PET_TYPE1)
    ids["s1_id2"], v2 = post_type(STORE1, PET_TYPE2)
    ids["s1_id3"], v3 = post_type(STORE1, PET_TYPE3)

    ids["s2_id1"], v4 = post_type(STORE2, PET_TYPE1)
    ids["s2_id2"], v5 = post_type(STORE2, PET_TYPE2)
    ids["s2_id3"], v6 = post_type(STORE2, PET_TYPE4)

    # IDs unique *per store*
    assert len({ids["s1_id1"], ids["s1_id2"], ids["s1_id3"]}) == 3
    assert len({ids["s2_id1"], ids["s2_id2"], ids["s2_id3"]}) == 3

    # Validate returned payloads
    assert v1 == PET_TYPE1_VAL
    assert v2 == PET_TYPE2_VAL
    assert v3 == PET_TYPE3_VAL
    assert v4 == PET_TYPE1_VAL
    assert v5 == PET_TYPE2_VAL
    assert v6 == PET_TYPE4_VAL

    return ids

# ------------------------------------------------------
# TESTS
# ------------------------------------------------------
def test_pets_creation(pet_type_ids):
    # Store 1
    for payload in [PET1_TYPE1, PET2_TYPE1]:
        r = requests.post(
            f"{STORE1}/pet-types/{pet_type_ids['s1_id1']}/pets",
            json=payload
        )
        assert r.status_code == 201

    for payload in [PET5_TYPE3, PET6_TYPE3]:
        r = requests.post(
            f"{STORE1}/pet-types/{pet_type_ids['s1_id3']}/pets",
            json=payload
        )
        assert r.status_code == 201

    # Store 2
    r = requests.post(
        f"{STORE2}/pet-types/{pet_type_ids['s2_id1']}/pets",
        json=PET3_TYPE1
    )
    assert r.status_code == 201

    r = requests.post(
        f"{STORE2}/pet-types/{pet_type_ids['s2_id2']}/pets",
        json=PET4_TYPE2
    )
    assert r.status_code == 201

    for payload in [PET7_TYPE4, PET8_TYPE4]:
        r = requests.post(
            f"{STORE2}/pet-types/{pet_type_ids['s2_id3']}/pets",
            json=payload
        )
        assert r.status_code == 201

def test_get_pet_type_and_pets(pet_type_ids):
    r = requests.get(
        f"{STORE1}/pet-types/{pet_type_ids['s1_id2']}"
    )
    assert r.status_code == 200
    assert r.json() == PET_TYPE2_VAL

    r = requests.get(
        f"{STORE2}/pet-types/{pet_type_ids['s2_id3']}/pets"
    )
    assert r.status_code == 200

    names = {p["name"] for p in r.json()}
    assert names == {"Lazy", "Lemon"}