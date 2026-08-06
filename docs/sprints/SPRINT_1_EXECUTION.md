# 🚀 Sprint 1 Execution Guide

Welcome to **Sprint 1**! This guide outlines our execution rules, issue labeling system, contribution workflow, and collaboration expectations for all team members.

---

## 🏷️ Issue Labeling System

Every issue assigned to Sprint 1 carries exactly **one** of the following three execution labels to define how work should be distributed:

| Label | Scope | Description & Execution Expectation |
| :--- | :--- | :--- |
| `all` | **Mandatory for Everyone** | Every contributor must complete this task individually in their own development environment. |
| `solo` | **Single Assignee** | The issue is assigned to and completed by **one** contributor. |
| `multiple` | **Open / Multi-Contributor** | Multiple contributors can work on this task simultaneously. Each contributor may bring their own strategy and vision for implementation. |

> ⚠️ **Important Requirement for `multiple` Issues:**
> If you work on an issue labeled `multiple`, you are responsible for ensuring that your individual contribution integrates cleanly into the codebase, passes all pipeline checks, and works well without breaking existing functionality.

---

## 📋 Sprint 1 Issues Overview

Below are the core issues designated for Sprint 1 execution:

1. **Monorepo Setup & Local Tooling Standardization**
2. **Microservice Template & Architecture Blueprint**
3. **CI/CD Pipeline & Quality Gate Configuration**
4. **Environment Setup & Developer Onboarding**

---

## 🛠️ How to Pick Up & Volunteer for an Issue

To maintain clear ownership and avoid overlapping effort:

1. **Browse Sprint 1 Issues:** Check the repository's Issue Board for active Sprint 1 tasks.
2. **Declare Intent:** Comment directly on the issue ticket stating that you want to work on it (e.g., *"I would like to volunteer for this issue"*).
3. **Assignment:** A maintainer will assign the ticket to you, and you can begin work in a dedicated feature branch (`feat/issue-title` or `fix/issue-title`).

---

## 💡 Key Execution Rules & Collaboration

### 1. Special Note on: *Monorepo Setup & Local Tooling Standardization*
If you are working on or onboarding with the **Monorepo Setup & Local Tooling Standardization** issue, reach out to **Aymen** for context, guidance, or troubleshooting.
* **How to ask for help:** Comment directly on the issue ticket, clearly stating your question, environment details, or the specific problem you are encountering.

### 2. Peer Support & Helping Others
Collaborative problem-solving is strongly encouraged. If you see a teammate struggling or asking questions on an issue ticket or PR, jump in to help! Reviewing PRs, sharing debugging insights, and offering assistance accelerates the entire team's progress.

---

## 🔄 Contribution Workflow Checklist

Before submitting your work for any issue:

- [ ] Volunteer by commenting on the issue ticket first.
- [ ] Create a feature branch off `develop` / `main`.
- [ ] Follow local pre-commit hooks and Conventional Commit standards (`feat:`, `fix:`, `chore:`).
- [ ] Ensure all local tests and type checks pass (`uv run pytest`, `uv run basedpyright`).
- [ ] Open a PR referencing the issue (e.g., `Closes #12`).
- [ ] Ensure CI pipeline status checks pass before requesting a review.
