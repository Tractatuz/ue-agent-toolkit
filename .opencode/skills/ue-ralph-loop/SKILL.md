---
name: ue-ralph-loop
description: Use when running an end-to-end autonomous Unreal Engine development loop from feature goal or spec through planning, implementation, validation, self-evaluation, and review handoff.
---

## Purpose

Use this skill when the user wants an Unreal Engine feature, fix, or change handled end-to-end with minimal intervention.
The goal is to coordinate a full Ralph Loop style workflow: spec readiness, planning, focused analysis, implementation, validation, self-evaluation, iteration, and reviewable handoff.

The preferred model is a step-based loop attempt. Each attempt follows the same ordered steps: re-check spec, revise plan, analyze project context, implement, validate/test, evaluate/report, then decide whether to launch the next attempt in a fresh `opencode run` session.

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

## Ordered Loop Steps

Treat the loop as explicit steps, not as separate high-level modes. The session should always know which step it is in and what artifact or decision finishes that step.

### Step 1: Read Goal And Prior State

Read the user goal, referenced spec, referenced plan, previous result packet, current repository state, and any validation evidence from the prior attempt.

Do not trust hidden chat memory from a previous failed attempt. Treat previous attempts as evidence to inspect.

Output of this step:

- Current goal summary.
- Prior attempt status if any.
- Known spec, plan, result packet, and evidence paths.

### Step 2: Re-Check The Spec

Use `ue-spec` when requirements need creation, refinement, or review.

Before any implementation, verify that the current spec or reconstructed requirement still defines observable behavior, target systems or discovery paths, major constraints, and validation signals.

If the previous attempt failed because the requirement was wrong, ambiguous, or incomplete, revise the spec or ask focused questions before continuing.

Output of this step:

- Spec readiness: `Ready`, `Ready with assumptions`, or `Blocked by open questions`.
- Updated spec path or embedded spec summary.
- Assumptions and open questions.

### Step 3: Revise The Plan Document

Use `ue-plan` to create or update the implementation plan from the current spec and prior failure evidence.

The plan must be updated before another implementation attempt when validation failed, project evidence contradicted an assumption, task boundaries were wrong, or a new dependency was found.

Output of this step:

- Updated plan path or embedded plan summary.
- Ordered task list.
- Current next task.
- Validation mapped to acceptance criteria.

### Step 4: Re-Analyze Project Context

Use `ue-analyze` when correct implementation depends on current source, config, Blueprint defaults, assets, input mappings, widgets, animation, maps, plugins, or logs.

Do this after revising the plan so analysis is scoped to the current next task instead of becoming a broad scan.

Output of this step:

- Evidence read or generated.
- Confirmed implementation surface.
- Risks that change the plan.

### Step 5: Implement The Next Smallest Change

Use `ue-implement` for source, config, and asset changes.

Implement only the next smallest correct change set from the updated plan. Do not combine unrelated fixes just because they were discovered during analysis.

Output of this step:

- Files, config, and assets changed.
- Any subagent results integrated.
- Any implementation assumptions introduced.

### Step 6: Validate And Test

Use `ue-test` after implementation.

Run the smallest useful verification that can catch the likely regression: build, Unreal Automation, TestPlay, editor validation, or manual smoke checks.

Output of this step:

- Commands or checks run.
- Pass/fail/blocked result.
- Log, result JSON, Automation, TestPlay, or TaskEvidence paths.
- First actionable failure if any.

### Step 7: Evaluate And Report

Compare the result against the user goal, current spec, updated plan, acceptance criteria, and validation evidence.

Output of this step:

- Status: `Complete`, `Complete with residual risk`, `Partial`, `Validation failed`, or `Blocked`.
- What changed.
- What was validated.
- What remains risky, incomplete, or blocked.

### Step 8: Launch Next Fresh Attempt If Needed

This is the only step that starts another loop attempt.

If Step 7 is not complete and another attempt is justified, write a self-contained re-entry packet and start the next attempt in a fresh `opencode run` session. The new attempt must begin again at Step 1, then re-check spec and revise the plan before implementation.

Use the cross-platform helper script when automatic fresh-session iteration is desired:

```bash
python .opencode/skills/ue-ralph-loop/scripts/run_ue_ralph_loop.py --feature "<feature>" --goal "<goal>"
```

Common options:

- `--goal-file <path>`: read the goal from a file instead of an argument.
- `--input-packet <path>`: continue from an existing re-entry packet.
- `--spec <path>`: provide a spec document to re-check.
- `--plan <path>`: provide a plan document to re-check.
- `--max-iterations <n>`: maximum fresh attempt sessions, default `3`.
- `--model <provider/model>`: pass a model to fresh `opencode run` attempt sessions.
- `--agent <agent>`: pass an agent to fresh `opencode run` attempt sessions.
- `--timeout-seconds <n>`: timeout for each attempt session.
- `--artifacts-dir <path>`: output directory for packets, status JSON, and logs. Default is `Saved/Agent/RalphLoop`.
- `--dry-run`: write the initial packet and show the first child command without running it.

Do not pass `--dangerously-skip-permissions` unless the user explicitly accepts the risk.

Next-attempt constraints:

- Launch fresh attempts sequentially, never in parallel, because they share the same Unreal project and working tree.
- Treat output files as evidence, not hidden chat memory.
- Stop when an attempt reports `complete`, `complete_with_residual_risk`, or `blocked`.
- Stop when `--max-iterations` is reached.
- Report the final result packet and status JSON paths.

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

Prefer step-based cross-session iteration over repeatedly retrying inside the same primary session.

In any single attempt session, run one bounded pass through the ordered steps:

1. Re-read or reconstruct the current spec.
2. Update or create the implementation plan.
3. Re-analyze project context needed for the updated plan.
4. Implement the next smallest correct change set.
5. Validate and test.
6. Self-evaluate against the spec and plan.
7. Report the result and launch the next fresh attempt only if needed.

Do not rely on memory from a previous failed attempt as authoritative. Treat prior attempts as evidence to inspect, not truth to repeat.

When beginning from a re-entry packet in a new session, start at Step 1. Re-check the spec and revise the plan before implementation. The new session must verify that the carried-over spec, plan, failure evidence, and repository state still match the current project.

## Persistent Artifacts

For automated fresh-attempt runs, keep generated packets, status JSON, and attempt-session logs under `Saved/Agent/RalphLoop` by default. This avoids creating source-controlled documentation unless the user asks for it.

For specs, plans, or re-entry packets that should be reviewed, committed, or reused outside a single automation run, use durable Markdown or JSON evidence outside generated engine outputs when the user approves it.

Recommended locations:

- Specs: `Docs/Agent/Specs/<feature>.md` when the spec should be reviewed or reused.
- Plans: `Docs/Agent/Plans/<feature>.md` when the plan should be reviewed or reused.
- Re-entry packets: `Docs/Agent/RalphLoop/<feature>-iteration-<n>.md` for cross-session continuation.
- Automated attempt packets, temporary logs, command outputs, generated TestPlay specs, and result JSON: `Saved/`.

If the repository does not already use `Docs/Agent/`, ask before creating durable source-controlled documentation. If the user wants no new tracked docs, include the re-entry packet in the final response instead and keep generated evidence under `Saved/`.

## Gate Details

These gates are the checks used inside the ordered steps. They are not separate modes.

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

If self-evaluation fails, identify the smallest necessary next starting gate for the current attempt's report or the next fresh attempt:

- Requirement ambiguity: Spec Gate.
- Bad task split or missing dependency: Plan Gate.
- Missing project evidence: Analysis Gate.
- Implementation defect: Implementation Gate.
- Insufficient proof: Validation Gate.

Prefer cross-session bounded iteration. By default, do not run another full implementation-validation loop inside the same attempt session after a meaningful failure. Instead, write a re-entry packet and status JSON, then use Step 8 to start the next fresh attempt session when appropriate.

An in-session retry is allowed only when the failure is small, mechanical, and immediately actionable, such as a simple compile error, missing include, formatting issue, typo, or incorrect command argument.

Do not run more than one in-session retry unless the failure is mechanical and the fix is clearly bounded.

Stop and report when another loop would require guessing, broad refactoring, destructive commands, unrelated cleanup, or risky asset/config changes not covered by the user's request.

## Failure Re-Entry Protocol

When an attempt result is `Partial`, `Blocked`, or validation fails in a way that requires another real attempt, create a re-entry packet for the next fresh session.

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
- The status JSON requested by the fresh-attempt launcher.

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
Start with `ue-ralph-loop` at Step 1.
Re-read the goal and prior state, re-check the spec, revise the plan for the failure above, re-analyze the needed project context, implement the next smallest fix, validate, evaluate, report, and only then decide whether another fresh attempt is needed.

## Suggested Prompt
Continue the Ralph Loop for <feature> from this re-entry packet. Follow the ordered steps: read goal and prior state, re-check the spec, revise the plan, re-analyze project context, implement the next smallest fix, validate/test, evaluate/report, and only then launch or request the next fresh attempt if needed.
```

The status JSON must use this shape when the fresh-attempt launcher requested one:

```json
{
  "status": "complete | complete_with_residual_risk | partial | validation_failed | blocked",
  "continue": true,
  "summary": "short result summary",
  "next_starting_gate": "Spec | Plan | Analysis | Implementation | Validation | Done",
  "first_actionable_failure": "failure, blocker, or empty string",
  "result_packet": "path to the result packet"
}
```

Set `continue` to `false` for `complete`, `complete_with_residual_risk`, and `blocked`. Set `continue` to `true` for `partial` or `validation_failed` only when another fresh attempt session should continue.

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
