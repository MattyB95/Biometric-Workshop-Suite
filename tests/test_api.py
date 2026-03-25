"""Integration tests for the Flask API endpoints."""

import json

import pytest

PHRASE = "the quick brown fox"
N = len(PHRASE)  # 19 characters → 18 flight intervals


def _sample(base_dwell: float = 80.0, base_flight: float = 50.0) -> dict:
    """Return a single timing sample matching the enrollment phrase length."""
    return {
        "dwell": [base_dwell + i * 1.5 for i in range(N)],
        "flight": [base_flight + i for i in range(N - 1)],
    }


def _enroll(client, name: str, n_samples: int = 5) -> None:
    """Helper: enroll `name` with `n_samples` distinct timing samples."""
    samples = [
        _sample(base_dwell=80.0 + j * 2, base_flight=50.0 + j) for j in range(n_samples)
    ]
    resp = client.post(
        "/api/enroll",
        data=json.dumps({"name": name, "samples": samples}),
        content_type="application/json",
    )
    assert resp.status_code == 200


class TestGetProfiles:
    def test_empty_returns_empty_list(self, client):
        resp = client.get("/api/profiles")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["enrolled"] == []
        assert data["phrase"] == PHRASE

    def test_enrolled_name_appears(self, client):
        _enroll(client, "Alice")
        data = client.get("/api/profiles").get_json()
        names = [e["name"] for e in data["enrolled"]]
        assert "Alice" in names

    def test_num_samples_reported(self, client):
        _enroll(client, "Bob", n_samples=5)
        data = client.get("/api/profiles").get_json()
        entry = next(e for e in data["enrolled"] if e["name"] == "Bob")
        assert entry["num_samples"] == 5


class TestGetProfileDetail:
    def test_returns_404_for_unknown(self, client):
        resp = client.get("/api/profiles/Nobody")
        assert resp.status_code == 404

    def test_returns_profile_fields(self, client):
        _enroll(client, "Carol")
        data = client.get("/api/profiles/Carol").get_json()
        for key in (
            "mean_dwell",
            "std_dwell",
            "mean_flight",
            "std_flight",
            "num_samples",
        ):
            assert key in data

    def test_vector_lengths_match_phrase(self, client):
        _enroll(client, "Dave")
        data = client.get("/api/profiles/Dave").get_json()
        assert len(data["mean_dwell"]) == N
        assert len(data["mean_flight"]) == N - 1


class TestEnroll:
    def test_missing_name_returns_400(self, client):
        samples = [_sample()] * 5
        resp = client.post(
            "/api/enroll",
            data=json.dumps({"name": "", "samples": samples}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Name" in resp.get_json()["error"]

    def test_too_few_samples_returns_400(self, client):
        resp = client.post(
            "/api/enroll",
            data=json.dumps({"name": "Eve", "samples": [_sample()] * 3}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "samples" in resp.get_json()["error"].lower()

    def test_success_returns_enrolled_list(self, client):
        samples = [_sample()] * 5
        resp = client.post(
            "/api/enroll",
            data=json.dumps({"name": "Frank", "samples": samples}),
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["success"] is True
        assert "Frank" in data["enrolled"]

    def test_re_enroll_overwrites(self, client):
        _enroll(client, "Grace", n_samples=5)
        _enroll(client, "Grace", n_samples=5)
        data = client.get("/api/profiles").get_json()
        count = sum(1 for e in data["enrolled"] if e["name"] == "Grace")
        assert count == 1


class TestIdentify:
    def test_no_profiles_returns_400(self, client):
        resp = client.post(
            "/api/identify",
            data=json.dumps({"timing": _sample()}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_best_match_returned(self, client):
        _enroll(client, "Heidi")
        _enroll(client, "Ivan")
        resp = client.post(
            "/api/identify",
            data=json.dumps({"timing": _sample()}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "best_match" in data
        assert "top_confidence" in data
        assert "results" in data

    def test_results_sorted_by_distance(self, client):
        _enroll(client, "Judy")
        _enroll(client, "Karl")
        data = client.post(
            "/api/identify",
            data=json.dumps({"timing": _sample()}),
            content_type="application/json",
        ).get_json()
        distances = [r["distance"] for r in data["results"]]
        assert distances == sorted(distances)

    def test_confidence_sums_to_100(self, client):
        _enroll(client, "Laura")
        _enroll(client, "Mallory")
        data = client.post(
            "/api/identify",
            data=json.dumps({"timing": _sample()}),
            content_type="application/json",
        ).get_json()
        total = sum(r["confidence"] for r in data["results"])
        assert abs(total - 100.0) < 0.2  # rounding tolerance

    def test_single_profile_gets_100_confidence(self, client):
        _enroll(client, "Niaj")
        data = client.post(
            "/api/identify",
            data=json.dumps({"timing": _sample()}),
            content_type="application/json",
        ).get_json()
        assert data["top_confidence"] == pytest.approx(100.0)


class TestDeleteProfile:
    def test_delete_removes_profile(self, client):
        _enroll(client, "Oscar")
        client.delete("/api/profiles/Oscar")
        data = client.get("/api/profiles").get_json()
        assert "Oscar" not in [e["name"] for e in data["enrolled"]]

    def test_delete_non_existent_is_idempotent(self, client):
        resp = client.delete("/api/profiles/Ghost")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_delete_returns_updated_enrolled_list(self, client):
        _enroll(client, "Peggy")
        _enroll(client, "Quinn")
        data = client.delete("/api/profiles/Peggy").get_json()
        assert "Peggy" not in data["enrolled"]
        assert "Quinn" in data["enrolled"]


class TestReset:
    def test_reset_clears_all_profiles(self, client):
        _enroll(client, "Romeo")
        _enroll(client, "Sybil")
        client.post("/api/reset", content_type="application/json")
        data = client.get("/api/profiles").get_json()
        assert data["enrolled"] == []

    def test_reset_returns_success(self, client):
        resp = client.post("/api/reset", content_type="application/json")
        assert resp.get_json()["success"] is True
