# Biometric Workshop Suite — task runner
# Install just: https://github.com/casey/just

set shell := ["sh", "-c"]
set windows-shell := ["pwsh", "-c"]

# List available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Run the development server (localhost only)
run:
    uv run python src/app.py

# Run the server accessible to other devices on the network (workshop mode)
run-network:
    uv run flask --app src.app run --host 0.0.0.0 --port 5000

# Delete all enrolled profiles (fresh start for a new session)
reset:
    rm -f profiles.json
    @echo "All profiles deleted."

# Run with gunicorn (production mode, mirrors Render)
serve:
    uv run gunicorn --bind 0.0.0.0:5000 src.app:app

# ── Code quality ────────────────────────────────────────────────────────────

# Run ruff linter
lint:
    uv run ruff check src/app.py

# Run ruff linter and auto-fix safe issues
lint-fix:
    uv run ruff check --fix src/app.py

# Format code with black and ruff
fmt:
    uv run black src/app.py
    uv run ruff format src/app.py

# Check formatting without modifying files
fmt-check:
    uv run black --check src/app.py
    uv run ruff format --check src/app.py

# Run mypy type checker
typecheck-mypy:
    uv run mypy src/app.py

# Run ty type checker
typecheck-ty:
    uv run ty check src/app.py

# Run both type checkers
typecheck:
    uv run mypy src/app.py
    uv run ty check src/app.py

# Run all checks (lint + format check + type checking) — use in CI
check:
    uv run ruff check src/app.py
    uv run black --check src/app.py
    uv run mypy src/app.py
    uv run ty check src/app.py

# ── HTML/CSS/JS (Node) ───────────────────────────────────────────────────────
# templates/keystroke.html is excluded from prettier/eslint — Jinja2 {{ }} in <script> blocks.

# Format all HTML files (docs/ + templates/ except keystroke.html)
fmt-html:
    npx prettier --write "docs/*.html" templates/home.html templates/face.html templates/voice.html templates/signature.html templates/mouse.html

# Check HTML formatting without modifying
fmt-html-check:
    npx prettier --check "docs/*.html" templates/home.html templates/face.html templates/voice.html templates/signature.html templates/mouse.html

# Lint HTML structure across all files
lint-html:
    npx htmlhint "docs/*.html" "templates/*.html"

# Lint inline JavaScript across all eligible HTML files
lint-js:
    npx eslint "docs/*.html" templates/face.html templates/voice.html templates/signature.html templates/mouse.html

# Run all HTML/CSS/JS checks
check-html:
    npx prettier --check "docs/*.html" templates/home.html templates/face.html templates/voice.html templates/signature.html templates/mouse.html
    npx htmlhint "docs/*.html" "templates/*.html"
    npx eslint "docs/*.html" templates/face.html templates/voice.html templates/signature.html templates/mouse.html

# ── Documentation (MkDocs) ──────────────────────────────────────────────────

# Build the MkDocs documentation site to site/documentation/
docs:
    uv run mkdocs build

# Serve the MkDocs documentation locally with live reload
docs-serve:
    uv run mkdocs serve

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
    uv run pytest --cov=src.app --cov-report=term-missing --cov-report=html:htmlcov

# Check coverage meets the minimum threshold without opening the report
coverage-check:
    uv run pytest --cov=src.app --cov-report=term-missing --cov-fail-under=80

# ── Pre-commit ───────────────────────────────────────────────────────────────

# Run all pre-commit hooks against every file
pre-commit:
    uv run pre-commit run --all-files

# Install pre-commit hooks into .git
pre-commit-install:
    uv run pre-commit install

# ── GitHub Pages static site (docs/) ────────────────────────────────────────

# Sync auto-generated docs pages from templates (home + face/voice/signature).
# docs/keystroke.html and docs/mouse.html are maintained separately (localStorage, no Flask backend).
sync-docs:
    #!/usr/bin/env python
    import shutil, subprocess
    shutil.copy('templates/face.html', 'docs/face.html')
    shutil.copy('templates/voice.html', 'docs/voice.html')
    shutil.copy('templates/signature.html', 'docs/signature.html')
    content = open('templates/home.html', encoding='utf-8').read()
    content = content.replace('href="/keystroke"',  'href="./keystroke.html"')
    content = content.replace('href="/face"',       'href="./face.html"')
    content = content.replace('href="/voice"',      'href="./voice.html"')
    content = content.replace('href="/signature"',  'href="./signature.html"')
    content = content.replace('href="/mouse"',      'href="./mouse.html"')
    open('docs/index.html', 'w', encoding='utf-8').write(content)
    subprocess.run('npx prettier --write docs/face.html docs/voice.html docs/signature.html docs/index.html', shell=True, check=True)
    print('Synced and formatted: docs/index.html, docs/face.html, docs/voice.html, docs/signature.html')
    print('Note: docs/keystroke.html and docs/mouse.html are maintained separately (localStorage-only, no Jinja2).')

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
