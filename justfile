# Keystroke Dynamics Demo — task runner
# Install just: https://github.com/casey/just

set shell := ["pwsh", "-c"]

# List available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Run the development server (localhost only)
run:
    uv run python app.py

# Run the server accessible to other devices on the network (workshop mode)
run-network:
    uv run flask --app app run --host 0.0.0.0 --port 5000

# Delete all enrolled profiles (fresh start for a new session)
reset:
    rm -f profiles.json
    @echo "All profiles deleted."

# Run with gunicorn (production mode, mirrors Render)
serve:
    uv run gunicorn --bind 0.0.0.0:5000 app:app

# ── Code quality ────────────────────────────────────────────────────────────

# Run ruff linter
lint:
    uv run ruff check app.py

# Run ruff linter and auto-fix safe issues
lint-fix:
    uv run ruff check --fix app.py

# Format code with black and ruff
fmt:
    uv run black app.py
    uv run ruff format app.py

# Check formatting without modifying files
fmt-check:
    uv run black --check app.py
    uv run ruff format --check app.py

# Run mypy type checker
typecheck-mypy:
    uv run mypy app.py

# Run ty type checker
typecheck-ty:
    uv run ty check app.py

# Run both type checkers
typecheck:
    uv run mypy app.py
    uv run ty check app.py

# Run all checks (lint + format check + type checking) — use in CI
check:
    uv run ruff check app.py
    uv run black --check app.py
    uv run mypy app.py
    uv run ty check app.py

# ── HTML/CSS/JS (Node) ───────────────────────────────────────────────────────

# Format docs/index.html with Prettier (templates/ excluded — Jinja2 in <script>)
fmt-html:
    npx prettier --write docs/index.html

# Check HTML formatting without modifying
fmt-html-check:
    npx prettier --check docs/index.html

# Lint HTML structure in both files
lint-html:
    npx htmlhint docs/index.html templates/index.html

# Lint inline JavaScript in docs/index.html
lint-js:
    npx eslint docs/index.html

# Run all HTML/CSS/JS checks
check-html:
    npx prettier --check docs/index.html
    npx htmlhint docs/index.html templates/index.html
    npx eslint docs/index.html

# ── Tests ────────────────────────────────────────────────────────────────────

# Install Playwright browsers (run once after first uv sync --group dev)
playwright-install:
    uv run playwright install chromium

# Run all tests (unit + API + UI)
test:
    uv run pytest

# Run only Python tests (unit + API, no browser)
test-py:
    uv run pytest tests/test_algorithm.py tests/test_api.py -v

# Run only Playwright browser tests
test-ui:
    uv run pytest tests/test_ui.py -v

# Run tests and show coverage report (terminal + htmlcov/)
coverage:
    uv run pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov

# Check coverage meets the minimum threshold without opening the report
coverage-check:
    uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80

# ── Pre-commit ───────────────────────────────────────────────────────────────

# Run all pre-commit hooks against every file
pre-commit:
    uv run pre-commit run --all-files

# Install pre-commit hooks into .git
pre-commit-install:
    uv run pre-commit install

# ── App management ───────────────────────────────────────────────────────────

# Show currently enrolled students
profiles:
    #!/usr/bin/env python
    import json, os
    if not os.path.exists('profiles.json'):
        print('No profiles found.')
    else:
        data = json.load(open('profiles.json'))
        if not data:
            print('No profiles enrolled.')
        else:
            print(f'{len(data)} enrolled student(s):')
            for name, p in data.items():
                print(f"  - {name} ({p['num_samples']} samples)")
