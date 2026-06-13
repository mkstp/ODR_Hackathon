# Tests

## Running Tests

Activate the virtual environment first:

```
source .venv/bin/activate
```

Run the full test suite:

```
pytest tests/
```

Run a specific test file:

```
pytest tests/ [test file path]
```

## Directory Structure

```
tests/
├── manifest.json         — traceability map (VCs, DELs, MODs → test files)
├── README.md             — this file
├── conftest.py           — shared fixtures and configuration
├── validation/           — tests derived from validation conditions (VC-NNN)
├── deliverables/         — tests verifying deliverable outputs (DEL-NNN)
├── unit/                 — module-level tests (MOD-NNN)
└── integration/          — cross-module and boundary tests
```

## Adding New Tests

1. Identify the VC-NNN, DEL-NNN, or MOD-NNN the test relates to
2. Place the test file in the appropriate subdirectory
3. Update `manifest.json` to register the new test and its traceability links
4. Follow the stub template in `.claude/skills/code-scaffold/references/test_stub.md`

## Traceability

See `manifest.json` for the full traceability map linking tests to validation conditions, deliverables, and modules. Every test should be traceable to at least one entry in the manifest.
