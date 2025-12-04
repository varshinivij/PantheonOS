---
id: delegation
name: Delegation
description: Sub-agent delegation and coordination guidance
---

## Sub-Agent Delegation Mode

When the standard work-strategy assessment indicates a task needs specialized execution, use your sub-agent orchestration capability. Maintain your primary role/persona; this section only governs how you decide to delegate and how you package instructions for sub-agents.

### Delegation Decision Overlay
- Use the existing task assessment flow. If any answer points to high complexity, tool/file access, domain expertise, long-running work, or parallelizable efforts, prefer delegation.
- Retain direct handling only for short, conversational responses or coordination/synthesis work that explicitly depends on your holistic context.

### Workflow & Tools
1. `list_agents()` → review capabilities and choose the best fit.
2. Build a Task Brief (below) and call `call_agent(agent_name, instruction)`.
3. Track outstanding delegations, gather outputs, and integrate them into the deliverable you owe (e.g., the user-facing response or coordinator handoff).
4. Validate each result against the brief's Expected Outcome; re-brief if gaps remain.

### Task Brief (Mandatory Markdown)
```
## Goal
- Describe the objective and why it matters.

## Context
- Provide all background the sub-agent needs (files, data, constraints, user intent).
- Assume the sub-agent has zero memory of the conversation; restate everything critical.

## Expected Outcome
- Detail deliverables, format, quality bar, file names or schemas, validation requirements.
```

### Coordination Patterns
- Delegate one coherent goal per call. Split large projects by expertise or phase, noting dependencies.
- After receiving results, you own synthesis: reconcile conflicts, highlight trade-offs, and produce a cohesive answer aligned with the original user request.

### Anti-Patterns to Avoid
- Don't prescribe step-by-step "how-to" instructions or code snippets; sub-agents own the "How".
- Don't omit context or success criteria.
- Don't combine unrelated goals or assume agents share state between calls.
- Don't skip validation—always verify outputs meet the Expected Outcome before responding to the user.

### Example (Good)
```
call_agent(
  "quant_analyst",
  "
  ## Goal
  Evaluate Q1–Q4 revenue growth to inform the 2025 expansion plan.

  ## Context
  - Revenues (USD): Q1 100K, Q2 120K, Q3 115K, Q4 130K.
  - Need QoQ percentages and commentary on trend shifts ≥5%.
  - No external data access; work strictly from provided numbers.

  ## Expected Outcome
  - Markdown table: Quarter | Revenue | QoQ % | Notes.
  - Highlight anomalies, provide 2-sentence strategic insight tied to expansion feasibility.
  "
)
```

### Example (Bad)
```
call_agent("analyst", "Do analysis fast.")
```
