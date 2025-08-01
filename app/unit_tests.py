import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from api_endpoints import app, get_db
import models_sqlalchemy as models
import models_pydantic as schemas

from unittest.mock import patch

# ---------- TEST FIXTURES ----------

# Use in-memory SQLite for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(bind=engine)
    yield engine
    models.Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine):
    """A new DB session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Override get_db dependency for FastAPI TestClient."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# ---------- MOCK EXTERNAL LLM CALLS ----------

@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    # Patch setup_llm_client and get_completion
    monkeypatch.setattr("api_endpoints.setup_llm_client", lambda model_name: (None, "mock-model", "mock-provider"))
    # Patch get_completion to always return '[1,2]'
    monkeypatch.setattr("api_endpoints.get_completion", lambda *a, **k: "[1,2]")
    monkeypatch.setattr("api_endpoints.clean_llm_output", lambda s, fmt: s)

# ---------- TEST DATA HELPERS ----------

def create_user_dict(name="Alice", email="alice@example.com", interests=None):
    return {
        "name": name,
        "email": email,
        "interests": interests or ["hiking", "food"]
    }

def create_property_dict(name="Cozy Cabin", address_line1="123 Main St", city="Denver", state="CO", amenities=None):
    return {
        "name": name,
        "address_line1": address_line1,
        "address_line2": "",
        "city": city,
        "state": state,
        "zip_code": "80202",
        "country": "USA",
        "price_per_night": 100.0,
        "amenities": amenities or ["wifi", "kitchen"]
    }

def create_reservation_dict(user_id, property_id, check_in, check_out):
    return {
        "user_id": user_id,
        "property_id": property_id,
        "check_in_date": check_in,
        "check_out_date": check_out
    }

# ---------- HAPPY PATH TESTS ----------

def test_create_and_get_user(client):
    data = create_user_dict()
    r = client.post("/users/", json=data)
    assert r.status_code == 201
    user = r.json()
    assert user["name"] == data["name"]
    assert user["email"] == data["email"]
    assert set(user["interests"]) == set(data["interests"])

    # Get user by id
    r2 = client.get(f"/users/{user['id']}")
    assert r2.status_code == 200
    assert r2.json() == user

def test_list_users(client):
    # Add two users
    client.post("/users/", json=create_user_dict(name="A", email="a@e.com"))
    client.post("/users/", json=create_user_dict(name="B", email="b@e.com"))
    r = client.get("/users/")
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_update_user(client):
    data = create_user_dict()
    r = client.post("/users/", json=data)
    user_id = r.json()["id"]
    update = {"name": "New Name", "interests": ["surfing"]}
    r2 = client.put(f"/users/{user_id}", json=update)
    assert r2.status_code == 200
    assert r2.json()["name"] == "New Name"
    assert r2.json()["interests"] == ["surfing"]

def test_delete_user(client):
    r = client.post("/users/", json=create_user_dict())
    user_id = r.json()["id"]
    r2 = client.delete(f"/users/{user_id}")
    assert r2.status_code == 204
    # Now should be 404
    r3 = client.get(f"/users/{user_id}")
    assert r3.status_code == 404

def test_create_and_get_property(client):
    data = create_property_dict()
    r = client.post("/properties/", json=data)
    assert r.status_code == 201
    prop = r.json()
    for key in ["name", "city", "state"]:
        assert prop[key] == data[key]
    assert set(prop["amenities"]) == set(data["amenities"])

    # Get property by id
    r2 = client.get(f"/properties/{prop['id']}")
    assert r2.status_code == 200
    assert r2.json() == prop

def test_list_properties(client):
    client.post("/properties/", json=create_property_dict(name="A", city="X"))
    client.post("/properties/", json=create_property_dict(name="B", city="Y"))
    r = client.get("/properties/")
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_update_property(client):
    r = client.post("/properties/", json=create_property_dict())
    prop_id = r.json()["id"]
    update = {"name": "Villa", "amenities": ["pool"]}
    r2 = client.put(f"/properties/{prop_id}", json=update)
    assert r2.status_code == 200
    assert r2.json()["name"] == "Villa"
    assert r2.json()["amenities"] == ["pool"]

def test_delete_property(client):
    r = client.post("/properties/", json=create_property_dict())
    prop_id = r.json()["id"]
    r2 = client.delete(f"/properties/{prop_id}")
    assert r2.status_code == 204
    r3 = client.get(f"/properties/{prop_id}")
    assert r3.status_code == 404

def test_create_and_get_reservation(client):
    # Need a user and property first
    u = client.post("/users/", json=create_user_dict())
    p = client.post("/properties/", json=create_property_dict())
    uid = u.json()["id"]
    pid = p.json()["id"]
    data = create_reservation_dict(uid, pid, "2025-01-01", "2025-01-05")
    r = client.post("/reservations/", json=data)
    assert r.status_code == 201
    res = r.json()
    assert res["user_id"] == uid
    assert res["property_id"] == pid
    assert res["check_in_date"] == "2025-01-01"
    # Get reservation
    r2 = client.get(f"/reservations/{res['id']}")
    assert r2.status_code == 200
    assert r2.json()["id"] == res["id"]

def test_list_reservations(client):
    u = client.post("/users/", json=create_user_dict())
    p = client.post("/properties/", json=create_property_dict())
    uid = u.json()["id"]
    pid = p.json()["id"]
    d1 = create_reservation_dict(uid, pid, "2025-01-01", "2025-01-05")
    d2 = create_reservation_dict(uid, pid, "2025-02-01", "2025-02-05")
    client.post("/reservations/", json=d1)
    client.post("/reservations/", json=d2)
    r = client.get("/reservations/")
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_update_reservation(client):
    u = client.post("/users/", json=create_user_dict())
    p = client.post("/properties/", json=create_property_dict())
    uid = u.json()["id"]
    pid = p.json()["id"]
    data = create_reservation_dict(uid, pid, "2025-01-01", "2025-01-05")
    res_id = client.post("/reservations/", json=data).json()["id"]
    update = {"check_in_date": "2025-01-03", "check_out_date": "2025-01-08"}
    r2 = client.put(f"/reservations/{res_id}", json=update)
    assert r2.status_code == 200
    assert r2.json()["check_in_date"] == "2025-01-03"

def test_delete_reservation(client):
    u = client.post("/users/", json=create_user_dict())
    p = client.post("/properties/", json=create_property_dict())
    uid = u.json()["id"]
    pid = p.json()["id"]
    data = create_reservation_dict(uid, pid, "2025-01-01", "2025-01-05")
    res_id = client.post("/reservations/", json=data).json()["id"]
    r2 = client.delete(f"/reservations/{res_id}")
    assert r2.status_code == 204
    r3 = client.get(f"/reservations/{res_id}")
    assert r3.status_code == 404

def test_user_properties_llm_recommendation(client):
    # Two properties, one user
    p1 = client.post("/properties/", json=create_property_dict(name="A", amenities=["wifi"]))
    p2 = client.post("/properties/", json=create_property_dict(name="B", amenities=["kitchen"]))
    u = client.post("/users/", json=create_user_dict(interests=["wifi", "kitchen"]))
    uid = u.json()["id"]
    r = client.get(f"/users/{uid}/properties")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    # Because mock_llm returns [1,2], check those property ids returned
    prop_ids = [prop["id"] for prop in r.json()]
    assert set(prop_ids).issubset({p1.json()["id"], p2.json()["id"]})

# ---------- EDGE CASE TESTS ----------

def test_create_user_duplicate_email(client):
    data = create_user_dict(email="x@y.com")
    client.post("/users/", json=data)
    r2 = client.post("/users/", json=data)
    assert r2.status_code == 400
    assert "Email already registered" in r2.text

def test_update_user_duplicate_email(client):
    # Two users, update one to other's email
    u1 = client.post("/users/", json=create_user_dict(email="a@x.com"))
    u2 = client.post("/users/", json=create_user_dict(email="b@x.com"))
    r = client.put(f"/users/{u2.json()['id']}", json={"email": "a@x.com"})
    assert r.status_code == 400
    assert "Email already registered" in r.text

def test_get_nonexistent_user(client):
    r = client.get("/users/999")
    assert r.status_code == 404

def test_update_nonexistent_user(client):
    r = client.put("/users/999", json={"name": "foo"})
    assert r.status_code == 404

def test_delete_nonexistent_user(client):
    r = client.delete("/users/999")
    assert r.status_code == 404

def test_get_nonexistent_property(client):
    r = client.get("/properties/999")
    assert r.status_code == 404

def test_update_nonexistent_property(client):
    r = client.put("/properties/999", json={"name": "foo"})
    assert r.status_code == 404

def test_delete_nonexistent_property(client):
    r = client.delete("/properties/999")
    assert r.status_code == 404

def test_create_reservation_invalid_user_or_property(client):
    u = client.post("/users/", json=create_user_dict())
    # Invalid property
    data = create_reservation_dict(u.json()["id"], 999, "2025-01-01", "2025-01-05")
    r = client.post("/reservations/", json=data)
    assert r.status_code == 400
    # Invalid user
    p = client.post("/properties/", json=create_property_dict())
    data2 = create_reservation_dict(999, p.json()["id"], "2025-01-01", "2025-01-05")
    r2 = client.post("/reservations/", json=data2)
    assert r2.status_code == 400

def test_create_reservation_check_out_before_check_in(client):
    u = client.post("/users/", json=create_user_dict())
    p = client.post("/properties/", json=create_property_dict())
    data = create_reservation_dict(u.json()["id"], p.json()["id"], "2025-01-05", "2025-01-01")
    r = client.post("/reservations/", json=data)
    assert r.status_code == 400
    assert "check_out_date" in r.text

def test_update_reservation_nonexistent(client):
    r = client.put("/reservations/999", json={"check_in_date": "2025-01-01"})
    assert r.status_code == 404

def test_delete_reservation_nonexistent(client):
    r = client.delete("/reservations/999")
    assert r.status_code == 404

def test_update_reservation_invalid_user_or_property(client):
    u = client.post("/users/", json=create_user_dict())
    p = client.post("/properties/", json=create_property_dict())
    data = create_reservation_dict(u.json()["id"], p.json()["id"], "2025-01-01", "2025-01-05")
    res_id = client.post("/reservations/", json=data).json()["id"]
    # Invalid user
    r = client.put(f"/reservations/{res_id}", json={"user_id": 999})
    assert r.status_code == 400
    # Invalid property
    r2 = client.put(f"/reservations/{res_id}", json={"property_id": 999})
    assert r2.status_code == 400

def test_update_reservation_check_out_before_check_in(client):
    u = client.post("/users/", json=create_user_dict())
    p = client.post("/properties/", json=create_property_dict())
    data = create_reservation_dict(u.json()["id"], p.json()["id"], "2025-01-01", "2025-01-05")
    res_id = client.post("/reservations/", json=data).json()["id"]
    # Swap dates (invalid)
    r = client.put(f"/reservations/{res_id}", json={"check_in_date": "2025-01-10", "check_out_date": "2025-01-05"})
    assert r.status_code == 400
    assert "check_out_date" in r.text

def test_user_properties_nonexistent_user(client):
    r = client.get("/users/999/properties")
    assert r.status_code == 404
    assert "User not found" in r.text

# ---------- END OF TEST SUITE ----------