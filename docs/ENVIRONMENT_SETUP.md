# Local Environment Setup Guide

This document outlines the required tools, extensions, and step-by-step instructions to set up your local development environment.

---

## 🛠️ Required Tools & Tech Stack

| Tool / Technology | Version / Type | Purpose |
| :--- | :--- | :--- |
| **VS Code** | Latest | Recommended IDE / Code Editor |
| **Python** | `3.12` | Runtime Environment |
| **`uv`** | Latest | Extremely fast Python package installer and virtual environment manager |
| **`pytest`** | Modern release | Testing framework |
| **`pre-commit`** | Modern release | Git hook manager for automated code quality checks |
| **Ruff** | VS Code Extension | Fast Python linter and code formatter |
| **Basedpyright** | VS Code Extension | Static type checker for Python |

---

## 📥 1. Prerequisites Installation

### A. Install VS Code & Python 3.12
1. Download and install **[Visual Studio Code](https://code.visualstudio.com/)**.
2. Download and install **[Python 3.12](https://www.python.org/downloads/)** (Ensure **"Add Python to PATH"** is checked during setup).

### B. Install Vscode Extention
1. Install ruff **[Extention](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)**
2. Install BasedRight **[Extention](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright)**

### C. Install `uv` Package Manager
`uv` replaces standard `pip` and `venv` workflows for significantly faster setup times.

* **macOS / Linux:**
  ```bash
  curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

* **powershell**
    ```bash
    powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"

### D. Install 3rd party tools
    ```bash
    uv tool install pre-commit
    pre-commit install
    pre-commit install --hook-type commit-msg
    # installing ruff
    uv tool install ruff

    # installing Basedright lsp

    uv tool install basedpyright
- check
