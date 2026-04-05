# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.3.0] - 2026-04-05

### Added

- **Admin Settings Panel** — instructors can now configure per-modality parameters at runtime via the admin page without editing code or restarting the server:
  - Keystroke: typing phrase, enrolment attempts required, confidence sensitivity (softmax scale)
  - Mouse: enrolment attempts required, confidence sensitivity (softmax scale)
  - Voice: recording duration (3–60 seconds)
  - Signature: enrolment attempts required
- Settings persisted to `admin_config.json` (Flask) or `localStorage` (static site) and survive page reloads
- New API endpoints: `GET/POST /api/admin/keystroke-settings`, `GET/POST /api/admin/mouse-settings`, `GET/POST /api/admin/voice-settings`, `GET/POST /api/admin/signature-settings`
- **Multi-sample signature enrolment** — students draw their signature the configured number of times (default: 3); features are averaged into a single representative profile, reducing within-session variability
- Enrolment progress dots on the signature page show how many samples have been collected
- Profile management (export/import/delete/reset) restricted to the admin panel; individual modality pages no longer expose these controls
- Settings section added to the keystroke page in the static site removed; all settings now live in the admin panel

### Changed

- Keystroke and mouse identify now apply a configurable softmax scale (previously hardcoded to `2.0` in client-side JavaScript and server-side Python)
- Voice `ENROL_FRAMES` now derived from the configurable duration setting (`duration × 60`) rather than a hardcoded constant in both Flask template and static page
- Signature enrol button relabelled **Save Sample** to reflect the multi-sample collection flow
- `admin_config.json` now stores per-modality settings in addition to the admin PIN
- Jinja2 template values injected into `<script>` blocks wrapped as `parseInt("{{ value }}", 10)` to keep files parseable by ESLint without excluding them from linting

### Fixed

- `_load_cfg()` return type annotated correctly — `dict(json.load(f))` instead of bare `json.load(f)` to satisfy mypy strict mode
- ESLint parsing errors in `templates/voice.html` and `templates/signature.html` caused by bare Jinja2 expressions inside `<script>` blocks

### Tests

- 135 → 167 tests; coverage 84% → 100%
- Added `TestKeystrokeSettings`, `TestMouseSettings`, `TestVoiceSettings`, `TestSignatureSettings` covering auth guards, defaults, save/read-back, input validation, and integration assertions
- Added `TestSettingsPersistence` to exercise the `_load_cfg` file-read branch
- Added `test_import_non_dict_profile_value_returns_400` for keystroke, mouse, and signature import validators

---

## [0.2.0] - 2026-04-05

### Added

- Import and export for all five modalities in the admin panel — instructors can back up and restore profiles as JSON files
- New API routes `/api/export`, `/api/mouse/export`, `/api/face/export`, `/api/voice/export`, `/api/signature/export` (GET) and corresponding `/api/import`, `/api/mouse/import`, `/api/face/import`, `/api/voice/import`, `/api/signature/import` (POST) for the Flask backend
- Import/export in the static version reads and writes `localStorage` directly (no server required)

### Changed

- Voice `ENROL_FRAMES` increased from 80 to 600 (~10 seconds at 60 fps) for a more representative voice profile
- Voice Stop button now stops frame collection only — the microphone stays open so the user can re-record without reloading
- Voice UI status messages guide the user through the open-mic → record → stop → enrol/identify flow
- Voice enrolment instruction updated to "speak for ~10 seconds"
- CI workflow inlines npm lint commands directly rather than calling `just`, removing the dependency on `just` being installed on the Actions runner

### Fixed

- Clear button icon (`&#x239A;`) replaced with `&#x2715;` — the previous codepoint is absent from most system fonts and rendered as a square
- "All Modules" back links in `docs/face.html`, `docs/signature.html`, and `docs/voice.html` corrected from `href="/"` to `href="./index.html"` (GitHub Pages does not serve a root index)
- Algorithm documentation floor values corrected to match source constants: mouse click dwell 15 ms (was 20 ms), mouse curvature 0.03 (was 0.05)
- Deployment documentation updated to reflect GitHub Actions as the GitHub Pages source (not "Deploy from a branch")

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
- Comprehensive test suite: 99 tests, 100% coverage (unit, API, and Playwright E2E)
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
