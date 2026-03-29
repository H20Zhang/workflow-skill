# workflow-skill

[![CI](https://img.shields.io/github/actions/workflow/status/H20Zhang/workflow-skill/ci.yml?branch=main&label=ci)](https://github.com/H20Zhang/workflow-skill/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/actions/workflow/status/H20Zhang/workflow-skill/release.yml?label=release)](https://github.com/H20Zhang/workflow-skill/actions/workflows/release.yml)
[![License](https://img.shields.io/github/license/H20Zhang/workflow-skill)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](pyproject.toml)

`workflow-skill` is a typed Python library for turning a constrained workflow specification into an enforced finite state machine for agent execution.

Use it when you need a workflow that can reject invalid specs early, block illegal transitions at runtime, and leave behind an auditable execution trace instead of a best-effort orchestration story.

## Why This Exists

Most agent workflows describe phases like "plan", "execute", and "finish", but they do not actually enforce them.

`workflow-skill` treats the workflow itself as a runtime contract:

- the workflow is authored in a constrained natural-language format
- the spec is normalized into a validated FSM
- invalid or ambiguous specs are rejected before execution starts
- sessions can only take declared transitions
- state and transition skills can gate progress with explicit checks
- terminal completion requires both a terminal state and explicit goal completion

## Install

Install directly from GitHub:

```bash
python3 -m pip install "git+https://github.com/H20Zhang/workflow-skill.git"
```

Install from a local checkout:

```bash
python3 -m pip install .
```

For development:

```bash
python3 -m pip install -e .[dev]
```

## Quickstart

```python
from pathlib import Path

from fsm_agent import FSMSession, build_fsm, default_skill_registry

spec_text = Path('examples/research_workflow.txt').read_text(encoding='utf-8')
registry = default_skill_registry()
fsm = build_fsm(spec_text, skill_registry=registry)

session = FSMSession(
    fsm,
    final_goal='Deliver a validated answer to the user',
    skill_registry=registry,
)

session.context.data['notes'] = 'Captured request constraints.'
session.advance(to_state='plan')

session.context.data['plan_ready'] = True
session.advance(to_state='execute')

session.context.data['result'] = 'Validated implementation artifact.'
session.context.mark_goal_complete()
session.advance(to_state='done')

assert session.is_complete()
```

## CLI

Validate a workflow spec:

```bash
fsm-agent validate examples/research_workflow.txt --json
```

Run the end-to-end demo with guarded transitions:

```bash
PYTHONPATH=src python3 -m fsm_agent demo \
  examples/research_workflow.txt \
  --final-goal "Deliver a validated answer to the user" \
  --actions examples/research_workflow_actions.json \
  --json
```

The `demo` command executes the workflow, applies registered skills, enforces guard checks, and emits a structured runtime trace.

## What You Get

- strict parsing for a constrained workflow format
- validation of initial state, terminal states, and transitions
- deterministic runtime progression through declared edges only
- optional state and transition skills for scoped execution checks
- structured session snapshots for auditability and tooling

## Accepted Specification Format

```text
goal: <explicit final goal>
initial_state: <state>
terminal_states: <terminal state>[, <terminal state>...]

state: <name>
  instructions:
    - <instruction>
  state_skills: skill_a, skill_b
  transitions:
    - to: <target state>
      when: <optional human-readable condition>
      guidance: <required next-phase guidance>
      skills: skill_x, skill_y
```

The parser is intentionally strict. This package is a controlled normalization and enforcement layer, not a permissive natural-language interpreter.

## Runtime Model

- `FSMSession` always starts in the validated initial state
- the runtime requires the explicit final goal again at session creation time
- only declared outgoing transitions can be selected
- transition skills can block legal edges until runtime conditions are satisfied
- state skills add scoped instructions when entering a state
- terminal completion requires both a terminal state and `goal_status == 'complete'`

## Project Layout

```text
.
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
├── docs/
├── examples/
├── src/
│   └── fsm_agent/
├── tests/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── RELEASING.md
├── SECURITY.md
└── pyproject.toml
```

## Development Commands

```bash
make dev
make format
make lint
make typecheck
make test
make check
make build
make demo
```

## Release Process

See [`RELEASING.md`](RELEASING.md) for:

- GitHub release and branch protection guidance
- tag-based release flow
- PyPI Trusted Publishing setup

## Scope Boundaries

This package does not try to:

- infer highly ambiguous workflow text
- repair underspecified FSMs automatically
- integrate with a specific external agent framework
- provide distributed execution, persistence, or UI dashboards

## Contributing and Support

- Contribution guide: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Security policy: [`SECURITY.md`](SECURITY.md)
- Support guide: [`SUPPORT.md`](SUPPORT.md)

## License

MIT. See [`LICENSE`](LICENSE).
