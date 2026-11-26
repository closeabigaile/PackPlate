"""Saved dietary profiles on accounts (M5), against the test database."""

from sqlalchemy import select

from db.models import DietProfile

WOLF = {"username": "wolf", "password": "howl at the moon"}
FOX = {"username": "fox", "password": "quick brown fox"}

PROFILE = {
    "name": "  Sam ",
    "avoid": ["nuts", "dairy", "nuts"],
    "diets": ["vegetarian"],
    "min_protein_g": 20,
    "max_calories": 800,
    "max_sodium_mg": None,
}


def register(client, creds=WOLF):
    assert client.post("/auth/register", json=creds).status_code == 201


def test_logged_out_is_401(client):
    assert client.get("/profile").status_code == 401
    assert client.put("/profile", json={"avoid": []}).status_code == 401
    assert client.delete("/profile").status_code == 401


def test_no_profile_until_saved(client):
    register(client)
    response = client.get("/profile")
    assert response.status_code == 200
    assert response.json() is None


def test_save_and_read_back(client, db):
    register(client)
    response = client.put("/profile", json=PROFILE)
    assert response.status_code == 200
    expected = {
        "name": "Sam",  # trimmed
        "avoid": ["nuts", "dairy"],  # each once, in order
        "diets": ["vegetarian"],
        "min_protein_g": 20,
        "max_calories": 800,
        "max_sodium_mg": None,
    }
    assert response.json() == expected
    assert client.get("/profile").json() == expected
    assert len(db.scalars(select(DietProfile)).all()) == 1


def test_save_replaces_the_whole_profile(client):
    register(client)
    client.put("/profile", json=PROFILE)
    response = client.put("/profile", json={"avoid": ["egg"]})
    assert response.json() == {
        "name": None,
        "avoid": ["egg"],
        "diets": [],
        "min_protein_g": None,
        "max_calories": None,
        "max_sodium_mg": None,
    }


def test_rejects_what_a_filter_request_would(client):
    register(client)
    assert client.put("/profile", json={"avoid": ["peanut"]}).status_code == 422
    assert client.put("/profile", json={"diets": ["keto"]}).status_code == 422
    assert client.put("/profile", json={"max_calories": -1}).status_code == 422
    assert client.put("/profile", json={"email": "x@y.z"}).status_code == 422
    assert client.put("/profile", json={"name": "x" * 51}).status_code == 422
    assert client.get("/profile").json() is None


def test_saved_profile_works_as_a_filter_profile(client):
    register(client)
    saved = client.put("/profile", json=PROFILE).json()
    # What GET /profile returns can be sent straight back to the filter endpoints.
    assert client.post("/filters/group", json={"profiles": [saved]}).status_code == 200


def test_delete(client, db):
    register(client)
    client.put("/profile", json=PROFILE)
    assert client.delete("/profile").status_code == 204
    assert client.get("/profile").json() is None
    assert client.delete("/profile").status_code == 204  # already gone is fine
    assert db.scalars(select(DietProfile)).all() == []


def test_each_account_sees_only_its_own(client):
    register(client, WOLF)
    client.put("/profile", json=PROFILE)
    client.post("/auth/logout")
    register(client, FOX)
    assert client.get("/profile").json() is None
    client.put("/profile", json={"avoid": ["soy"]})
    client.post("/auth/logout")
    client.post("/auth/login", json=WOLF)
    assert client.get("/profile").json()["avoid"] == ["nuts", "dairy"]


def test_deleting_the_account_deletes_the_profile(client, db):
    register(client)
    client.put("/profile", json=PROFILE)
    response = client.request("DELETE", "/auth/me", json={"password": WOLF["password"]})
    assert response.status_code == 204
    assert db.scalars(select(DietProfile)).all() == []
