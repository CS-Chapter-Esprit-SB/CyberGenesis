# CyberGenesis

CyberGenesis is a monorepo for the client, server, data management, and monitoring components of the project.

## Repository layout
- `client/` — client-facing services and example packages
- `server/` — backend services and APIs
- `data_management/` — data ingestion, storage, and ETL workflows
- `monitoring/` — observability and monitoring utilities
- `docs/` — architecture, environment, and sprint documentation

## Developer setup
1. Install Python 3.12 and `uv`.
2. Clone the repository and enter the workspace root:
   ```bash
   git clone <repo-url>
   cd CyberGenesis
   ```
3. Create and sync the development environment:
   ```bash
   uv sync --group dev
   ```
4. Install the repository hooks:
   ```bash
   uv run pre-commit install --install-hooks
   ```
5. Run the checks locally before committing:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run basedpyright
   uv run pytest
   ```

## Tooling standards
- Ruff is configured in `pyproject.toml` for linting and formatting.
- Basedpyright is configured for repository-wide type checking.
- Pre-commit hooks enforce trailing whitespace cleanup, EOF formatting, Ruff checks, and pytest validation.

## Additional guidance
- Follow the repository structure described in [docs/folder_structure.md](docs/folder_structure.md).
- Refer to [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) for environment-specific details.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution conventions and pull request expectations.

## License
This project is licensed under the terms in [LICENSE](LICENSE).
