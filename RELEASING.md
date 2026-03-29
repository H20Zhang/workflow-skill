# Releasing

This repository is set up for a conventional GitHub + PyPI release flow.

## Recommended GitHub repository settings

These are important and cannot be fully enforced by files alone:

1. protect the default branch
2. require pull requests before merge
3. require at least one approving review
4. require CI status checks to pass before merge
5. block force pushes and branch deletion on the default branch
6. require conversation resolution before merge
7. restrict who can dismiss reviews if your team model supports it

## Pre-release checklist

- update `CHANGELOG.md`
- confirm version in `pyproject.toml` and `src/fsm_agent/__init__.py`
- run `make check`
- run `make build`
- run `make demo`
- verify CI passes on the release commit

## Tag-based release flow/

1. merge the release commit into the default branch
2. create an annotated tag like `v0.2.0`
3. push the tag
4. GitHub Actions builds sdist and wheel
5. the release workflow publishes to PyPI using Trusted Publishing

## PyPI Trusted Publishing

Configure the PyPI project to trust the GitHub Actions workflow file used by `.github/workflows/release.yml`.

## Post-release

- verify the published wheel and sdist on PyPI
- create or update GitHub release notes
- start the next changelog entry under `Unreleased`
