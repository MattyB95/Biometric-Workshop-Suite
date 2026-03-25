import json
import math
import os
from typing import Any

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)

PROFILES_FILE = "profiles.json"
PHRASE = "the quick brown fox"
ENROLL_SAMPLES_REQUIRED = 5


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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index() -> str:
    return render_template(
        "index.html", phrase=PHRASE, enroll_samples=ENROLL_SAMPLES_REQUIRED
    )


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
