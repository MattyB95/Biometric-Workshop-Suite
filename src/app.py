import json
import math
import os
from typing import Any

from flask import Flask, Response, jsonify, render_template, request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(_ROOT, "templates"),
    static_folder=os.path.join(_ROOT, "static"),
    static_url_path="/static",
)

PROFILES_FILE: str = os.path.join(_ROOT, "profiles.json")
PHRASE = "the quick brown fox"
ENROLL_SAMPLES_REQUIRED = 5

MOUSE_PROFILES_FILE: str = os.path.join(_ROOT, "mouse_profiles.json")
MOUSE_ENROLL_SAMPLES_REQUIRED = 5


# ---------------------------------------------------------------------------
# Profile persistence
# ---------------------------------------------------------------------------


def load_profiles() -> dict[str, Any]:
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE) as f:
            return json.load(f)  # type: ignore[no-any-return]
    return {}


def save_profiles(profiles: dict[str, Any]) -> None:
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


def load_mouse_profiles() -> dict[str, Any]:
    if os.path.exists(MOUSE_PROFILES_FILE):
        with open(MOUSE_PROFILES_FILE) as f:
            return json.load(f)  # type: ignore[no-any-return]
    return {}


def save_mouse_profiles(profiles: dict[str, Any]) -> None:
    with open(MOUSE_PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


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
        stds = [30.0] * length
    return means, stds


def compute_distance(timing: dict[str, Any], profile: dict[str, Any]) -> float:
    """
    Normalised Manhattan distance between a timing sample and a stored profile.
    Each feature is divided by max(std, floor) so high-variance features count less.
    Returns an average per-feature distance (scale-independent).
    """
    total = 0.0
    n = 0

    dwell_floor = 15.0  # ms – minimum std for dwell
    flight_floor = 25.0  # ms – minimum std for flight

    for t, m, s in zip(timing["dwell"], profile["mean_dwell"], profile["std_dwell"]):
        total += abs(t - m) / max(s, dwell_floor)
        n += 1

    for t, m, s in zip(timing["flight"], profile["mean_flight"], profile["std_flight"]):
        total += abs(t - m) / max(s, flight_floor)
        n += 1

    return total / n if n > 0 else float("inf")


def compute_mouse_distance(sample: dict[str, Any], profile: dict[str, Any]) -> float:
    """
    Normalised Manhattan distance for mouse dynamics.
    Features: movement_times (7), click_dwells (8), curvatures (7).
    """
    total = 0.0
    n = 0

    time_floor = 30.0  # ms
    dwell_floor = 15.0  # ms
    curve_floor = 0.03  # curvature units

    for t, m, s in zip(
        sample["movement_times"],
        profile["mean_movement_times"],
        profile["std_movement_times"],
    ):
        total += abs(t - m) / max(s, time_floor)
        n += 1

    for t, m, s in zip(
        sample["click_dwells"],
        profile["mean_click_dwells"],
        profile["std_click_dwells"],
    ):
        total += abs(t - m) / max(s, dwell_floor)
        n += 1

    for t, m, s in zip(
        sample["curvatures"],
        profile["mean_curvatures"],
        profile["std_curvatures"],
    ):
        total += abs(t - m) / max(s, curve_floor)
        n += 1

    return total / n if n > 0 else float("inf")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def home() -> str:
    return render_template("home.html")


@app.route("/keystroke")
def keystroke() -> str:
    return render_template(
        "keystroke.html", phrase=PHRASE, enroll_samples=ENROLL_SAMPLES_REQUIRED
    )


@app.route("/face")
def face() -> str:
    return render_template("face.html")


@app.route("/voice")
def voice() -> str:
    return render_template("voice.html")


@app.route("/signature")
def signature() -> str:
    return render_template("signature.html")


@app.route("/mouse")
def mouse() -> str:
    return render_template("mouse.html", enroll_samples=MOUSE_ENROLL_SAMPLES_REQUIRED)


@app.route("/api/enroll", methods=["POST"])
def enroll() -> Response | tuple[Response, int]:
    data = request.json
    name = (data.get("name") or "").strip()
    samples = data.get("samples", [])

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if len(samples) < ENROLL_SAMPLES_REQUIRED:
        msg = f"Need {ENROLL_SAMPLES_REQUIRED} samples, got {len(samples)}"
        return jsonify({"error": msg}), 400

    dwell_samples = [s["dwell"] for s in samples]
    flight_samples = [s["flight"] for s in samples]

    mean_dwell, std_dwell = mean_and_std(dwell_samples)
    mean_flight, std_flight = mean_and_std(flight_samples)

    profiles = load_profiles()
    profiles[name] = {
        "mean_dwell": mean_dwell,
        "std_dwell": std_dwell,
        "mean_flight": mean_flight,
        "std_flight": std_flight,
        "num_samples": len(samples),
    }
    save_profiles(profiles)

    return jsonify({"success": True, "name": name, "enrolled": list(profiles.keys())})


@app.route("/api/identify", methods=["POST"])
def identify() -> Response | tuple[Response, int]:
    data = request.json
    timing = data.get("timing")

    profiles = load_profiles()
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
    scale = 2.0
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
    profiles = load_profiles()
    enrolled = [
        {"name": k, "num_samples": v["num_samples"]} for k, v in profiles.items()
    ]
    return jsonify({"enrolled": enrolled, "phrase": PHRASE})


@app.route("/api/profiles/<name>", methods=["GET"])
def get_profile(name: str) -> Response | tuple[Response, int]:
    profiles = load_profiles()
    if name not in profiles:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(profiles[name])


@app.route("/api/profiles/<name>", methods=["DELETE"])
def delete_profile(name: str) -> Response:
    profiles = load_profiles()
    profiles.pop(name, None)
    save_profiles(profiles)
    return jsonify({"success": True, "enrolled": list(profiles.keys())})


@app.route("/api/reset", methods=["POST"])
def reset() -> Response:
    save_profiles({})
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Mouse dynamics API
# ---------------------------------------------------------------------------


@app.route("/api/mouse/enroll", methods=["POST"])
def mouse_enroll() -> Response | tuple[Response, int]:
    data = request.json
    name = (data.get("name") or "").strip()
    samples = data.get("samples", [])

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if len(samples) < MOUSE_ENROLL_SAMPLES_REQUIRED:
        msg = f"Need {MOUSE_ENROLL_SAMPLES_REQUIRED} samples, got {len(samples)}"
        return jsonify({"error": msg}), 400

    mean_cd, std_cd = mean_and_std([s["click_dwells"] for s in samples])
    mean_mt, std_mt = mean_and_std([s["movement_times"] for s in samples])
    mean_cv, std_cv = mean_and_std([s["curvatures"] for s in samples])

    profiles = load_mouse_profiles()
    profiles[name] = {
        "mean_click_dwells": mean_cd,
        "std_click_dwells": std_cd,
        "mean_movement_times": mean_mt,
        "std_movement_times": std_mt,
        "mean_curvatures": mean_cv,
        "std_curvatures": std_cv,
        "num_samples": len(samples),
    }
    save_mouse_profiles(profiles)
    return jsonify({"success": True, "name": name, "enrolled": list(profiles.keys())})


@app.route("/api/mouse/identify", methods=["POST"])
def mouse_identify() -> Response | tuple[Response, int]:
    data = request.json
    sample = data.get("sample")

    profiles = load_mouse_profiles()
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

    scale = 2.0
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
    profiles = load_mouse_profiles()
    enrolled = [
        {"name": k, "num_samples": v["num_samples"]} for k, v in profiles.items()
    ]
    return jsonify({"enrolled": enrolled})


@app.route("/api/mouse/profiles/<name>", methods=["GET"])
def get_mouse_profile(name: str) -> Response | tuple[Response, int]:
    profiles = load_mouse_profiles()
    if name not in profiles:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(profiles[name])


@app.route("/api/mouse/profiles/<name>", methods=["DELETE"])
def delete_mouse_profile(name: str) -> Response:
    profiles = load_mouse_profiles()
    profiles.pop(name, None)
    save_mouse_profiles(profiles)
    return jsonify({"success": True, "enrolled": list(profiles.keys())})


@app.route("/api/mouse/reset", methods=["POST"])
def mouse_reset() -> Response:
    save_mouse_profiles({})
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
