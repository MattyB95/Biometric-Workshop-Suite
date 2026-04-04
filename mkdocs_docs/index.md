# Biometric Workshop Suite

![Biometric Workshop Suite](https://raw.githubusercontent.com/MattyB95/Biometric-Workshop-Suite/main/social_preview.png)

An interactive, multi-modality biometric demonstration suite built for classroom and workshop use. Students enrol their biometric traits across five different techniques and see in real time how each system works — from feature extraction through to matching and identification.

!!! warning "Educational Use Only"
    This project is designed exclusively for **education and training purposes**. The algorithms, storage, and architecture are intentionally simplified to make the concepts accessible and observable. This suite **must not** be used in any security-critical, production, or real-world authentication context.

---

## Modules

| Module | Technique | Features extracted |
|---|---|---|
| **Keystroke Dynamics** | Typing rhythm analysis | Dwell time, flight time per character |
| **Mouse Dynamics** | Pointer movement profiling | Movement time, path curvature, click dwell |
| **Face Recognition** | Geometric facial features | 16 normalised landmark ratios (68-point model) |
| **Voice Biometrics** | Speaker characterisation | MFCC mean vector, pitch, spectrogram |
| **Signature Dynamics** | On-screen handwriting | Duration, path length, velocity, stroke count |

Every module supports **Enrol** and **Identify** (or Verify) with live visualisations so students can see exactly which features are being extracted and how the matching score is calculated.

---

## Quick Start

**1. Clone the repository**

```bash
git clone https://github.com/MattyB95/Biometric-Workshop-Suite.git
cd Biometric-Workshop-Suite
```

**2. Install dependencies**

```bash
uv sync
```

**3. Run the server**

```bash
just run
```

**4. Open your browser**

```
http://localhost:5000
```

---

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A modern web browser (Chrome or Firefox recommended)
- A webcam for the Face Recognition module
- A microphone for the Voice Biometrics module

---

## Two versions

| Version | Where | Storage | Best for |
|---|---|---|---|
| **Flask app** | `src/app.py` + `templates/` | Server-side JSON files | Shared classroom server |
| **Static site** | `docs/` | Browser `localStorage` | GitHub Pages, offline use |

See [Deployment](deployment.md) for full hosting options.
