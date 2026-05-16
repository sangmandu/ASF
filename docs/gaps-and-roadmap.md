# Weaknesses and Roadmap

ASF v0.1 is intentionally small. This document lists known weaknesses and possible improvements.

## Known Weaknesses

### `ask_user` Is Too Small for Long-Term Use

`ask_user: true` is a minimal hint. It does not define the type of input required, valid responses, confirmation criteria, or resume behavior.

Future versions may replace or extend it with typed gates.

### Step Paths Are Not Stable Public IDs

ASF v0.1 uses step file paths as call path entries. This keeps the format simple, but file renames can break persisted state.

Future versions may add optional stable call IDs after real use shows the right shape.

### No Output Contracts

ASF v0.1 does not declare required artifacts or validation checks. A runtime can know the current step, but cannot prove that the step produced the right output.

Future versions may add output declarations.

### No Event Journal

ASF v0.1 allows a snapshot. Snapshots are easy, but they lose history and are weaker under crashes.

Future production runtimes may use append-only events plus a materialized snapshot.

### No Locking or Lease Model

ASF v0.1 assumes one active session owns one active state file. It does not define locking, leases, or concurrent mutation protection.

Future versions may define optional locks for multi-terminal safety.

### No Universal Hook Payload

Codex, Claude Code, OpenCode, and other hosts expose different hook semantics. ASF v0.1 does not try to standardize those events.

Future work may define host adapter contracts instead of forcing all hosts to share one payload.

### No Branching or Retry

ASF v0.1 supports ordered calls only. It does not define conditional branching, retry loops, skipping, or parallel calls.

This is deliberate. Branching should not be added until the linear composition model is proven.

## Roadmap

### v0.1

- Define base artifact shape.
- Add `execution.calls`.
- Distinguish `skill` and `step`.
- Define `ask_user` as a minimal step-level hint.
- Define session-scoped state as a runtime responsibility.

### v0.2 Candidate

- Add optional `schema_version`.
- Add optional stable call IDs.
- Define richer user gates.
- Add basic output artifacts.
- Add reference parser conformance tests.

### v0.3 Candidate

- Define host adapter expectations.
- Add event journal recommendation.
- Add crash recovery guidance.
- Add runtime conformance tests.

### v1.0 Candidate

- Freeze core fields.
- Publish compatibility levels.
- Provide reference implementations for major hosts.
- Establish a registry or discovery story only if the format has real adoption.

## Main Risk

The main risk is pretending that a file format alone can enforce a workflow.

ASF should stay honest: the artifact declares intent; the host runtime enforces behavior.
