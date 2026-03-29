# GitHub Presentation Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository read like a polished Python library landing page on GitHub, remove public-facing repository noise, validate the package, and publish the resulting branch to GitHub.

**Architecture:** Keep the package behavior intact and focus on repository presentation surfaces. The work centers on top-level docs, packaging metadata, tracked artifact cleanup, verification, and the GitHub publication flow, with each change kept small and reviewable.

**Tech Stack:** Python 3.11+, setuptools, Ruff, MyPy, unittest, GitHub Actions, git, gh

---

## File Map

- Modify: `README.md`
- Modify: `pyproject.toml`
- Review/possibly modify: `CONTRIBUTING.md`
- Review/possibly modify: `SECURITY.md`
- Review/possibly modify: `SUPPORT.md`
- Delete if tracked: `tests/__pycache__/...`
- Delete if tracked: `src/fsm_agent/__pycache__/...`
- Delete if tracked: `src/workflow_skill.egg-info/...`
- Delete if tracked: `src/fsm_agent_ref.egg-info/...`

### Task 1: Audit tracked repository noise and lock cleanup scope

**Files:**
- Review: `tests/__pycache__/`
- Review: `src/fsm_agent/__pycache__/`
- Review: `src/workflow_skill.egg-info/`
- Review: `src/fsm_agent_ref.egg-info/`
- Verify: `.gitignore`

- [ ] **Step 1: Confirm which generated artifacts are actually tracked**

Run: `git ls-files tests src | rg '__pycache__|\\.egg-info'`
Expected: A concrete list of generated files that should be removed from version control.

- [ ] **Step 2: Verify ignore coverage before deletion**

Run: `sed -n '1,220p' .gitignore`
Expected: Ignore rules include `__pycache__/` and `*.egg-info/` so cleanup stays stable.

- [ ] **Step 3: Remove only the tracked generated artifacts**

Run:

```bash
git rm -r tests/__pycache__ src/fsm_agent/__pycache__ src/workflow_skill.egg-info src/fsm_agent_ref.egg-info
```

Expected: Only generated caches and egg-info directories are staged for deletion.

- [ ] **Step 4: Verify cleanup scope**

Run: `git status -sb`
Expected: Deletions are limited to generated artifacts and no source files were removed.

### Task 2: Restructure the README for first-minute comprehension

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Review the current README structure**

Run: `sed -n '1,260p' README.md`
Expected: Existing content emphasizes technical detail before quick comprehension.

- [ ] **Step 2: Rewrite the top-level README content**

Update `README.md` so the opening follows this structure:

```md
# workflow-skill

[badge block]

`workflow-skill` is a typed Python library for turning a constrained workflow spec into an enforced finite-state machine for agent execution.

Use it when you need a workflow that can reject invalid specs early, block illegal transitions at runtime, and produce an auditable execution trace.

## Why It Exists

- Generic "plan/act/finish" flows are usually advisory.
- This package makes the workflow executable and enforceable.
- Terminal completion requires both legal state progression and explicit goal completion.

## Install

```bash
python3 -m pip install workflow-skill
```

## Quickstart

```python
from fsm_agent import build_fsm, FSMSession, default_skill_registry
```
```

Expected: The README becomes landing-page-first, with technical reference content moved lower rather than deleted.

- [ ] **Step 3: Add trust signals only for real repository state**

Add a compact badge block near the top, using only verifiable signals such as CI workflow, release workflow, license, and Python support reflected in `pyproject.toml`.

- [ ] **Step 4: Preserve deeper technical reference sections lower on the page**

Keep sections such as spec format, runtime model, CLI usage, development commands, and release process after the quickstart material.

- [ ] **Step 5: Verify the new README reads clearly in plain text**

Run: `sed -n '1,260p' README.md`
Expected: The first screen explains what the package is, why it matters, and how to try it.

### Task 3: Align package metadata with the GitHub presentation

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Review the current package metadata**

Run: `sed -n '1,260p' pyproject.toml`
Expected: Metadata is broadly correct but may not be optimized for concise GitHub-facing positioning.

- [ ] **Step 2: Tighten the metadata wording if needed**

Update the `description`, `keywords`, and URL fields only if the new README positioning exposes mismatches. Keep the package name and release semantics unchanged.

Suggested description target:

```toml
description = "Typed Python FSM enforcement for agent workflows defined in constrained natural language."
```

- [ ] **Step 3: Verify metadata consistency**

Run: `sed -n '1,120p' pyproject.toml`
Expected: Package metadata reinforces the same positioning as the README and keeps the existing release URLs intact.

### Task 4: Align public root documentation with the new positioning

**Files:**
- Review/possibly modify: `CONTRIBUTING.md`
- Review/possibly modify: `SECURITY.md`
- Review/possibly modify: `SUPPORT.md`

- [ ] **Step 1: Review the public-facing root docs**

Run:

```bash
sed -n '1,220p' CONTRIBUTING.md
sed -n '1,220p' SECURITY.md
sed -n '1,220p' SUPPORT.md
```

Expected: The docs should be concise, public-ready, and consistent with the README tone.

- [ ] **Step 2: Edit only where the messaging is inconsistent**

If these docs already fit, leave them unchanged. If not, tighten wording so they read like public open source project documents rather than internal notes.

- [ ] **Step 3: Verify the documentation set is coherent**

Run: `find . -maxdepth 1 -type f | sort`
Expected: Root docs present a consistent public package surface without visible generated clutter.

### Task 5: Run full verification before publication

**Files:**
- Verify: `README.md`
- Verify: `pyproject.toml`
- Verify: repository worktree

- [ ] **Step 1: Run formatting**

Run: `make format`
Expected: Formatter completes successfully.

- [ ] **Step 2: Run lint, typecheck, and tests**

Run: `make check`
Expected: Ruff, MyPy, and unittest all pass.

- [ ] **Step 3: Run build validation**

Run: `make build`
Expected: Source and wheel distributions build successfully.

- [ ] **Step 4: Inspect the final diff and status**

Run:

```bash
git status -sb
git diff -- README.md pyproject.toml CONTRIBUTING.md SECURITY.md SUPPORT.md .gitignore
```

Expected: Only intended presentation and cleanup changes remain.

### Task 6: Publish the branch to GitHub

**Files:**
- Modify: git index and branch state
- Publish: remote `origin`

- [ ] **Step 1: Check GitHub CLI availability and auth**

Run:

```bash
gh --version
gh auth status
```

Expected: `gh` is installed and authenticated for the target GitHub account.

- [ ] **Step 2: Create or reuse the publication branch**

Run:

```bash
git branch --show-current
git checkout -b codex/github-presentation-optimization
```

Expected: Work moves off `main` to a dedicated publication branch.

- [ ] **Step 3: Commit the implementation changes intentionally**

Run:

```bash
git add README.md pyproject.toml CONTRIBUTING.md SECURITY.md SUPPORT.md tests/__pycache__ src/fsm_agent/__pycache__ src/workflow_skill.egg-info src/fsm_agent_ref.egg-info
git commit
```

Expected: One intentional commit captures the GitHub presentation optimization work.

- [ ] **Step 4: Push the branch**

Run: `git push -u origin codex/github-presentation-optimization`
Expected: The remote branch is available on GitHub.

- [ ] **Step 5: Open a draft PR**

Run:

```bash
gh pr create --draft --fill --head codex/github-presentation-optimization
```

Expected: A draft pull request is created against the repository default branch.

## Self-Review

- Spec coverage: This plan covers README restructuring, trust signals, tracked artifact cleanup, metadata alignment, verification, and GitHub publication.
- Placeholder scan: No `TODO`, `TBD`, or content-free implementation steps remain.
- Type consistency: Paths, commands, and publication branch naming are consistent across tasks.
