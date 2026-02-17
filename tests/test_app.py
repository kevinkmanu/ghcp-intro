"""
Tests for the Mergington High School API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset in-memory activities database before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture()
def client():
    return TestClient(app)


# ── GET / ────────────────────────────────────────────────────────────────────


class TestRoot:
    def test_root_redirects_to_static(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ── GET /activities ──────────────────────────────────────────────────────────


class TestGetActivities:
    def test_returns_all_activities(self, client):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Soccer Team" in data
        assert "Chess Club" in data

    def test_activity_has_expected_fields(self, client):
        response = client.get("/activities")
        data = response.json()
        for name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


# ── POST /activities/{name}/signup ───────────────────────────────────────────


class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Soccer Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

        # Verify participant was added
        act = client.get("/activities").json()
        assert "newstudent@mergington.edu" in act["Soccer Team"]["participants"]

    def test_signup_duplicate_rejected(self, client):
        """A student already in the list should get a 400."""
        response = client.post(
            "/activities/Soccer Team/signup?email=liam@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_twice_same_student(self, client):
        """Signing up the same student twice should fail the second time."""
        email = "twice@mergington.edu"
        r1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert r1.status_code == 200

        r2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert r2.status_code == 400


# ── DELETE /activities/{name}/unregister ─────────────────────────────────────


class TestUnregister:
    def test_unregister_success(self, client):
        response = client.delete(
            "/activities/Soccer Team/unregister?email=liam@mergington.edu"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

        # Verify participant was removed
        act = client.get("/activities").json()
        assert "liam@mergington.edu" not in act["Soccer Team"]["participants"]

    def test_unregister_not_registered(self, client):
        response = client.delete(
            "/activities/Soccer Team/unregister?email=unknown@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity(self, client):
        response = client.delete(
            "/activities/Fake Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_signup_then_unregister(self, client):
        """Full round-trip: sign up, verify, unregister, verify."""
        email = "roundtrip@mergington.edu"
        activity = "Drama Club"

        # Sign up
        r = client.post(f"/activities/{activity}/signup?email={email}")
        assert r.status_code == 200

        act = client.get("/activities").json()
        assert email in act[activity]["participants"]

        # Unregister
        r = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert r.status_code == 200

        act = client.get("/activities").json()
        assert email not in act[activity]["participants"]
