# Contributing

Thank you for contributing! This document explains how to set up a development environment, run tests, and create high-quality PRs.

Local setup
1. Clone the repo and create a virtual environment:

```bash
git clone <repo-url>
cd cs_and_atia
cd <your_working_folder>
uv init <project-name>
uv add pre-commit --dev
```

Code style and checks
- We use `ruff` (configured in `pyproject.toml`) for linting.
- Run linters locally before committing.

Testing
- Run `pytest` from the repository root.
- Tests should live alongside packages under `*/tests` or `*/test` following `pyproject.toml` patterns.

Branching and PRs
- Create a feature branch from `main` named `feature/short-description`.
- Keep changes small and focused.
- Include tests for new behavior and update docs when applicable.
