import json
import math
import os
from typing import Any

from flask import Flask, Response, jsonify, render_template, request, session

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(_ROOT, "templates"),
    static_folder=os.path.join(_ROOT, "static"),
    static_url_path="/static",
)
app.secret_key = os.environ.get("BWS_SECRET_KEY", "bws-workshop-dev-key-change-in-prod")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB upload limit

PROFILES_FILE: str = os.path.join(_ROOT, "profiles.json")
DEFAULT_PHRASE = "the quick brown fox"
DEFAULT_ENROLL_SAMPLES = 5

MOUSE_PROFILES_FILE: str = os.path.join(_ROOT, "mouse_profiles.json")
MOUSE_ENROLL_SAMPLES_REQUIRED = 5

FACE_PROFILES_FILE: str = os.path.join(_ROOT, "face_profiles.json")
VOICE_PROFILES_FILE: str = os.path.join(_ROOT, "voice_profiles.json")
SIGNATURE_PROFILES_FILE: str = os.path.join(_ROOT, "signature_profiles.json")
ADMIN_CONFIG_FILE: str = os.path.join(_ROOT, "admin_config.json")
DEFAULT_ADMIN_PIN = "1965"

# ---------------------------------------------------------------------------
# Algorithm constants
# ---------------------------------------------------------------------------

SOFTMAX_SCALE = 2.0  # controls sharpness of confidence distribution
DWELL_FLOOR = 15.0  # ms – minimum std for keystroke dwell
FLIGHT_FLOOR = 25.0  # ms – minimum std for keystroke flight
SINGLE_SAMPLE_STD_MS = 30.0  # ms – default std when only one sample is enrolled
MOUSE_TIME_FLOOR = 30.0  # ms – minimum std for mouse movement times
MOUSE_DWELL_FLOOR = 15.0  # ms – minimum std for mouse click dwells
MOUSE_CURVE_FLOOR = 0.03  # curvature units – minimum std for curvature

# ---------------------------------------------------------------------------
# Profile persistence
# ---------------------------------------------------------------------------


def _load_json(path: str) -> dict[str, Any]:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)  # type: ignore[no-any-return]
    return {}


def _save_json(path: str, data: dict[str, Any]) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_admin_pin() -> str:
    if os.path.exists(ADMIN_CONFIG_FILE):
        with open(ADMIN_CONFIG_FILE) as f:
            cfg: dict[str, Any] = json.load(f)
            return str(cfg.get("pin", DEFAULT_ADMIN_PIN))
    return DEFAULT_ADMIN_PIN


def save_admin_pin(pin: str) -> None:
    cfg = _load_cfg()
    cfg["pin"] = pin
    _save_cfg(cfg)


def _load_cfg() -> dict[str, Any]:
    if os.path.exists(ADMIN_CONFIG_FILE):
        try:
            with open(ADMIN_CONFIG_FILE) as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                return loaded
        except json.JSONDecodeError:
            pass
    return {}


def _save_cfg(cfg: dict[str, Any]) -> None:
    with open(ADMIN_CONFIG_FILE, "w") as f:
        json.dump(cfg, f)


def load_keystroke_settings() -> dict[str, Any]:
    cfg = _load_cfg()
    return {
        "phrase": str(cfg.get("keystroke_phrase", DEFAULT_PHRASE)),
        "samples": int(cfg.get("keystroke_samples", DEFAULT_ENROLL_SAMPLES)),
        "softmax_scale": float(cfg.get("keystroke_softmax_scale", 2.0)),
    }


def save_keystroke_settings(phrase: str, samples: int, softmax_scale: float) -> None:
    cfg = _load_cfg()
    cfg["keystroke_phrase"] = phrase
    cfg["keystroke_samples"] = samples
    cfg["keystroke_softmax_scale"] = softmax_scale
    _save_cfg(cfg)


def load_mouse_settings() -> dict[str, Any]:
    cfg = _load_cfg()
    return {
        "samples": int(cfg.get("mouse_samples", 5)),
        "softmax_scale": float(cfg.get("mouse_softmax_scale", 2.0)),
    }


def save_mouse_settings(samples: int, softmax_scale: float) -> None:
    cfg = _load_cfg()
    cfg["mouse_samples"] = samples
    cfg["mouse_softmax_scale"] = softmax_scale
    _save_cfg(cfg)


def load_voice_settings() -> dict[str, Any]:
    cfg = _load_cfg()
    return {
        "duration": int(cfg.get("voice_duration", 10)),
        "enrol_samples": int(cfg.get("voice_enrol_samples", 3)),
    }


def save_voice_settings(duration: int, enrol_samples: int) -> None:
    cfg = _load_cfg()
    cfg["voice_duration"] = duration
    cfg["voice_enrol_samples"] = enrol_samples
    _save_cfg(cfg)


def load_signature_settings() -> dict[str, Any]:
    cfg = _load_cfg()
    return {
        "samples": int(cfg.get("signature_samples", 3)),
    }


def save_signature_settings(samples: int) -> None:
    cfg = _load_cfg()
    cfg["signature_samples"] = samples
    _save_cfg(cfg)


# ---------------------------------------------------------------------------
# Import schema validation helpers
# ---------------------------------------------------------------------------

_KEYSTROKE_REQUIRED_LISTS = ("mean_dwell", "std_dwell", "mean_flight", "std_flight")
_MOUSE_REQUIRED_LISTS = (
    "mean_click_dwells",
    "std_click_dwells",
    "mean_movement_times",
    "std_movement_times",
    "mean_curvatures",
    "std_curvatures",
)
_SIGNATURE_REQUIRED_FIELDS = (
    "dur",
    "pathLen",
    "avgVel",
    "maxVel",
    "velVar",
    "numStrokes",
    "aspect",
    "dirRate",
)


def _is_finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _is_numeric_list(lst: Any) -> bool:
    return (
        isinstance(lst, list)
        and len(lst) > 0
        and all(_is_finite_number(x) for x in lst)
    )


def _valid_keystroke_profile(v: Any) -> bool:
    if not isinstance(v, dict):
        return False
    if not isinstance(v.get("num_samples"), int):
        return False
    return all(_is_numeric_list(v.get(k)) for k in _KEYSTROKE_REQUIRED_LISTS)


def _valid_mouse_profile(v: Any) -> bool:
    if not isinstance(v, dict):
        return False
    if not isinstance(v.get("num_samples"), int):
        return False
    return all(_is_numeric_list(v.get(k)) for k in _MOUSE_REQUIRED_LISTS)


def _valid_numeric_feature_vector(v: Any, allowed_lengths: tuple[int, ...]) -> bool:
    if not isinstance(v, list):
        return False
    if len(v) not in allowed_lengths:
        return False
    return all(_is_finite_number(item) for item in v)


def _valid_face_features_profile(v: Any) -> bool:
    # face: exactly 16 finite numeric values
    return _valid_numeric_feature_vector(v, (16,))


def _valid_voice_features_profile(v: Any) -> bool:
    # voice: exactly 13 finite numeric values
    return _valid_numeric_feature_vector(v, (13,))


def _valid_signature_profile(v: Any) -> bool:
    if not isinstance(v, dict):
        return False
    return all(k in v and _is_finite_number(v[k]) for k in _SIGNATURE_REQUIRED_FIELDS)


# ---------------------------------------------------------------------------
# Maths helpers
# ---------------------------------------------------------------------------


def mean_and_std(
    values_by_sample: list[list[float]],
) -> tuple[list[float], list[float]]:
    """
    values_by_sample: list of lists, one per enrollment attempt.
    Returns (means, stds) each as a list of floats.
    """
    n = len(values_by_sample)
    length = len(values_by_sample[0])
    means = [sum(s[i] for s in values_by_sample) / n for i in range(length)]
    if n > 1:
        stds = [
            math.sqrt(sum((s[i] - means[i]) ** 2 for s in values_by_sample) / (n - 1))
            for i in range(length)
        ]
    else:
        # Single sample – use generous defaults so one-sample profiles still work
        stds = [SINGLE_SAMPLE_STD_MS] * length
    return means, stds


def compute_distance(timing: dict[str, Any], profile: dict[str, Any]) -> float:
    """
    Normalised Manhattan distance between a timing sample and a stored profile.
    Each feature is divided by max(std, floor) so high-variance features count less.
    Returns an average per-feature distance (scale-independent).
    """
    total = 0.0
    n = 0

    for t, m, s in zip(timing["dwell"], profile["mean_dwell"], profile["std_dwell"]):
        total += abs(t - m) / max(s, DWELL_FLOOR)
        n += 1

    for t, m, s in zip(timing["flight"], profile["mean_flight"], profile["std_flight"]):
        total += abs(t - m) / max(s, FLIGHT_FLOOR)
        n += 1

    return total / n if n > 0 else float("inf")


def compute_mouse_distance(sample: dict[str, Any], profile: dict[str, Any]) -> float:
    """
    Normalised Manhattan distance for mouse dynamics.
    Features: movement_times (7), click_dwells (8), curvatures (7).
    """
    total = 0.0
    n = 0

    for t, m, s in zip(
        sample["movement_times"],
        profile["mean_movement_times"],
        profile["std_movement_times"],
    ):
        total += abs(t - m) / max(s, MOUSE_TIME_FLOOR)
        n += 1

    for t, m, s in zip(
        sample["click_dwells"],
        profile["mean_click_dwells"],
        profile["std_click_dwells"],
    ):
        total += abs(t - m) / max(s, MOUSE_DWELL_FLOOR)
        n += 1

    for t, m, s in zip(
        sample["curvatures"],
        profile["mean_curvatures"],
        profile["std_curvatures"],
    ):
        total += abs(t - m) / max(s, MOUSE_CURVE_FLOOR)
        n += 1

    return total / n if n > 0 else float("inf")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def home() -> str:
    return render_template("home.html")


@app.route("/admin")
def admin() -> str:
    return render_template("admin.html", authenticated=session.get("admin", False))


@app.route("/keystroke")
def keystroke() -> str:
    ks = load_keystroke_settings()
    return render_template(
        "keystroke.html", phrase=ks["phrase"], enroll_samples=ks["samples"]
    )


@app.route("/face")
def face() -> str:
    return render_template("face.html")


@app.route("/voice")
def voice() -> str:
    vs = load_voice_settings()
    return render_template(
        "voice.html",
        enrol_frames=vs["duration"] * 60,
        enrol_samples=vs["enrol_samples"],
    )


@app.route("/signature")
def signature() -> str:
    ss = load_signature_settings()
    return render_template("signature.html", enroll_samples=ss["samples"])


@app.route("/mouse")
def mouse() -> str:
    ms = load_mouse_settings()
    return render_template("mouse.html", enroll_samples=ms["samples"])


@app.route("/api/enroll", methods=["POST"])
def enroll() -> Response | tuple[Response, int]:
    data = request.json or {}
    name = (data.get("name") or "").strip()
    samples = data.get("samples", [])

    if not name:
        return jsonify({"error": "Name is required"}), 400
    required = load_keystroke_settings()["samples"]
    if len(samples) < required:
        msg = f"Need {required} samples, got {len(samples)}"
        return jsonify({"error": msg}), 400

    dwell_samples = [s["dwell"] for s in samples]
    flight_samples = [s["flight"] for s in samples]

    mean_dwell, std_dwell = mean_and_std(dwell_samples)
    mean_flight, std_flight = mean_and_std(flight_samples)

    profiles = _load_json(PROFILES_FILE)
    profiles[name] = {
        "mean_dwell": mean_dwell,
        "std_dwell": std_dwell,
        "mean_flight": mean_flight,
        "std_flight": std_flight,
        "num_samples": len(samples),
    }
    _save_json(PROFILES_FILE, profiles)

    return jsonify({"success": True, "name": name, "enrolled": list(profiles.keys())})


@app.route("/api/identify", methods=["POST"])
def identify() -> Response | tuple[Response, int]:
    data = request.json or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    timing = data.get("timing")
    if not isinstance(timing, dict):
        return jsonify({"error": "timing is required"}), 400

    profiles = _load_json(PROFILES_FILE)
    if not profiles:
        return (
            jsonify({"error": "No profiles enrolled yet. Ask someone to enrol first!"}),
            400,
        )

    results: list[dict[str, Any]] = []
    for name, profile in profiles.items():
        dist = compute_distance(timing, profile)
        results.append({"name": name, "distance": round(dist, 4)})

    results.sort(key=lambda r: r["distance"])

    # Convert distances to confidence scores via softmax relative to best match.
    # Scaling factor controls how sharply peaked the distribution is.
    scale = load_keystroke_settings()["softmax_scale"]
    min_dist = results[0]["distance"]
    raw_scores = [math.exp(-scale * (r["distance"] - min_dist)) for r in results]
    total = sum(raw_scores)

    for i, r in enumerate(results):
        r["confidence"] = round(raw_scores[i] / total * 100, 1)

    return jsonify(
        {
            "results": results,
            "best_match": results[0]["name"],
            "top_confidence": results[0]["confidence"],
        }
    )


@app.route("/api/profiles", methods=["GET"])
def get_profiles() -> Response:
    profiles = _load_json(PROFILES_FILE)
    enrolled = [
        {"name": k, "num_samples": v["num_samples"]} for k, v in profiles.items()
    ]
    return jsonify(
        {"enrolled": enrolled, "phrase": load_keystroke_settings()["phrase"]}
    )


@app.route("/api/profiles/<name>", methods=["GET"])
def get_profile(name: str) -> Response | tuple[Response, int]:
    profiles = _load_json(PROFILES_FILE)
    if name not in profiles:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(profiles[name])


@app.route("/api/profiles/<name>", methods=["DELETE"])
def delete_profile(name: str) -> Response:
    profiles = _load_json(PROFILES_FILE)
    profiles.pop(name, None)
    _save_json(PROFILES_FILE, profiles)
    return jsonify({"success": True, "enrolled": list(profiles.keys())})


@app.route("/api/reset", methods=["POST"])
def reset() -> Response:
    _save_json(PROFILES_FILE, {})
    return jsonify({"success": True})


@app.route("/api/export", methods=["GET"])
def export_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(_load_json(PROFILES_FILE))


@app.route("/api/import", methods=["POST"])
def import_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    invalid = [k for k, v in data.items() if not _valid_keystroke_profile(v)]
    if invalid:
        names = ", ".join(invalid)
        return jsonify({"error": f"Invalid profile shape for: {names}"}), 400
    profiles = _load_json(PROFILES_FILE)
    profiles.update(data)
    _save_json(PROFILES_FILE, profiles)
    return jsonify({"success": True, "imported": len(data)})


# ---------------------------------------------------------------------------
# Mouse dynamics API
# ---------------------------------------------------------------------------


@app.route("/api/mouse/enroll", methods=["POST"])
def mouse_enroll() -> Response | tuple[Response, int]:
    data = request.json or {}
    name = (data.get("name") or "").strip()
    samples = data.get("samples", [])

    if not name:
        return jsonify({"error": "Name is required"}), 400
    required = load_mouse_settings()["samples"]
    if len(samples) < required:
        msg = f"Need {required} samples, got {len(samples)}"
        return jsonify({"error": msg}), 400

    mean_cd, std_cd = mean_and_std([s["click_dwells"] for s in samples])
    mean_mt, std_mt = mean_and_std([s["movement_times"] for s in samples])
    mean_cv, std_cv = mean_and_std([s["curvatures"] for s in samples])

    profiles = _load_json(MOUSE_PROFILES_FILE)
    profiles[name] = {
        "mean_click_dwells": mean_cd,
        "std_click_dwells": std_cd,
        "mean_movement_times": mean_mt,
        "std_movement_times": std_mt,
        "mean_curvatures": mean_cv,
        "std_curvatures": std_cv,
        "num_samples": len(samples),
    }
    _save_json(MOUSE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "name": name, "enrolled": list(profiles.keys())})


@app.route("/api/mouse/identify", methods=["POST"])
def mouse_identify() -> Response | tuple[Response, int]:
    data = request.json or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    sample = data.get("sample")
    if not isinstance(sample, dict):
        return jsonify({"error": "sample is required"}), 400

    profiles = _load_json(MOUSE_PROFILES_FILE)
    if not profiles:
        return (
            jsonify({"error": "No profiles enrolled yet. Ask someone to enrol first!"}),
            400,
        )

    results: list[dict[str, Any]] = []
    for name, profile in profiles.items():
        dist = compute_mouse_distance(sample, profile)
        results.append({"name": name, "distance": round(dist, 4)})

    results.sort(key=lambda r: r["distance"])

    scale = load_mouse_settings()["softmax_scale"]
    min_dist = results[0]["distance"]
    raw_scores = [math.exp(-scale * (r["distance"] - min_dist)) for r in results]
    total = sum(raw_scores)
    for i, r in enumerate(results):
        r["confidence"] = round(raw_scores[i] / total * 100, 1)

    return jsonify(
        {
            "results": results,
            "best_match": results[0]["name"],
            "top_confidence": results[0]["confidence"],
        }
    )


@app.route("/api/mouse/profiles", methods=["GET"])
def get_mouse_profiles() -> Response:
    profiles = _load_json(MOUSE_PROFILES_FILE)
    enrolled = [
        {"name": k, "num_samples": v["num_samples"]} for k, v in profiles.items()
    ]
    return jsonify({"enrolled": enrolled})


@app.route("/api/mouse/profiles/<name>", methods=["GET"])
def get_mouse_profile(name: str) -> Response | tuple[Response, int]:
    profiles = _load_json(MOUSE_PROFILES_FILE)
    if name not in profiles:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(profiles[name])


@app.route("/api/mouse/profiles/<name>", methods=["DELETE"])
def delete_mouse_profile(name: str) -> Response:
    profiles = _load_json(MOUSE_PROFILES_FILE)
    profiles.pop(name, None)
    _save_json(MOUSE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "enrolled": list(profiles.keys())})


@app.route("/api/mouse/reset", methods=["POST"])
def mouse_reset() -> Response:
    _save_json(MOUSE_PROFILES_FILE, {})
    return jsonify({"success": True})


@app.route("/api/mouse/export", methods=["GET"])
def export_mouse_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(_load_json(MOUSE_PROFILES_FILE))


@app.route("/api/mouse/import", methods=["POST"])
def import_mouse_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    invalid = [k for k, v in data.items() if not _valid_mouse_profile(v)]
    if invalid:
        names = ", ".join(invalid)
        return jsonify({"error": f"Invalid profile shape for: {names}"}), 400
    profiles = _load_json(MOUSE_PROFILES_FILE)
    profiles.update(data)
    _save_json(MOUSE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "imported": len(data)})


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------


@app.route("/api/admin/login", methods=["POST"])
def admin_login() -> Response | tuple[Response, int]:
    data = request.json or {}
    pin = str(data.get("pin", "")).strip()
    if pin == load_admin_pin():
        session["admin"] = True
        return jsonify({"success": True})
    return jsonify({"error": "Incorrect PIN"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout() -> Response:
    session.pop("admin", None)
    return jsonify({"success": True})


@app.route("/api/admin/change-pin", methods=["POST"])
def admin_change_pin() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json or {}
    new_pin = str(data.get("new_pin", "")).strip()
    if len(new_pin) < 4:
        return jsonify({"error": "PIN must be at least 4 characters"}), 400
    save_admin_pin(new_pin)
    # Note: existing authenticated sessions remain valid after a PIN change.
    # The PIN is only checked at login time, not on every request. This is
    # intentional for workshop use — see SECURITY.md.
    return jsonify({"success": True})


@app.route("/api/admin/keystroke-settings", methods=["GET"])
def get_keystroke_settings() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(load_keystroke_settings())


@app.route("/api/admin/keystroke-settings", methods=["POST"])
def set_keystroke_settings() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json or {}
    phrase = str(data.get("phrase", "")).strip()
    if not phrase:
        return jsonify({"error": "Phrase cannot be empty"}), 400
    try:
        samples = int(data.get("samples", 0))
        if samples < 1:
            raise ValueError
    except TypeError, ValueError:
        return jsonify({"error": "Samples must be a positive integer"}), 400
    try:
        softmax_scale = float(data.get("softmax_scale", 2.0))
        if softmax_scale <= 0:
            raise ValueError
    except TypeError, ValueError:
        return (
            jsonify({"error": "Confidence sensitivity must be a positive number"}),
            400,
        )
    save_keystroke_settings(phrase, samples, softmax_scale)
    return jsonify({"success": True})


@app.route("/api/admin/mouse-settings", methods=["GET"])
def get_mouse_settings() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(load_mouse_settings())


@app.route("/api/admin/mouse-settings", methods=["POST"])
def set_mouse_settings() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json or {}
    try:
        samples = int(data.get("samples", 0))
        if samples < 1:
            raise ValueError
    except TypeError, ValueError:
        return jsonify({"error": "Samples must be a positive integer"}), 400
    try:
        softmax_scale = float(data.get("softmax_scale", 2.0))
        if softmax_scale <= 0:
            raise ValueError
    except TypeError, ValueError:
        return (
            jsonify({"error": "Confidence sensitivity must be a positive number"}),
            400,
        )
    save_mouse_settings(samples, softmax_scale)
    return jsonify({"success": True})


@app.route("/api/admin/voice-settings", methods=["GET"])
def get_voice_settings() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(load_voice_settings())


@app.route("/api/admin/voice-settings", methods=["POST"])
def set_voice_settings() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json or {}
    try:
        duration = int(data.get("duration", 0))
        if duration < 3 or duration > 60:
            raise ValueError
    except TypeError, ValueError:
        return jsonify({"error": "Duration must be between 3 and 60 seconds"}), 400
    try:
        enrol_samples = int(data.get("enrol_samples", 3))
        if enrol_samples < 1 or enrol_samples > 10:
            raise ValueError
    except TypeError, ValueError:
        return jsonify({"error": "Enrolment samples must be between 1 and 10"}), 400
    save_voice_settings(duration, enrol_samples)
    return jsonify({"success": True})


@app.route("/api/admin/signature-settings", methods=["GET"])
def get_signature_settings() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(load_signature_settings())


@app.route("/api/admin/signature-settings", methods=["POST"])
def set_signature_settings() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json or {}
    try:
        samples = int(data.get("samples", 0))
        if samples < 1:
            raise ValueError
    except TypeError, ValueError:
        return jsonify({"error": "Samples must be a positive integer"}), 400
    save_signature_settings(samples)
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Face profiles API
# ---------------------------------------------------------------------------


@app.route("/api/face/enroll", methods=["POST"])
def face_enroll() -> Response | tuple[Response, int]:
    data = request.json or {}
    name = str(data.get("name", "")).strip()
    features = data.get("features")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not isinstance(features, list) or len(features) == 0:
        return jsonify({"error": "Features are required"}), 400
    profiles = _load_json(FACE_PROFILES_FILE)
    profiles[name] = features
    _save_json(FACE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "name": name, "enrolled": list(profiles.keys())})


@app.route("/api/face/profiles", methods=["GET"])
def get_face_profiles() -> Response:
    profiles = _load_json(FACE_PROFILES_FILE)
    return jsonify({"profiles": profiles, "enrolled": list(profiles.keys())})


@app.route("/api/face/profiles/<name>", methods=["DELETE"])
def delete_face_profile(name: str) -> Response:
    profiles = _load_json(FACE_PROFILES_FILE)
    profiles.pop(name, None)
    _save_json(FACE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "enrolled": list(profiles.keys())})


@app.route("/api/face/reset", methods=["POST"])
def face_reset() -> Response:
    _save_json(FACE_PROFILES_FILE, {})
    return jsonify({"success": True})


@app.route("/api/face/export", methods=["GET"])
def export_face_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(_load_json(FACE_PROFILES_FILE))


@app.route("/api/face/import", methods=["POST"])
def import_face_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    invalid = [k for k, v in data.items() if not _valid_face_features_profile(v)]
    if invalid:
        names = ", ".join(invalid)
        return jsonify({"error": f"Invalid profile shape for: {names}"}), 400
    profiles = _load_json(FACE_PROFILES_FILE)
    profiles.update(data)
    _save_json(FACE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "imported": len(data)})


# ---------------------------------------------------------------------------
# Voice profiles API
# ---------------------------------------------------------------------------


@app.route("/api/voice/enroll", methods=["POST"])
def voice_enroll() -> Response | tuple[Response, int]:
    data = request.json or {}
    name = str(data.get("name", "")).strip()
    features = data.get("features")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if features is None:
        return jsonify({"error": "Features are required"}), 400
    profiles = _load_json(VOICE_PROFILES_FILE)
    profiles[name] = features
    _save_json(VOICE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "name": name, "enrolled": list(profiles.keys())})


@app.route("/api/voice/profiles", methods=["GET"])
def get_voice_profiles() -> Response:
    profiles = _load_json(VOICE_PROFILES_FILE)
    return jsonify({"profiles": profiles, "enrolled": list(profiles.keys())})


@app.route("/api/voice/profiles/<name>", methods=["DELETE"])
def delete_voice_profile(name: str) -> Response:
    profiles = _load_json(VOICE_PROFILES_FILE)
    profiles.pop(name, None)
    _save_json(VOICE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "enrolled": list(profiles.keys())})


@app.route("/api/voice/reset", methods=["POST"])
def voice_reset() -> Response:
    _save_json(VOICE_PROFILES_FILE, {})
    return jsonify({"success": True})


@app.route("/api/voice/export", methods=["GET"])
def export_voice_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(_load_json(VOICE_PROFILES_FILE))


@app.route("/api/voice/import", methods=["POST"])
def import_voice_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    invalid = [k for k, v in data.items() if not _valid_voice_features_profile(v)]
    if invalid:
        names = ", ".join(invalid)
        return jsonify({"error": f"Invalid profile shape for: {names}"}), 400
    profiles = _load_json(VOICE_PROFILES_FILE)
    profiles.update(data)
    _save_json(VOICE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "imported": len(data)})


# ---------------------------------------------------------------------------
# Signature profiles API
# ---------------------------------------------------------------------------


@app.route("/api/signature/enroll", methods=["POST"])
def signature_enroll() -> Response | tuple[Response, int]:
    data = request.json or {}
    name = str(data.get("name", "")).strip()
    features = data.get("features")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if features is None:
        return jsonify({"error": "Features are required"}), 400
    profiles = _load_json(SIGNATURE_PROFILES_FILE)
    profiles[name] = features
    _save_json(SIGNATURE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "name": name, "enrolled": list(profiles.keys())})


@app.route("/api/signature/profiles", methods=["GET"])
def get_signature_profiles() -> Response:
    profiles = _load_json(SIGNATURE_PROFILES_FILE)
    return jsonify({"profiles": profiles, "enrolled": list(profiles.keys())})


@app.route("/api/signature/profiles/<name>", methods=["DELETE"])
def delete_signature_profile(name: str) -> Response:
    profiles = _load_json(SIGNATURE_PROFILES_FILE)
    profiles.pop(name, None)
    _save_json(SIGNATURE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "enrolled": list(profiles.keys())})


@app.route("/api/signature/reset", methods=["POST"])
def signature_reset() -> Response:
    _save_json(SIGNATURE_PROFILES_FILE, {})
    return jsonify({"success": True})


@app.route("/api/signature/export", methods=["GET"])
def export_signature_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    return jsonify(_load_json(SIGNATURE_PROFILES_FILE))


@app.route("/api/signature/import", methods=["POST"])
def import_signature_profiles() -> Response | tuple[Response, int]:
    if not session.get("admin"):
        return jsonify({"error": "Not authenticated"}), 403
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    invalid = [k for k, v in data.items() if not _valid_signature_profile(v)]
    if invalid:
        names = ", ".join(invalid)
        return jsonify({"error": f"Invalid profile shape for: {names}"}), 400
    profiles = _load_json(SIGNATURE_PROFILES_FILE)
    profiles.update(data)
    _save_json(SIGNATURE_PROFILES_FILE, profiles)
    return jsonify({"success": True, "imported": len(data)})


if __name__ == "__main__":  # pragma: no cover
    debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(debug=debug_mode, port=5000)
