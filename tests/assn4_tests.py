import pytest
import requests
from test_data import (
    STORE1, STORE2,
    PET_TYPE1, PET_TYPE1_VAL,
    PET_TYPE2, PET_TYPE2_VAL,
    PET_TYPE3, PET_TYPE3_VAL,
    PET_TYPE4, PET_TYPE4_VAL,
    PET1_TYPE1, PET2_TYPE1, PET3_TYPE1, PET4_TYPE2,
    PET5_TYPE3, PET6_TYPE3, PET7_TYPE4, PET8_TYPE4
)

def _post_type(store_base: str, payload: dict) -> tuple[int, dict]:
    r = requests.post(f"{store_base}/pet-types", json=payload, timeout=5)
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
    return body["id"], body


def _assert_family_genus_fields(actual: dict, expected: dict) -> None:
    """Assignment requires family/genus match PET_TYPE*_VAL (not necessarily full dict equality)."""
    assert actual.get("family") == expected["family"]
    assert actual.get("genus") == expected["genus"]


@pytest.fixture(scope="module")
def seeded_ids():
    """Create the 6 pet-types as required and return their ids.

    Important: The assignment wording requires unique ids per store.
    (It does not require the id spaces of store #1 and store #2 to be disjoint.)
    """
    # Store #1
    id1, v1 = _post_type(STORE1, PET_TYPE1)
    id2, v2 = _post_type(STORE1, PET_TYPE2)
    id3, v3 = _post_type(STORE1, PET_TYPE3)

    # Store #2
    id4, v4 = _post_type(STORE2, PET_TYPE1)
    id5, v5 = _post_type(STORE2, PET_TYPE2)
    id6, v6 = _post_type(STORE2, PET_TYPE4)

    # Unique IDs per store
    assert len({id1, id2, id3}) == 3
    assert len({id4, id5, id6}) == 3

    # Validate family/genus (per assignment text)
    _assert_family_genus_fields(v1, PET_TYPE1_VAL)
    _assert_family_genus_fields(v2, PET_TYPE2_VAL)
    _assert_family_genus_fields(v3, PET_TYPE3_VAL)
    _assert_family_genus_fields(v4, PET_TYPE1_VAL)
    _assert_family_genus_fields(v5, PET_TYPE2_VAL)
    _assert_family_genus_fields(v6, PET_TYPE4_VAL)

    return {"id1": id1, "id2": id2, "id3": id3, "id4": id4, "id5": id5, "id6": id6}


def test_pets_creation(seeded_ids):
    ids = seeded_ids

    # Store 1 pets
    for payload in [PET1_TYPE1, PET2_TYPE1]:
        r = requests.post(f"{STORE1}/pet-types/{ids['id1']}/pets", json=payload, timeout=5)
        assert r.status_code == 201

    for payload in [PET5_TYPE3, PET6_TYPE3]:
        r = requests.post(f"{STORE1}/pet-types/{ids['id3']}/pets", json=payload, timeout=5)
        assert r.status_code == 201

    # Store 2 pets
    r = requests.post(f"{STORE2}/pet-types/{ids['id4']}/pets", json=PET3_TYPE1, timeout=5)
    assert r.status_code == 201

    r = requests.post(f"{STORE2}/pet-types/{ids['id5']}/pets", json=PET4_TYPE2, timeout=5)
    assert r.status_code == 201

    for payload in [PET7_TYPE4, PET8_TYPE4]:
        r = requests.post(f"{STORE2}/pet-types/{ids['id6']}/pets", json=payload, timeout=5)
        assert r.status_code == 201


def test_get_pet_type_and_pets(seeded_ids):
    ids = seeded_ids

    # GET pet-type id2 from store #1 (must match PET_TYPE2_VAL on required fields)
    r = requests.get(f"{STORE1}/pet-types/{ids['id2']}", timeout=5)
    assert r.status_code == 200
    body = r.json()
    # At minimum, these must match the assignment's PET_TYPE2_VAL fields
    for k in ["type", "family", "genus", "attributes", "lifespan"]:
        assert body.get(k) == PET_TYPE2_VAL[k]

    # GET pets for type id6 in store #2
    r = requests.get(f"{STORE2}/pet-types/{ids['id6']}/pets", timeout=5)
    assert r.status_code == 200
    pets = r.json()
    assert isinstance(pets, list)

    # Verify pets match PET7_TYPE4 and PET8_TYPE4
    names = {p.get("name") for p in pets}
    assert {"Lazy", "Lemon"}.issubset(names)
    
    # Check birthdates match the payloads
    for pet in pets:
        if pet.get("name") == "Lazy":
            assert pet.get("birthdate") == PET7_TYPE4["birthdate"]
        elif pet.get("name") == "Lemon":
            assert pet.get("birthdate") == PET8_TYPE4["birthdate"]