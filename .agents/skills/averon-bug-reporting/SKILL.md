---
name: averon-bug-reporting
description: Use when QA or review discovers a visual, gameplay, or technical defect.
---

# Report and retest defects

1. Establish factual observation and scope first; avoid assigning speculative root cause based only on a screenshot.
2. Capture exact source commit/ROM checksum, mGBA version, save or fixture state, map/location, action sequence and screenshots if safe to publish.
3. State observed vs expected behavior separately; classify severity and reproducibility.
4. Link owning PR or issue and relevant file ownership, without editing another agent's feature branch.
5. If a proposed cause is inferred, label it hypothesis and describe what evidence would distinguish alternatives.
6. After new ROM build, repeat same steps and mark FIXED, STILL FAILING, or NOT RETESTED. Do not equate CI green with rendered correctness.

## Authority

Current code and live PRs override past notes and generated indices. Follow root/project AGENTS.md, development/AGENT_ROLES.md, WORKFLOW.md and issue #15. Preserve existing developer claims.
