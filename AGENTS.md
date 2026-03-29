# Repository Guidelines

## Project Structure & Module Organization
Core package code lives in `src/fsm_agent/`. Key modules include `parser.py`, `validator.py`, `runtime.py`, and `api.py`; the CLI entry point is `src/fsm_agent/__main__.py`. Tests live in `tests/` and follow the public surface closely, for example `tests/test_parser.py` and `tests/test_runtime.py`. Example workflow specs and demo inputs live in `examples/`. Release and contributor docs are at the repo root plus `docs/`.

Ignore generated artifacts in `build/`, `dist/`, `dist_sdist/`, `dist_smoke/`, and `src/*.egg-info` when making source changes.

## Build, Test, and Development Commands
Use the Make targets instead of ad hoc commands where possible:

- `make dev`: install the package in editable mode with dev tools.
- `make format`: run Ruff formatter.
- `make lint`: run Ruff lint checks.
- `make typecheck`: run strict MyPy on `src` and `tests`.
- `make test`: run the unittest suite with verbose output.
- `make check`: run lint, typecheck, and tests together.
- `make build`: build sdist and wheel via `python -m build`.
- `make demo`: execute the sample FSM workflow from `examples/`.

## Coding Style & Naming Conventions
Python requires 4-space indentation; other text files default to 2 spaces, and `Makefile` entries must use tabs. Ruff enforces formatting, import sorting, and core lint rules; line length is `120` and quotes should stay single-quoted where formatter-supported. MyPy runs in `strict` mode, so keep annotations complete and public APIs typed.

Use `snake_case` for modules, functions, variables, and test names. Keep new modules inside `src/fsm_agent/` focused and small rather than introducing parallel package trees.

## Testing Guidelines
Add or update tests for every behavior change, especially parsing, validation, transition guards, and CLI behavior. Name tests `test_*.py` and keep fixtures reusable in `tests/spec_fixtures.py` when appropriate. Run `make check` before opening a PR; run `make demo` when workflow execution behavior changes.

## Commit & Pull Request Guidelines
This checkout does not include `.git` history, so follow the repository’s documented convention: prefer small, reviewable commits, and use Conventional Commits when practical. Pull requests should keep scope focused, include tests for behavior changes, update docs for user-visible changes, keep changelog or release metadata accurate, and never merge with failing CI. Security-sensitive changes to parsing, validation, guards, packaging, or release automation should get an extra review.
