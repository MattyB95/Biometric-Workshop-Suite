# Contributing

Contributions that improve the educational value of the suite are welcome. See the full [CONTRIBUTING.md](https://github.com/MattyB95/Biometric-Workshop-Suite/blob/main/CONTRIBUTING.md) in the repository for detailed setup instructions, code style guidance, and the PR process.

## Quick reference

### Setup

```bash
git clone https://github.com/MattyB95/Biometric-Workshop-Suite.git
cd Biometric-Workshop-Suite
uv sync
uv run pre-commit install
```

### Running tests

```bash
just test-py        # unit + API tests (fast)
just test           # all tests including Playwright browser tests
just coverage       # tests with coverage report
```

### Code quality

```bash
just fmt            # format Python (black + ruff)
just lint           # lint Python (ruff)
just typecheck      # type check (mypy + ty)
just check          # all checks combined (used in CI)
```

### Key principles

- Keep the Flask app (`templates/`) and the static site (`docs/`) in sync for shared features.
- Every new API endpoint needs tests — coverage must stay at 100%.
- The project is for education: prefer clarity and explainability over algorithmic sophistication.

## Reporting issues

Use the [GitHub issue tracker](https://github.com/MattyB95/Biometric-Workshop-Suite/issues). Bug report and feature request templates are provided.
