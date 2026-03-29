# Contributing

Thanks for contributing.

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Local checks

```bash
make format
make lint
make typecheck
make test
make build
make demo
```

Or run the full local gate:

```bash
make check
```

The `make test` and `make demo` targets export `PYTHONPATH=src`, so they work from a fresh clone before an editable install.

## Pull request expectations

- keep changes focused
- add or update tests for behavior changes
- update docs when public behavior changes
- keep release metadata and changelog entries accurate
- do not merge failing CI

## Design principles

- validation before execution
- rejection over guesswork for ambiguous workflow text
- deterministic runtime behavior
- explicit state and transition semantics
- auditable traces over hidden control flow

## Commit guidance

Prefer small, reviewable commits. Conventional Commits are recommended but not mandatory.

## Security-sensitive changes

If your change touches parsing, validation, transition guards, packaging, or release automation, request an extra review.
