# README and Adoption Strategy

This document records how ASF should present itself and how people can discover it.

## README Strategy

The README should answer four questions quickly:

1. What is ASF?
2. Why does it exist?
3. How does the format look?
4. What is outside the scope?

The first screen should avoid workflow-engine language. It should say:

> Agent Skill Format (ASF) is a portable YAML + Markdown format for defining agent skills.

Then it should immediately show a small `SKILL.md` example.

## Positioning

ASF should position itself as a small extension to the emerging `SKILL.md` convention, not as a competing runtime.

Good framing:

- portable skill artifacts
- execution hints
- host-owned runtime state
- hook-friendly metadata

Avoid:

- workflow engine
- orchestrator
- daemon
- replacement for Codex, Claude Code, or OpenCode

## Audience

Primary audience:

- people writing reusable agent skills
- maintainers of agent harnesses
- teams building internal skill libraries

Secondary audience:

- package managers and registries for skills
- security reviewers
- documentation authors

## Awareness Plan

### 1. Publish a Crisp GitHub Repository

The repo should contain:

- README with minimal examples
- `spec/asf-v0.1.md`
- runtime-state design
- roadmap and weaknesses
- examples

The repository should be easy to read without installing anything.

### 2. Create Compatibility Examples

Show the same skill working conceptually in:

- Codex
- Claude Code
- OpenCode

Do not claim full compatibility until a host adapter exists.

### 3. Write a Short Announcement

Recommended title:

> Agent Skill Format: a small execution extension for SKILL.md

Core message:

- `SKILL.md` is becoming the portable skill artifact.
- Basic metadata is not enough for composed skills.
- ASF adds minimal execution declarations.
- State remains host-owned.

### 4. Ask for Review from Skill Authors

The first feedback should come from people already maintaining skills. Questions:

- Is `execution.calls` understandable?
- Is `skill` versus `step` clear?
- Is `ask_user` too small or useful enough?
- Does session-scoped state match how agents really work?

### 5. Avoid Overclaiming

ASF should not claim to be a universal standard before adoption.

Use language like:

- draft
- proposal
- candidate format
- reference contract

Avoid:

- industry standard
- official standard
- works everywhere

## Success Criteria

ASF is useful if:

- a person can read a composed skill without searching prose for order
- a host can parse the execution path without custom per-skill code
- hooks can identify whether a step is allowed to stop
- runtime state can stay outside shared skill files
- the format stays small enough to implement
