## issue ID
pattern : (resolve/fix/close)#number
-
## 📝 Description

Briefly describe the changes introduced by this pull request. Mention why these changes are necessary and what problem they solve.

---


## 🔍 Type of Change

Select the type of change that best fits your PR:

- [ ] 🐛 **Bug Fix** (non-breaking change fixing an issue)
- [ ] ✨ **New Feature** (non-breaking change adding functionality)
- [ ] 🚨 **Breaking Change** (fix/feature that breaks existing behavior)
- [ ] 🧹 **Refactoring / Maintenance** (code cleanup, performance, or internal changes)
- [ ] 📚 **Documentation** (updates to docs, READMEs, or guides)
- [ ] ⚙️ **CI/CD & Tooling** (updates to GitHub Actions, pre-commit, or build scripts)

---

## 📌 Affected Microservices / Modules

Specify which parts of the workspace are modified:

- [ ] `client/*`
- [ ] `server/*`
- [ ] `data_management/*`
- [ ] `monitoring/*`
- [ ] **Root Config / Shared Tooling**

---

## 🧪 How Has This Been Tested?

Describe the testing process used to verify these changes:

- [ ] Local unit tests (`uv run pytest`)
- [ ] Type checks (`uv run basedpyright`)
- [ ] Linting & formatting checks (`uvx ruff check .`)
- [ ] Docker build validation (`docker build .`)

> **Steps to reproduce tests locally:**
> ```bash
> cd path/to/service
> uv sync --all-extras --dev
> uv run pytest
> ```

---

## ✅ Checklist

Before submitting your PR, complete the following checks:

- [ ] My code follows the project's style guidelines (`ruff` and `basedpyright` pass locally).
- [ ] I have run `pre-commit` hooks prior to committing.
- [ ] I have added/updated tests where applicable.
- [ ] All new and existing tests pass locally.
- [ ] I have updated relevant documentation or inline comments.
- [ ] If modified, the `Dockerfile` builds without errors.
