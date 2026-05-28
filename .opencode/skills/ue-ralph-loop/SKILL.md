---
name: ue-ralph-loop
description: Use when running an end-to-end autonomous Unreal Engine development loop from feature goal or spec through planning, implementation, validation, self-evaluation, and review handoff.
---

## Purpose

Use this skill when the user wants an Unreal Engine feature, fix, or change handled end-to-end with minimal intervention.
The goal is to coordinate a full Ralph Loop style workflow: spec readiness, planning, focused analysis, implementation, validation, self-evaluation, iteration, and reviewable handoff.

The preferred model is one bounded loop attempt per primary chat session. If an attempt fails or is incomplete, produce a durable re-entry packet and stop so the next attempt can begin from a fresh session with explicit evidence instead of stale assumptions.

This skill does not replace `ue-spec`, `ue-plan`, `ue-analyze`, `ue-implement`, or `ue-test`. It decides when to use those skills, how to move between them, and when to stop or loop back.

## Trigger Conditions

Use this skill when the user asks to run a full Unreal development loop from a feature goal, bug/fix request, implementation prompt, existing spec, or planned work item through implementation and validation.

Typical triggers include:

- "do the full loop"
- "take this from spec to working"
- "implement, test, and iterate"
- "handle this end to end"
- "autonomously build this"
- Ralph Loop style workflow requests

Do not use this skill for narrow single-phase requests:

- Use `ue-spec` for spec creation, refinement, or review only.
- Use `ue-plan` for implementation planning only.
- Use `ue-analyze` for analysis-only questions about existing behavior.
- Use `ue-implement` for direct implementation requests that do not require full loop orchestration.
- Use `ue-test` for validation-only requests.

## Core Outcome

Complete the smallest responsible end-to-end development loop and produce a reviewable result that includes:

- The interpreted goal and readiness status.
- The plan or task breakdown used for implementation.
- Evidence gathered from code, config, assets, logs, or tests where relevant.
- Code, config, and asset changes made.
- Build, Automation, TestPlay, editor, or manual validation results.
- Self-evaluation against the original goal and acceptance criteria.
- Remaining risks, skipped validation, blockers, and recommended next steps when needed.
- A re-entry packet for the next fresh session when the loop is not complete.

## Session Boundary Model

Prefer cross-session iteration over repeatedly retrying inside the same primary session.

Run one bounded loop attempt in the current session:

1. Re-read or reconstruct the current spec.
2. Update or create the implementation plan.
3. Re-analyze project context needed for the updated plan.
4. Implement the next smallest correct change set.
5. Validate and test.
6. Self-evaluate against the spec and plan.
7. Either finish, or write a re-entry packet for a new session.

Do not rely on memory from a previous failed attempt as authoritative. Treat prior attempts as evidence to inspect, not truth to repeat.

When beginning from a re-entry packet in a new session, re-run the Spec Gate and Plan Gate before implementation. The new session should verify that the carried-over spec, plan, failure evidence, and repository state still match the current project.

## Persistent Artifacts

For loops that are likely to span sessions, keep durable Markdown or JSON evidence outside generated engine outputs unless the user gives a different path.

Recommended locations:

- Specs: `Docs/Agent/Specs/<feature>.md` when the spec should be reviewed or reused.
- Plans: `Docs/Agent/Plans/<feature>.md` when the plan should be reviewed or reused.
- Re-entry packets: `Docs/Agent/RalphLoop/<feature>-iteration-<n>.md` for cross-session continuation.
- Temporary logs, command outputs, generated TestPlay specs, and result JSON: `Saved/`.

If the repository does not already use `Docs/Agent/`, ask before creating durable source-controlled documentation. If the user wants no new tracked docs, include the re-entry packet in the final response instead and keep generated evidence under `Saved/`.

## Loop Workflow

### 1. Spec Gate

Check whether the user's input is implementation-ready.

Ready inputs define observable behavior, target systems or discovery paths, major constraints, and some validation signal.

If requirements are unclear enough that different implementations would be valid, do not invent core behavior. Use `ue-spec` or ask focused questions before implementation.

Spec-blocking gaps include:

- Ambiguous player-facing or editor-facing behavior.
- Unknown target class, actor, component, widget, map, asset, or plugin when multiple candidates are plausible.
- Networking, persistence, save/load, replication, or authority requirements that materially affect implementation.
- Asset, UI, animation, input, or data ownership decisions that change the implementation surface.
- No observable acceptance criteria or validation path.

### 2. Plan Gate

Use `ue-plan` when the input is ready enough to turn into ordered implementation work.

The plan should identify:

- Code, config, asset, UI, animation, input, data, networking, persistence, plugin, or editor-tooling surface.
- Concrete files, classes, assets, config files, or discovery searches.
- Ordered tasks and dependencies.
- Code tasks that can run in parallel.
- Asset or editor automation tasks that must run sequentially.
- Validation mapped to acceptance criteria.
- Risks, assumptions, open questions, and blockers.

Skip writing a separate long plan only when the change is small enough that the plan would add no clarity. Still keep the task sequence explicit in your own todo list.

### 3. Analysis Gate

Use `ue-analyze` when correct implementation depends on existing runtime behavior, class ownership, config, Blueprint defaults, asset references, input mappings, widgets, animation, maps, or plugin behavior.

Keep analysis focused on decisions needed for implementation. Avoid broad project scans unless the plan requires them.

If asset evidence is needed but AssetToJson, the editor, or Python Remote Execution is unavailable, report the limitation and decide whether code-only work can safely continue.

### 4. Implementation Gate

Use `ue-implement` for source, config, and asset changes.

Implementation rules:

- Prefer minimal C++ or config changes when feasible.
- Avoid binary asset edits unless the feature clearly requires them.
- Keep `ue-code-writer` work parallel only when file scopes are independent.
- Keep `ue-asset-editor`, JsonToAsset, Unreal Remote Execution, package saves, and editor automation sequential.
- Inspect and integrate subagent results before considering implementation complete.
- Do not touch generated output under `Binaries/`, `Intermediate/`, `Saved/`, or `DerivedDataCache/` except for temporary evidence or generated validation artifacts under `Saved/`.

### 5. Validation Gate

Use `ue-test` after implementation.

Choose the smallest validation that can catch the likely regression:

- Build after C++ changes when possible.
- Run relevant Unreal Automation tests when they exist or were added.
- Run TestPlay PIE checks when runtime gameplay, input, actor state, or widgets need proof.
- Use editor or manual validation only when automation is unavailable or not cost-effective.

Do not claim success from a launched editor process alone. Report command exit codes, result JSON, logs, Automation reports, TaskEvidence, or other concrete evidence.

### 6. Self-Evaluation Gate

Compare the implementation and validation evidence against:

- The original user request.
- The spec or accepted assumptions.
- The implementation plan.
- Acceptance criteria.
- Unreal-specific risks such as reflected API compatibility, Blueprint defaults, serialized assets, networking authority, config redirects, and asset references.

Classify the result as:

- `Complete`: requirements are met and validation is sufficient for the requested scope.
- `Complete with residual risk`: requirements appear met but some validation or evidence is limited.
- `Partial`: useful work is done but one or more requirements remain incomplete.
- `Blocked`: progress cannot continue without user input, unavailable tools, editor/plugin state, build failure outside the task scope, or missing assets.

### 7. Loop Decision

If self-evaluation fails, loop back to the smallest necessary gate:

- Requirement ambiguity: return to Spec Gate.
- Bad task split or missing dependency: return to Plan Gate.
- Missing project evidence: return to Analysis Gate.
- Implementation defect: return to Implementation Gate.
- Insufficient proof: return to Validation Gate.

Prefer cross-session bounded iteration. By default, do not run another implementation-validation loop inside the same primary session after a meaningful failure. Instead, create a re-entry packet and stop so the next attempt can start in a fresh session.

An in-session retry is allowed only when the failure is small, mechanical, and immediately actionable, such as a simple compile error, missing include, formatting issue, typo, or incorrect command argument.

Do not run more than one in-session retry unless the user explicitly asks to keep going.

Stop and report when another loop would require guessing, broad refactoring, destructive commands, unrelated cleanup, or risky asset/config changes not covered by the user's request.

## Failure Re-Entry Protocol

When the loop is `Partial`, `Blocked`, or validation fails in a way that requires another real attempt, create a re-entry packet for the next fresh session.

The packet must be self-contained enough that a new agent session can continue without trusting hidden chat context.

Include:

- Original user goal and current feature name.
- Current spec path or embedded spec summary.
- Current plan path or embedded plan summary.
- What was implemented in this attempt.
- Files, assets, config, and generated evidence touched.
- Exact validation commands run and pass/fail results.
- First actionable failure, blocker, or unmet acceptance criterion.
- What assumptions should be rechecked next session.
- Recommended next session starting gate: Spec, Plan, Analysis, Implementation, or Validation.
- A copy-pasteable next-session prompt.

Use this template:

```text
# Ralph Loop Re-Entry: <Feature> Iteration <N>

## Goal
<Original user goal>

## Current Status
Partial | Blocked | Validation failed | Complete with residual risk

## Spec State
- Path: <spec path or none>
- Summary: <current intended behavior>
- Questions to recheck: <items>

## Plan State
- Path: <plan path or none>
- Last completed tasks: <tasks>
- Tasks needing revision: <tasks>

## Project Evidence
- Code/config/assets inspected: <paths>
- Relevant findings: <findings>

## Changes Made This Attempt
- <files/assets/config changed>

## Validation Evidence
- Command/test: <command>
- Result: <pass/fail/blocked>
- Logs/results: <paths>
- First actionable failure: <failure>

## Next Session Instructions
Start with `ue-ralph-loop`.
Re-read the spec and plan, revise the plan for the failure above, re-analyze any changed project context, then implement the next smallest fix and validate again.

## Suggested Prompt
Continue the Ralph Loop for <feature> from this re-entry packet. First re-check the spec and plan against the current repository state, then update the plan, analyze the needed project context, implement the next smallest fix, validate, self-evaluate, and either complete or produce the next re-entry packet.
```

## State Tracking

Use a todo list for non-trivial loops.

Track at least:

- Spec readiness.
- Plan or task breakdown.
- Required analysis scopes.
- Implementation tasks.
- Validation tasks.
- Self-evaluation.
- Final handoff.

Keep exactly one active task while work remains. Mark tasks complete only after the relevant evidence or edits are actually done.

## Delegation Guidance

Use existing Unreal subagents through their owning skills rather than bypassing the specialized workflows.

- Use `ue-code-reader` through `ue-analyze` for focused code/config evidence.
- Use `ue-asset-scanner` through `ue-analyze` for asset evidence.
- Use `ue-code-writer` through `ue-implement` for focused source/config changes.
- Use `ue-asset-editor` through `ue-implement` for JsonToAsset asset work.
- Use `ue-tester` through `ue-test` for focused validation.

The primary agent remains responsible for integration, cross-checking, loop decisions, and final reporting.

## Final Response Structure

Use the user's language unless they ask for another language.

For completed or partially completed loops, use this structure when it fits:

```text
## Outcome
Complete | Complete with residual risk | Partial | Blocked

## What Changed
- <Files, assets, config, or behavior changed>

## Validation
- <Commands/tests/editor checks run and results>

## Self-Evaluation
- <Whether the result satisfies the goal and acceptance criteria>

## Risks Or Gaps
- <Remaining risks, skipped validation, blockers, or next actions>
```

For blocked loops, lead with the blocker and the smallest user decision or environment change needed to proceed.

## Safety

- Follow `AGENTS.md` and project-specific Unreal rules.
- Never revert user changes without explicit permission.
- Do not run destructive git, editor, or filesystem commands.
- Treat `.uproject`, `.uplugin`, `.Build.cs`, and `Config/*.ini` edits as high-impact and call them out.
- Do not directly edit `.uasset` binary files.
- After adding or changing opencode skills, agents, plugins, or config, tell the user to restart opencode before relying on the new definitions.
