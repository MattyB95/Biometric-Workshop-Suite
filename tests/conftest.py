"""Shared pytest fixtures for the test suite."""

import threading
import time

import pytest

import src.app as flask_app_module
from src.app import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Flask test client with isolated profile and config files per test."""
    monkeypatch.setattr(
        flask_app_module, "PROFILES_FILE", str(tmp_path / "profiles.json")
    )
    monkeypatch.setattr(
        flask_app_module, "MOUSE_PROFILES_FILE", str(tmp_path / "mouse_profiles.json")
    )
    monkeypatch.setattr(
        flask_app_module, "FACE_PROFILES_FILE", str(tmp_path / "face_profiles.json")
    )
    monkeypatch.setattr(
        flask_app_module, "VOICE_PROFILES_FILE", str(tmp_path / "voice_profiles.json")
    )
    monkeypatch.setattr(
        flask_app_module,
        "SIGNATURE_PROFILES_FILE",
        str(tmp_path / "signature_profiles.json"),
    )
    monkeypatch.setattr(
        flask_app_module, "ADMIN_CONFIG_FILE", str(tmp_path / "admin_config.json")
    )
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    """
    Live Flask server on 127.0.0.1:5099 for Playwright end-to-end tests.
    Started once per test session in a background daemon thread.
    """
    profiles_path = str(tmp_path_factory.mktemp("live") / "profiles.json")
    original_profiles_file = flask_app_module.PROFILES_FILE
    flask_app_module.PROFILES_FILE = profiles_path

    thread = threading.Thread(
        target=flask_app.run,
        kwargs={
            "host": "127.0.0.1",
            "port": 5099,
            "use_reloader": False,
            "debug": False,
        },
        daemon=True,
    )
    thread.start()
    time.sleep(0.5)  # Allow the server to finish binding

    yield "http://127.0.0.1:5099"

    flask_app_module.PROFILES_FILE = original_profiles_file
