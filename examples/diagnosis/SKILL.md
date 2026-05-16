---
name: diagnosis
description: Evidence-first diagnosis workflow.
execution:
  calls:
    - step: 001-capture-classify.md
    - step: 002-reference-check.md
    - step: 007-explain-confirm.md
      ask_user: true
---

# Diagnosis

Use this skill to turn a bug report into a confirmed fix contract.
