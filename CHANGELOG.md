# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] - 2026-04-04

Initial public release of the Biometric Workshop Suite.

### Added

- **Keystroke Dynamics** module — enrol/identify using dwell and flight timing with Manhattan distance matching
- **Mouse Dynamics** module — enrol/identify using movement time, path curvature, and click dwell
- **Face Recognition** module — live webcam landmark detection with cosine similarity matching
- **Voice Biometrics** module — MFCC feature extraction and speaker identification
- **Signature Dynamics** module — on-screen handwriting with velocity and stroke analysis
- PIN-protected instructor admin panel (`/admin`) with per-modality profile management
- Self-contained static version (`docs/`) for GitHub Pages deployment (all logic in JavaScript, `localStorage`)
- Flask backend with per-modality JSON profile storage and REST API
- Render deployment config (`render.yaml`) for hosted classroom use
- GitHub Actions CI workflow — lint, type check, and test on every push
- GitHub Actions docs workflow — MkDocs site and static app deployed to GitHub Pages
- GitHub Actions release workflow — automatically publishes a GitHub release on every push to `main`
- MkDocs documentation site with module explainers and workshop guide
- Comprehensive test suite: 97 tests, 100% coverage (unit, API, and Playwright E2E)
- Code quality toolchain: `ruff`, `black`, `mypy`, `prettier`, `eslint`, `htmlhint`, `pre-commit`
- `justfile` task runner with shortcuts for all common development tasks
- Dependabot configuration for automated dependency updates targeting `develop`
- GitHub Sponsors, Ko-fi, and thanks.dev funding links
- Community health files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`

### Changed

- Consolidated JSON persistence into two generic helpers (`_load_json` / `_save_json`)
- Extracted algorithm constants (`SOFTMAX_SCALE`, `DWELL_FLOOR`, `FLIGHT_FLOOR`, etc.)
- Tightened dependency version bounds (`flask<4.0.0`, `gunicorn<26.0.0`)
- `BWS_SECRET_KEY` auto-generated on Render deployments via `generateValue: true`

### Fixed

- XSS: added `escapeHtml` to face, voice, and signature templates
- `request.json` null guard on all enroll/identify endpoints
- `MAX_CONTENT_LENGTH` (1 MB) added to prevent oversized payloads
