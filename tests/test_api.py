"""Integration tests for the Flask API endpoints."""

import json

import pytest

from src.app import DEFAULT_ADMIN_PIN

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
    def test_non_dict_body_returns_400(self, client):
        resp = client.post(
            "/api/identify",
            data=json.dumps([1, 2, 3]),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "object" in resp.get_json()["error"].lower()

    def test_missing_timing_returns_400(self, client):
        resp = client.post(
            "/api/identify",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "timing" in resp.get_json()["error"].lower()

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


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------


class TestPageRoutes:
    def test_home_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_keystroke_returns_200(self, client):
        assert client.get("/keystroke").status_code == 200

    def test_face_returns_200(self, client):
        assert client.get("/face").status_code == 200

    def test_voice_returns_200(self, client):
        assert client.get("/voice").status_code == 200

    def test_signature_returns_200(self, client):
        assert client.get("/signature").status_code == 200

    def test_mouse_returns_200(self, client):
        assert client.get("/mouse").status_code == 200

    def test_admin_returns_200(self, client):
        assert client.get("/admin").status_code == 200


# ---------------------------------------------------------------------------
# Mouse dynamics API helpers
# ---------------------------------------------------------------------------

N_SEG = 7
N_TGT = 8


def _mouse_sample(
    base_time: float = 300.0, base_dwell: float = 80.0, base_curve: float = 0.1
) -> dict:
    return {
        "movement_times": [base_time + i * 5 for i in range(N_SEG)],
        "click_dwells": [base_dwell + i * 2 for i in range(N_TGT)],
        "curvatures": [base_curve + i * 0.005 for i in range(N_SEG)],
    }


def _mouse_enroll(client, name: str, n_samples: int = 5) -> None:
    samples = [_mouse_sample(base_time=300.0 + j * 10) for j in range(n_samples)]
    resp = client.post(
        "/api/mouse/enroll",
        data=json.dumps({"name": name, "samples": samples}),
        content_type="application/json",
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Mouse dynamics API tests
# ---------------------------------------------------------------------------


class TestMouseEnroll:
    def test_missing_name_returns_400(self, client):
        resp = client.post(
            "/api/mouse/enroll",
            data=json.dumps({"name": "", "samples": [_mouse_sample()] * 5}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_too_few_samples_returns_400(self, client):
        resp = client.post(
            "/api/mouse/enroll",
            data=json.dumps({"name": "Alice", "samples": [_mouse_sample()] * 2}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_success_returns_enrolled_list(self, client):
        _mouse_enroll(client, "Bob")
        data = client.get("/api/mouse/profiles").get_json()
        assert any(e["name"] == "Bob" for e in data["enrolled"])

    def test_re_enroll_overwrites(self, client):
        _mouse_enroll(client, "Carol")
        _mouse_enroll(client, "Carol")
        data = client.get("/api/mouse/profiles").get_json()
        assert sum(1 for e in data["enrolled"] if e["name"] == "Carol") == 1


class TestMouseProfiles:
    def test_empty_returns_empty_list(self, client):
        data = client.get("/api/mouse/profiles").get_json()
        assert data["enrolled"] == []

    def test_enrolled_name_appears(self, client):
        _mouse_enroll(client, "Dave")
        data = client.get("/api/mouse/profiles").get_json()
        assert any(e["name"] == "Dave" for e in data["enrolled"])

    def test_num_samples_reported(self, client):
        _mouse_enroll(client, "Eve", n_samples=5)
        data = client.get("/api/mouse/profiles").get_json()
        entry = next(e for e in data["enrolled"] if e["name"] == "Eve")
        assert entry["num_samples"] == 5

    def test_profile_detail_returns_fields(self, client):
        _mouse_enroll(client, "Frank")
        data = client.get("/api/mouse/profiles/Frank").get_json()
        for key in (
            "mean_movement_times",
            "std_movement_times",
            "mean_click_dwells",
            "std_click_dwells",
            "mean_curvatures",
            "std_curvatures",
            "num_samples",
        ):
            assert key in data

    def test_profile_detail_returns_404_for_unknown(self, client):
        assert client.get("/api/mouse/profiles/Nobody").status_code == 404


class TestMouseIdentify:
    def test_non_dict_body_returns_400(self, client):
        resp = client.post(
            "/api/mouse/identify",
            data=json.dumps([1, 2, 3]),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "object" in resp.get_json()["error"].lower()

    def test_missing_sample_returns_400(self, client):
        resp = client.post(
            "/api/mouse/identify",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "sample" in resp.get_json()["error"].lower()

    def test_no_profiles_returns_400(self, client):
        resp = client.post(
            "/api/mouse/identify",
            data=json.dumps({"sample": _mouse_sample()}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_best_match_returned(self, client):
        _mouse_enroll(client, "Grace")
        _mouse_enroll(client, "Heidi")
        resp = client.post(
            "/api/mouse/identify",
            data=json.dumps({"sample": _mouse_sample()}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "best_match" in data
        assert "top_confidence" in data
        assert "results" in data

    def test_confidence_sums_to_100(self, client):
        _mouse_enroll(client, "Ivan")
        _mouse_enroll(client, "Judy")
        data = client.post(
            "/api/mouse/identify",
            data=json.dumps({"sample": _mouse_sample()}),
            content_type="application/json",
        ).get_json()
        total = sum(r["confidence"] for r in data["results"])
        assert abs(total - 100.0) < 0.2

    def test_single_profile_gets_100_confidence(self, client):
        _mouse_enroll(client, "Karl")
        data = client.post(
            "/api/mouse/identify",
            data=json.dumps({"sample": _mouse_sample()}),
            content_type="application/json",
        ).get_json()
        assert data["top_confidence"] == pytest.approx(100.0)


class TestMouseDeleteAndReset:
    def test_delete_removes_profile(self, client):
        _mouse_enroll(client, "Laura")
        client.delete("/api/mouse/profiles/Laura")
        data = client.get("/api/mouse/profiles").get_json()
        assert "Laura" not in [e["name"] for e in data["enrolled"]]

    def test_delete_non_existent_is_idempotent(self, client):
        resp = client.delete("/api/mouse/profiles/Ghost")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_reset_clears_all(self, client):
        _mouse_enroll(client, "Mallory")
        _mouse_enroll(client, "Niaj")
        client.post("/api/mouse/reset", content_type="application/json")
        assert client.get("/api/mouse/profiles").get_json()["enrolled"] == []

    def test_reset_returns_success(self, client):
        resp = client.post("/api/mouse/reset", content_type="application/json")
        assert resp.get_json()["success"] is True


# ---------------------------------------------------------------------------
# Admin API tests
# ---------------------------------------------------------------------------


class TestAdminLogin:
    def test_correct_pin_returns_success(self, client):
        resp = client.post(
            "/api/admin/login",
            data=json.dumps({"pin": DEFAULT_ADMIN_PIN}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_wrong_pin_returns_401(self, client):
        resp = client.post(
            "/api/admin/login",
            data=json.dumps({"pin": "0000"}),
            content_type="application/json",
        )
        assert resp.status_code == 401
        assert "error" in resp.get_json()

    def test_logout_returns_success(self, client):
        client.post(
            "/api/admin/login",
            data=json.dumps({"pin": DEFAULT_ADMIN_PIN}),
            content_type="application/json",
        )
        resp = client.post("/api/admin/logout", content_type="application/json")
        assert resp.get_json()["success"] is True


class TestAdminChangePin:
    def _login(self, client) -> None:
        client.post(
            "/api/admin/login",
            data=json.dumps({"pin": DEFAULT_ADMIN_PIN}),
            content_type="application/json",
        )

    def test_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/admin/change-pin",
            data=json.dumps({"new_pin": "9999"}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_too_short_returns_400(self, client):
        self._login(client)
        resp = client.post(
            "/api/admin/change-pin",
            data=json.dumps({"new_pin": "12"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_valid_change_returns_success(self, client):
        self._login(client)
        resp = client.post(
            "/api/admin/change-pin",
            data=json.dumps({"new_pin": "9876"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_new_pin_takes_effect(self, client):
        self._login(client)
        client.post(
            "/api/admin/change-pin",
            data=json.dumps({"new_pin": "5555"}),
            content_type="application/json",
        )
        client.post("/api/admin/logout", content_type="application/json")
        resp = client.post(
            "/api/admin/login",
            data=json.dumps({"pin": "5555"}),
            content_type="application/json",
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Face profiles API tests
# ---------------------------------------------------------------------------

FACE_FEATURES = [0.5 + i * 0.02 for i in range(16)]


class TestFaceEnroll:
    def test_missing_name_returns_400(self, client):
        resp = client.post(
            "/api/face/enroll",
            data=json.dumps({"name": "", "features": FACE_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_features_returns_400(self, client):
        resp = client.post(
            "/api/face/enroll",
            data=json.dumps({"name": "Alice"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_empty_features_returns_400(self, client):
        resp = client.post(
            "/api/face/enroll",
            data=json.dumps({"name": "Alice", "features": []}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_success_stores_profile(self, client):
        resp = client.post(
            "/api/face/enroll",
            data=json.dumps({"name": "Bob", "features": FACE_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert "Bob" in resp.get_json()["enrolled"]

    def test_re_enroll_overwrites(self, client):
        for _ in range(2):
            client.post(
                "/api/face/enroll",
                data=json.dumps({"name": "Carol", "features": FACE_FEATURES}),
                content_type="application/json",
            )
        data = client.get("/api/face/profiles").get_json()
        assert data["enrolled"].count("Carol") == 1


class TestFaceProfiles:
    def test_empty_returns_empty(self, client):
        data = client.get("/api/face/profiles").get_json()
        assert data["profiles"] == {}
        assert data["enrolled"] == []

    def test_enrolled_profile_returned(self, client):
        client.post(
            "/api/face/enroll",
            data=json.dumps({"name": "Dave", "features": FACE_FEATURES}),
            content_type="application/json",
        )
        data = client.get("/api/face/profiles").get_json()
        assert "Dave" in data["profiles"]
        assert data["profiles"]["Dave"] == FACE_FEATURES

    def test_delete_removes_profile(self, client):
        client.post(
            "/api/face/enroll",
            data=json.dumps({"name": "Eve", "features": FACE_FEATURES}),
            content_type="application/json",
        )
        client.delete("/api/face/profiles/Eve")
        data = client.get("/api/face/profiles").get_json()
        assert "Eve" not in data["profiles"]

    def test_delete_non_existent_is_idempotent(self, client):
        resp = client.delete("/api/face/profiles/Ghost")
        assert resp.status_code == 200

    def test_reset_clears_all(self, client):
        client.post(
            "/api/face/enroll",
            data=json.dumps({"name": "Frank", "features": FACE_FEATURES}),
            content_type="application/json",
        )
        client.post("/api/face/reset", content_type="application/json")
        assert client.get("/api/face/profiles").get_json()["profiles"] == {}


# ---------------------------------------------------------------------------
# Voice profiles API tests
# ---------------------------------------------------------------------------

VOICE_FEATURES = [float(i) * 0.1 for i in range(13)]


class TestVoiceEnroll:
    def test_missing_name_returns_400(self, client):
        resp = client.post(
            "/api/voice/enroll",
            data=json.dumps({"name": "", "features": VOICE_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_features_returns_400(self, client):
        resp = client.post(
            "/api/voice/enroll",
            data=json.dumps({"name": "Alice"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_success_stores_profile(self, client):
        resp = client.post(
            "/api/voice/enroll",
            data=json.dumps({"name": "Bob", "features": VOICE_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert "Bob" in resp.get_json()["enrolled"]


class TestVoiceProfiles:
    def test_empty_returns_empty(self, client):
        data = client.get("/api/voice/profiles").get_json()
        assert data["profiles"] == {}

    def test_enrolled_profile_returned(self, client):
        client.post(
            "/api/voice/enroll",
            data=json.dumps({"name": "Carol", "features": VOICE_FEATURES}),
            content_type="application/json",
        )
        data = client.get("/api/voice/profiles").get_json()
        assert "Carol" in data["profiles"]

    def test_delete_removes_profile(self, client):
        client.post(
            "/api/voice/enroll",
            data=json.dumps({"name": "Dave", "features": VOICE_FEATURES}),
            content_type="application/json",
        )
        client.delete("/api/voice/profiles/Dave")
        assert "Dave" not in client.get("/api/voice/profiles").get_json()["profiles"]

    def test_delete_non_existent_is_idempotent(self, client):
        assert client.delete("/api/voice/profiles/Ghost").status_code == 200

    def test_reset_clears_all(self, client):
        client.post(
            "/api/voice/enroll",
            data=json.dumps({"name": "Eve", "features": VOICE_FEATURES}),
            content_type="application/json",
        )
        client.post("/api/voice/reset", content_type="application/json")
        assert client.get("/api/voice/profiles").get_json()["profiles"] == {}


# ---------------------------------------------------------------------------
# Signature profiles API tests
# ---------------------------------------------------------------------------

SIG_FEATURES = {
    "dur": 2.5,
    "pathLen": 1.2,
    "avgVel": 0.48,
    "maxVel": 0.9,
    "velVar": 0.05,
    "numStrokes": 3,
    "aspect": 1.5,
    "dirRate": 0.6,
}


class TestSignatureEnroll:
    def test_missing_name_returns_400(self, client):
        resp = client.post(
            "/api/signature/enroll",
            data=json.dumps({"name": "", "features": SIG_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_features_returns_400(self, client):
        resp = client.post(
            "/api/signature/enroll",
            data=json.dumps({"name": "Alice"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_success_stores_profile(self, client):
        resp = client.post(
            "/api/signature/enroll",
            data=json.dumps({"name": "Bob", "features": SIG_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert "Bob" in resp.get_json()["enrolled"]


class TestSignatureProfiles:
    def test_empty_returns_empty(self, client):
        data = client.get("/api/signature/profiles").get_json()
        assert data["profiles"] == {}

    def test_enrolled_profile_returned(self, client):
        client.post(
            "/api/signature/enroll",
            data=json.dumps({"name": "Carol", "features": SIG_FEATURES}),
            content_type="application/json",
        )
        data = client.get("/api/signature/profiles").get_json()
        assert "Carol" in data["profiles"]
        assert data["profiles"]["Carol"] == SIG_FEATURES

    def test_delete_removes_profile(self, client):
        client.post(
            "/api/signature/enroll",
            data=json.dumps({"name": "Dave", "features": SIG_FEATURES}),
            content_type="application/json",
        )
        client.delete("/api/signature/profiles/Dave")
        assert (
            "Dave" not in client.get("/api/signature/profiles").get_json()["profiles"]
        )

    def test_delete_non_existent_is_idempotent(self, client):
        assert client.delete("/api/signature/profiles/Ghost").status_code == 200

    def test_reset_clears_all(self, client):
        client.post(
            "/api/signature/enroll",
            data=json.dumps({"name": "Eve", "features": SIG_FEATURES}),
            content_type="application/json",
        )
        client.post("/api/signature/reset", content_type="application/json")
        assert client.get("/api/signature/profiles").get_json()["profiles"] == {}


# ---------------------------------------------------------------------------
# Export / Import API tests (admin-only)
# ---------------------------------------------------------------------------


def _admin_login(client) -> None:
    """Helper: log in as admin using the default PIN."""
    resp = client.post(
        "/api/admin/login",
        data=json.dumps({"pin": DEFAULT_ADMIN_PIN}),
        content_type="application/json",
    )
    assert resp.status_code == 200


class TestKeystrokeExportImport:
    def test_export_unauthenticated_returns_403(self, client):
        assert client.get("/api/export").status_code == 403

    def test_import_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/import",
            data=json.dumps({"Alice": {}}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_export_returns_dict(self, client):
        _admin_login(client)
        resp = client.get("/api/export")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), dict)

    def test_export_includes_enrolled_profiles(self, client):
        _enroll(client, "Alice")
        _admin_login(client)
        data = client.get("/api/export").get_json()
        assert "Alice" in data

    def test_import_merges_profiles(self, client):
        _enroll(client, "Bob")
        _admin_login(client)
        exported = client.get("/api/export").get_json()
        # Clear and re-import
        client.post("/api/reset", content_type="application/json")
        resp = client.post(
            "/api/import",
            data=json.dumps(exported),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["imported"] == len(exported)
        profiles = client.get("/api/profiles").get_json()
        assert "Bob" in [e["name"] for e in profiles["enrolled"]]

    def test_import_non_object_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/import",
            data=json.dumps([1, 2, 3]),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_invalid_schema_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/import",
            data=json.dumps({"Alice": {"bad_key": "not_a_profile"}}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_non_dict_profile_value_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/import",
            data=json.dumps({"Alice": 42}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestMouseExportImport:
    def test_export_unauthenticated_returns_403(self, client):
        assert client.get("/api/mouse/export").status_code == 403

    def test_import_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/mouse/import",
            data=json.dumps({"Alice": {}}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_export_returns_dict(self, client):
        _admin_login(client)
        resp = client.get("/api/mouse/export")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), dict)

    def test_import_merges_profiles(self, client):
        _mouse_enroll(client, "TestUser")
        _admin_login(client)
        payload = client.get("/api/mouse/export").get_json()
        assert "TestUser" in payload

        client.post("/api/mouse/reset", content_type="application/json")
        _mouse_enroll(client, "ExistingUser")

        resp = client.post(
            "/api/mouse/import",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["imported"] == len(payload)
        data = client.get("/api/mouse/export").get_json()
        assert "TestUser" in data
        assert "ExistingUser" in data

    def test_import_non_object_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/mouse/import",
            data=json.dumps("bad"),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_invalid_schema_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/mouse/import",
            data=json.dumps({"Alice": {"speeds": [1.0, 2.0]}}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_non_dict_profile_value_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/mouse/import",
            data=json.dumps({"Alice": "not_a_dict"}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestFaceExportImport:
    def test_export_unauthenticated_returns_403(self, client):
        assert client.get("/api/face/export").status_code == 403

    def test_import_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/face/import",
            data=json.dumps({"Alice": FACE_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_export_returns_dict(self, client):
        _admin_login(client)
        resp = client.get("/api/face/export")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), dict)

    def test_export_includes_enrolled_profiles(self, client):
        client.post(
            "/api/face/enroll",
            data=json.dumps({"name": "Alice", "features": FACE_FEATURES}),
            content_type="application/json",
        )
        _admin_login(client)
        data = client.get("/api/face/export").get_json()
        assert "Alice" in data

    def test_import_merges_profiles(self, client):
        _admin_login(client)
        payload = {"Bob": FACE_FEATURES}
        resp = client.post(
            "/api/face/import",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["imported"] == 1
        data = client.get("/api/face/export").get_json()
        assert "Bob" in data

    def test_import_non_object_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/face/import",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_invalid_schema_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/face/import",
            data=json.dumps({"Alice": 42}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_voice_features_into_face_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/face/import",
            data=json.dumps({"Alice": VOICE_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestVoiceExportImport:
    def test_export_unauthenticated_returns_403(self, client):
        assert client.get("/api/voice/export").status_code == 403

    def test_import_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/voice/import",
            data=json.dumps({"Alice": VOICE_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_export_returns_dict(self, client):
        _admin_login(client)
        resp = client.get("/api/voice/export")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), dict)

    def test_export_includes_enrolled_profiles(self, client):
        client.post(
            "/api/voice/enroll",
            data=json.dumps({"name": "Alice", "features": VOICE_FEATURES}),
            content_type="application/json",
        )
        _admin_login(client)
        data = client.get("/api/voice/export").get_json()
        assert "Alice" in data

    def test_import_merges_profiles(self, client):
        _admin_login(client)
        payload = {"Bob": VOICE_FEATURES}
        resp = client.post(
            "/api/voice/import",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["imported"] == 1
        data = client.get("/api/voice/export").get_json()
        assert "Bob" in data

    def test_import_non_object_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/voice/import",
            data=json.dumps([1, 2]),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_invalid_schema_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/voice/import",
            data=json.dumps({"Alice": []}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_face_features_into_voice_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/voice/import",
            data=json.dumps({"Alice": FACE_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestSignatureExportImport:
    def test_export_unauthenticated_returns_403(self, client):
        assert client.get("/api/signature/export").status_code == 403

    def test_import_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/signature/import",
            data=json.dumps({"Alice": SIG_FEATURES}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_export_returns_dict(self, client):
        _admin_login(client)
        resp = client.get("/api/signature/export")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), dict)

    def test_export_includes_enrolled_profiles(self, client):
        client.post(
            "/api/signature/enroll",
            data=json.dumps({"name": "Alice", "features": SIG_FEATURES}),
            content_type="application/json",
        )
        _admin_login(client)
        data = client.get("/api/signature/export").get_json()
        assert "Alice" in data

    def test_import_merges_profiles(self, client):
        _admin_login(client)
        payload = {"Bob": SIG_FEATURES}
        resp = client.post(
            "/api/signature/import",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["imported"] == 1
        data = client.get("/api/signature/export").get_json()
        assert "Bob" in data

    def test_import_non_object_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/signature/import",
            data=json.dumps("invalid"),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_invalid_schema_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/signature/import",
            data=json.dumps({"Alice": {"bad_key": 1.0}}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_non_dict_profile_value_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/signature/import",
            data=json.dumps({"Alice": [1, 2, 3]}),
            content_type="application/json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Admin settings endpoints
# ---------------------------------------------------------------------------


class TestKeystrokeSettings:
    def test_get_unauthenticated_returns_403(self, client):
        resp = client.get("/api/admin/keystroke-settings")
        assert resp.status_code == 403

    def test_post_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/admin/keystroke-settings",
            data=json.dumps({"phrase": "hello", "samples": 3, "softmax_scale": 2.0}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_get_returns_defaults(self, client):
        _admin_login(client)
        resp = client.get("/api/admin/keystroke-settings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "phrase" in data
        assert "samples" in data
        assert "softmax_scale" in data

    def test_post_saves_and_get_reflects_change(self, client):
        _admin_login(client)
        client.post(
            "/api/admin/keystroke-settings",
            data=json.dumps(
                {"phrase": "hello world", "samples": 7, "softmax_scale": 3.5}
            ),
            content_type="application/json",
        )
        resp = client.get("/api/admin/keystroke-settings")
        data = resp.get_json()
        assert data["phrase"] == "hello world"
        assert data["samples"] == 7
        assert data["softmax_scale"] == pytest.approx(3.5)

    def test_post_empty_phrase_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/keystroke-settings",
            data=json.dumps({"phrase": "  ", "samples": 3, "softmax_scale": 2.0}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_post_invalid_samples_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/keystroke-settings",
            data=json.dumps({"phrase": "test", "samples": 0, "softmax_scale": 2.0}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_post_invalid_softmax_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/keystroke-settings",
            data=json.dumps({"phrase": "test", "samples": 3, "softmax_scale": -1.0}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_softmax_used_in_identify(self, client):
        """Higher softmax scale increases separation between matches."""
        _admin_login(client)

        # Enroll with slow typing (high dwell) and fast typing (low dwell)
        slow_samples = [
            _sample(base_dwell=200.0 + j, base_flight=150.0 + j) for j in range(5)
        ]
        fast_samples = [
            _sample(base_dwell=40.0 + j, base_flight=20.0 + j) for j in range(5)
        ]
        client.post(
            "/api/enroll",
            data=json.dumps({"name": "SlowTyper", "samples": slow_samples}),
            content_type="application/json",
        )
        client.post(
            "/api/enroll",
            data=json.dumps({"name": "FastTyper", "samples": fast_samples}),
            content_type="application/json",
        )

        # Set a very high softmax scale
        client.post(
            "/api/admin/keystroke-settings",
            data=json.dumps({"phrase": PHRASE, "samples": 5, "softmax_scale": 20.0}),
            content_type="application/json",
        )

        # Identify with a slow sample — should strongly prefer SlowTyper
        resp = client.post(
            "/api/identify",
            data=json.dumps({"timing": _sample(base_dwell=200.0, base_flight=150.0)}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        results = resp.get_json()["results"]
        assert results[0]["name"] == "SlowTyper"
        assert results[0]["confidence"] > 90.0


class TestMouseSettings:
    def test_get_unauthenticated_returns_403(self, client):
        resp = client.get("/api/admin/mouse-settings")
        assert resp.status_code == 403

    def test_post_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/admin/mouse-settings",
            data=json.dumps({"samples": 3, "softmax_scale": 2.0}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_get_returns_defaults(self, client):
        _admin_login(client)
        resp = client.get("/api/admin/mouse-settings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "samples" in data
        assert "softmax_scale" in data

    def test_post_saves_and_get_reflects_change(self, client):
        _admin_login(client)
        client.post(
            "/api/admin/mouse-settings",
            data=json.dumps({"samples": 8, "softmax_scale": 4.0}),
            content_type="application/json",
        )
        resp = client.get("/api/admin/mouse-settings")
        data = resp.get_json()
        assert data["samples"] == 8
        assert data["softmax_scale"] == pytest.approx(4.0)

    def test_post_invalid_samples_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/mouse-settings",
            data=json.dumps({"samples": 0, "softmax_scale": 2.0}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_post_invalid_softmax_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/mouse-settings",
            data=json.dumps({"samples": 3, "softmax_scale": 0}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestVoiceSettings:
    def test_get_unauthenticated_returns_403(self, client):
        resp = client.get("/api/admin/voice-settings")
        assert resp.status_code == 403

    def test_post_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 10}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_get_returns_defaults(self, client):
        _admin_login(client)
        resp = client.get("/api/admin/voice-settings")
        assert resp.status_code == 200
        assert "duration" in resp.get_json()

    def test_post_saves_and_get_reflects_change(self, client):
        _admin_login(client)
        client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 30}),
            content_type="application/json",
        )
        resp = client.get("/api/admin/voice-settings")
        assert resp.get_json()["duration"] == 30

    def test_post_below_minimum_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 2}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_post_above_maximum_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 61}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_duration_injected_into_voice_template(self, client):
        """Voice page should reflect configured duration as ENROL_FRAMES."""
        _admin_login(client)
        client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 20}),
            content_type="application/json",
        )
        resp = client.get("/voice")
        assert resp.status_code == 200
        assert b"1200" in resp.data  # 20 s × 60 fps

    def test_get_returns_enrol_samples_in_response(self, client):
        _admin_login(client)
        resp = client.get("/api/admin/voice-settings")
        data = resp.get_json()
        assert "enrol_samples" in data
        assert data["enrol_samples"] == 3  # default

    def test_post_enrol_samples_saves_and_get_reflects_change(self, client):
        _admin_login(client)
        client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 10, "enrol_samples": 5}),
            content_type="application/json",
        )
        resp = client.get("/api/admin/voice-settings")
        assert resp.get_json()["enrol_samples"] == 5

    def test_post_enrol_samples_below_minimum_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 10, "enrol_samples": 0}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_post_enrol_samples_above_maximum_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 10, "enrol_samples": 11}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_enrol_samples_injected_into_voice_template(self, client):
        """Voice page should reflect configured enrol_samples as ENROL_SAMPLES."""
        _admin_login(client)
        client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 10, "enrol_samples": 7}),
            content_type="application/json",
        )
        resp = client.get("/voice")
        assert resp.status_code == 200
        assert b'parseInt("7"' in resp.data


class TestSignatureSettings:
    def test_get_unauthenticated_returns_403(self, client):
        resp = client.get("/api/admin/signature-settings")
        assert resp.status_code == 403

    def test_post_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/admin/signature-settings",
            data=json.dumps({"samples": 3}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_get_returns_defaults(self, client):
        _admin_login(client)
        resp = client.get("/api/admin/signature-settings")
        assert resp.status_code == 200
        assert "samples" in resp.get_json()

    def test_post_saves_and_get_reflects_change(self, client):
        _admin_login(client)
        client.post(
            "/api/admin/signature-settings",
            data=json.dumps({"samples": 5}),
            content_type="application/json",
        )
        resp = client.get("/api/admin/signature-settings")
        assert resp.get_json()["samples"] == 5

    def test_post_invalid_samples_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/signature-settings",
            data=json.dumps({"samples": 0}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_samples_injected_into_signature_template(self, client):
        """Signature page should embed the configured sample count."""
        _admin_login(client)
        client.post(
            "/api/admin/signature-settings",
            data=json.dumps({"samples": 6}),
            content_type="application/json",
        )
        resp = client.get("/signature")
        assert resp.status_code == 200
        assert b'"6"' in resp.data  # parseInt("6", 10) in rendered template


class TestFaceSettings:
    def test_get_unauthenticated_returns_403(self, client):
        resp = client.get("/api/admin/face-settings")
        assert resp.status_code == 403

    def test_post_unauthenticated_returns_403(self, client):
        resp = client.post(
            "/api/admin/face-settings",
            data=json.dumps({"enrol_samples": 3}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_get_returns_defaults(self, client):
        _admin_login(client)
        resp = client.get("/api/admin/face-settings")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["enrol_samples"] == 3

    def test_post_saves_and_get_reflects_change(self, client):
        _admin_login(client)
        client.post(
            "/api/admin/face-settings",
            data=json.dumps({"enrol_samples": 5}),
            content_type="application/json",
        )
        resp = client.get("/api/admin/face-settings")
        assert resp.get_json()["enrol_samples"] == 5

    def test_post_below_minimum_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/face-settings",
            data=json.dumps({"enrol_samples": 0}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_post_above_maximum_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/face-settings",
            data=json.dumps({"enrol_samples": 11}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_enrol_samples_injected_into_face_template(self, client):
        """Face page should embed the configured enrol_samples value."""
        _admin_login(client)
        client.post(
            "/api/admin/face-settings",
            data=json.dumps({"enrol_samples": 4}),
            content_type="application/json",
        )
        resp = client.get("/face")
        assert resp.status_code == 200
        assert b'parseInt("4"' in resp.data

    def test_post_non_object_json_returns_400(self, client):
        _admin_login(client)
        resp = client.post(
            "/api/admin/face-settings",
            data=json.dumps([1, 2, 3]),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_get_corrupted_config_falls_back_to_default(self, client, tmp_path):
        """load_face_settings should return default=3 when config has a non-integer value."""
        import src.app as app_module

        (tmp_path / "admin_config.json").write_text(
            json.dumps({"face_enrol_samples": "not-a-number"})
        )
        settings = app_module.load_face_settings()
        assert settings["enrol_samples"] == 3

    def test_get_out_of_range_config_falls_back_to_default(self, client, tmp_path):
        """load_face_settings should return default=3 when config value is out of 1–10 range."""
        import src.app as app_module

        (tmp_path / "admin_config.json").write_text(
            json.dumps({"face_enrol_samples": 99})
        )
        settings = app_module.load_face_settings()
        assert settings["enrol_samples"] == 3


class TestSettingsPersistence:
    """Verify settings survive across requests via the config file."""

    def test_keystroke_settings_persist_across_requests(self, client):
        _admin_login(client)
        client.post(
            "/api/admin/keystroke-settings",
            data=json.dumps(
                {"phrase": "persist test", "samples": 4, "softmax_scale": 1.5}
            ),
            content_type="application/json",
        )
        # New request — reads from the config file
        resp = client.get("/api/admin/keystroke-settings")
        data = resp.get_json()
        assert data["phrase"] == "persist test"
        assert data["samples"] == 4
        assert data["softmax_scale"] == pytest.approx(1.5)

    def test_cfg_file_read_branch_covered(self, client):
        """Ensure _load_cfg takes the file-exists path after a save."""
        _admin_login(client)
        # First write — creates the file
        client.post(
            "/api/admin/voice-settings",
            data=json.dumps({"duration": 15}),
            content_type="application/json",
        )
        # Second read — exercises the open/json.load branch in _load_cfg
        resp = client.get("/api/admin/voice-settings")
        assert resp.get_json()["duration"] == 15
