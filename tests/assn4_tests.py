import pytest
import requests
import time

STORE1 = "http://localhost:5001"
STORE2 = "http://localhost:5002"

# ---------------- PET TYPES ----------------
PET_TYPE1 = {"type": "Golden Retriever"}
PET_TYPE2 = {"type": "Australian Shepherd"}
PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE4 = {"type": "bulldog"}

PET_TYPE1_VAL = {
    "type": "Golden Retriever",
    "family": "Canidae",
    "genus": "Canis",
    "attribute": [],
    "lifespan": 12,
}

PET_TYPE2_VAL = {
    "type": "Australian Shepherd",
    "family": "Canidae",
    "genus": "Canis",
    "attribute": ["Loyal", "outgoing", "and", "friendly"],
    "lifespan": 15,
}

PET_TYPE3_VAL = {
    "type": "Abyssinian",
    "family": "Felidae",
    "genus": "Felis",
    "attribute": ["Intelligent", "and", "curious"],
    "lifespan": 13,
}

PET_TYPE4_VAL = {
    "type": "bulldog",
    "family": "Canidae",
    "genus": "Canis",
    "attribute": ["Gentle", "calm", "and", "affectionate"],
    "lifespan": None,
}

# ---------------- PET PAYLOADS (ISO dates) ----------------
PET1_TYPE1 = {"name": "Lander", "birthdate": "2020-05-14"}
PET2_TYPE1 = {"name": "Lanky"}
PET3_TYPE1 = {"name": "Shelly", "birthdate": "2019-07-07"}
PET4_TYPE2 = {"name": "Felicity", "birthdate": "2011-11-27"}
PET5_TYPE3 = {"name": "Muscles"}
PET6_TYPE3 = {"name": "Junior"}
PET7_TYPE4 = {"name": "Lazy", "birthdate": "2018-08-07"}
PET8_TYPE4 = {"name": "Lemon", "birthdate": "2020-03-27"}


def _post_type(store, payload):
    r = requests.post(f"{store}/pet-types", json=payload, timeout=10)
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
    return body["id"], body


@pytest.fixture(scope="module")
def seeded_ids():
    # Give containers time in CI
    time.sleep(3)

    id1, v1 = _post_type(STORE1, PET_TYPE1)
    id2, v2 = _post_type(STORE1, PET_TYPE2)
    id3, v3 = _post_type(STORE1, PET_TYPE3)

    id4, v4 = _post_type(STORE2, PET_TYPE1)
    id5, v5 = _post_type(STORE2, PET_TYPE2)
    id6, v6 = _post_type(STORE2, PET_TYPE4)

    assert len({id1, id2, id3}) == 3
    assert len({id4, id5, id6}) == 3

    for actual, expected in [
        (v1, PET_TYPE1_VAL),
        (v2, PET_TYPE2_VAL),
        (v3, PET_TYPE3_VAL),
        (v4, PET_TYPE1_VAL),
        (v5, PET_TYPE2_VAL),
        (v6, PET_TYPE4_VAL),
    ]:
        assert actual["family"] == expected["family"]
        assert actual["genus"] == expected["genus"]

    return {
        "id1": id1, "id2": id2, "id3": id3,
        "id4": id4, "id5": id5, "id6": id6,
    }


def test_pets_creation(seeded_ids):
    ids = seeded_ids

    for p in [PET1_TYPE1, PET2_TYPE1]:
        assert requests.post(
            f"{STORE1}/pet-types/{ids['id1']}/pets", json=p, timeout=10
        ).status_code == 201

    for p in [PET5_TYPE3, PET6_TYPE3]:
        assert requests.post(
            f"{STORE1}/pet-types/{ids['id3']}/pets", json=p, timeout=10
        ).status_code == 201

    assert requests.post(
        f"{STORE2}/pet-types/{ids['id4']}/pets", json=PET3_TYPE1, timeout=10
    ).status_code == 201

    assert requests.post(
        f"{STORE2}/pet-types/{ids['id5']}/pets", json=PET4_TYPE2, timeout=10
    ).status_code == 201

    for p in [PET7_TYPE4, PET8_TYPE4]:
        assert requests.post(
            f"{STORE2}/pet-types/{ids['id6']}/pets", json=p, timeout=10
        ).status_code == 201


def test_get_pet_type_and_pets(seeded_ids):
    ids = seeded_ids

    r = requests.get(f"{STORE1}/pet-types/{ids['id2']}", timeout=10)
    assert r.status_code == 200
    body = r.json()

    for k in ["type", "family", "genus", "attribute", "lifespan"]:
        assert body.get(k) == PET_TYPE2_VAL[k]

    r = requests.get(f"{STORE2}/pet-types/{ids['id6']}/pets", timeout=10)
    assert r.status_code == 200

    names = {p["name"] for p in r.json()}
    assert {"Lazy", "Lemon"} <= names