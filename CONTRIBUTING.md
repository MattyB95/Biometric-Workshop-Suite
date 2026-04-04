# Contributing to Biometric Workshop Suite

Thank you for your interest in contributing. This project is an educational tool — contributions that make the demos clearer, more reliable, or more useful for teaching are most welcome.

## Educational scope

Before contributing, please keep in mind the project's core principle:

> This suite is for **education and training only**. It must never be used as a real authentication or security system.

Contributions that would make the project appear production-ready or that obscure its educational limitations will not be accepted.

---

## What kinds of contributions are welcome?

- **Bug fixes** — something broken in a demo or the admin panel
- **New biometric modules** — a new modality with the same enrol/identify pattern and a pipeline explainer
- **Teaching improvements** — better explanations, visualisations, or discussion prompts
- **Accessibility** — keyboard navigation, colour contrast, screen reader support
- **Documentation** — clearer setup instructions, additional hosting guides
- **Tests** — improved coverage for the Python backend or UI flows

---

## Getting started

**1. Fork and clone**

```bash
git clone https://github.com/<your-username>/Biometric-Workshop-Suite.git
cd Biometric-Workshop-Suite
```

**2. Install dependencies**

```bash
uv sync
```

**3. Install pre-commit hooks**

```bash
just pre-commit-install
```

**4. Run the dev server**

```bash
just run
```

---

## Making changes

- Keep the Flask app (`templates/` + `src/app.py`) and the static docs version (`docs/`) in sync where applicable.
- Run `just check` before committing — this runs ruff, black, and mypy.
- Run `just test-py` to confirm Python tests pass.
- If you add a new modality, add it to both the Flask and static versions and update the README module table.

---

## Commit style

Use short, imperative subject lines:

```
Add gait recognition module
Fix cosine similarity edge case when profile is empty
Update admin panel PIN validation
```

---

## Branching model

This project uses a two-branch model:

| Branch    | Purpose                                                                 |
| --------- | ----------------------------------------------------------------------- |
| `main`    | Stable, released code. Every push triggers an automated GitHub release. |
| `develop` | Integration branch. All work targets `develop` first.                   |

**Open all pull requests against `develop`**, not `main`. When a set of changes is ready to release, `develop` is merged into `main`.

To make a new release:

1. Bump the version in `pyproject.toml`
2. Move the `[Unreleased]` entries in `CHANGELOG.md` into a new versioned section
3. Merge `develop` → `main` — the release workflow creates the GitHub release automatically

## Pull requests

- Open a PR against `develop`.
- Fill in the PR template.
- One logical change per PR — separate bug fixes from new features.
- If your change affects the workshop UX, briefly describe how you tested it in a browser.

---

## Code style

| Tool       | Purpose                                          |
| ---------- | ------------------------------------------------ |
| `ruff`     | Python linting and import sorting                |
| `black`    | Python formatting                                |
| `mypy`     | Python static type checking (strict mode)        |
| `prettier` | HTML/JS formatting (docs/ and select templates/) |
| `htmlhint` | HTML structure linting                           |
| `eslint`   | JavaScript linting                               |

All checks run automatically via pre-commit hooks once installed.

---

## Questions?

Open a [GitHub Discussion](../../discussions) or file an issue with the `question` label.
