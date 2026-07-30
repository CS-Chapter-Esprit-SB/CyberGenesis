# Microservices Architecture Monorepo

Welcome to the project repository! This repository uses a monorepo structure containing four distinct operational layers, built with **FastAPI**, **Docker**, **uv**, and static code analysis tools.

---

## 📂 Repository Directory Structure

```text
.
├── .github/
│   ├── CODEOWNERS             # Restricts PR approvals to @org/mentors
│   └── workflows/
│       └── ci.yml             # Matrix CI pipeline for Ruff, Pytest & Docker builds
│
├── client/                     # Layer 1: Client facing microservices
│       └── client_by_<name>/
│           ├── src/
│           │   └── client_by_<name> /       # FastAPI application code
│           ├── test/          # Service unit and integration tests
│           ├── Dockerfile     # Microservice container definition
│           └── pyproject.toml # Service-specific dependencies (FastAPI, etc.)
│
├── server/                     # Layer 2: Core server / business logic services
│       └── server_by_<name>/
│           ├── src/
│           │   └── server_by_<name>/
│           ├── test/
│           ├── Dockerfile
│           └── pyproject.toml
│
├── data_management/            # Layer 3: Data layer microservices
│       └── data_managment_by_<name>/
│           ├── src/
│           │   └── data_managment_by_<name>/
│           ├── test/
│           ├── Dockerfile
│           └── pyproject.toml
│
├── monitoring/                 # Layer 4: Monitoring and observability services
│       └── monitor_by_<name>/
│           ├── src/
│           │   └── monitor_by_<name>/
│           ├── test/
│           ├── Dockerfile
│           └── pyproject.toml
│
├── docs/
│   └── servicename_projectname.md
├── monitoring/
│   └──.pre-commit-config.yaml     # Global pre-commit configuration
├── pyproject.toml              # ROOT TOOLING ONLY (Ruff, Basedpyright, Pytest)
└── README.md
