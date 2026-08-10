## issue ID
resolve #3

## 📝 Description

Add a new microservice `client_by_ahmed` under the `client/` directory following the project microservice template. The service includes utility functions (`add`, `is_even`, `reverse_string`) with full test coverage.

---


## 🔍 Type of Change

Select the type of change that best fits your PR:

- [ ] 🐛 **Bug Fix** (non-breaking change fixing an issue)
- [x] ✨ **New Feature** (non-breaking change adding functionality)
- [ ] 🚨 **Breaking Change** (fix/feature that breaks existing behavior)
- [ ] 🧹 **Refactoring / Maintenance** (code cleanup, performance, or internal changes)
- [ ] 📚 **Documentation** (updates to docs, READMEs, or guides)
- [ ] ⚙️ **CI/CD & Tooling** (updates to GitHub Actions, pre-commit, or build scripts)

---

## 📌 Affected Microservices / Modules

Specify which parts of the workspace are modified:

- [x] `client/*`
- [ ] `server/*`
- [ ] `data_management/*`
- [ ] `monitoring/*`
- [ ] **Root Config / Shared Tooling**

---

## 🧪 How Has This Been Tested?

Describe the testing process used to verify these changes:

- [x] Local unit tests (`uv run pytest`)
- [x] Type checks (`uv run basedpyright`)
- [x] Linting & formatting checks (`uvx ruff check .`)
- [ ] Docker build validation (`docker build .`)

> **Steps to reproduce tests locally:**
> ```bash
> cd client/client_by_ahmed
> uv sync --all-extras --dev
> uv run pytest
> ```

---

## ✅ Checklist

Before submitting your PR, complete the following checks:

- [x] My code follows the project's style guidelines (`ruff` and `basedpyright` pass locally).
- [x] I have run `pre-commit` hooks prior to committing.
- [x] I have added/updated tests where applicable.
- [x] All new and existing tests pass locally.
- [ ] I have updated relevant documentation or inline comments.
- [ ] If modified, the `Dockerfile` builds without errors.
