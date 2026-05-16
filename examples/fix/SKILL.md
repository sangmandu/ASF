---
name: fix
description: Diagnosis-first bug fix workflow.
execution:
  calls:
    - skill: diagnosis
    - skill: code
---

# Fix

Use this skill when a reported bug needs evidence-backed diagnosis before implementation.

Run the `diagnosis` skill first. After the fix contract is confirmed, run the `code` skill.
