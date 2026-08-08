---
name: ue-plan
description: Use when turning an Unreal Engine spec document or implementation goal prompt into a concrete implementation plan with executable tasks before coding.
---

## Purpose

Use this skill after a feature spec is ready, or when the user provides an implementation goal prompt that is already concrete enough to plan from.
The goal is to convert the spec or prompt into a reviewable implementation plan document with ordered work units, likely file and asset scopes, dependencies, validation steps, and handoff notes for `ue-implement`.

This skill produces an implementation plan. It does not implement the feature and should not edit Unreal source, config, assets, maps, or generated files unless the user separately asks for implementation.

## Trigger Conditions

Use this skill when the user asks to plan, break down, split into tasks, create an implementation plan, make executable work items, prepare implementation steps, or turn a spec into implementable units for an Unreal Engine feature.

Typical triggers include:

- Existing spec documents that are ready for planning.
- Rough implementation prompts that already define observable behavior and constraints.
- Requests like "write a plan", "break this down", "make tasks", "implementation plan", "agent task plan", or "prepare for implementation".

Do not use this skill to create or review the spec itself. Use `ue-spec` when requirements are not planning-ready.
Do not use this skill for analysis-only questions. Use `ue-analyze` when the user asks how existing gameplay works.
Do not use this skill once the user asks to directly build the feature. Use `ue-implement` for implementation.

## Core Outcome

Create a plan document that makes these decisions explicit enough for another agent or developer to implement safely:

- The implementation goal and source spec or prompt being planned.
- The likely Unreal implementation surface: C++, Config, Blueprint, assets, UI, animation, input, data, networking, persistence, plugins, or editor tooling.
- Concrete code, config, and asset areas to inspect or change.
- Ordered implementation phases and task boundaries.
- Dependencies between tasks and which tasks can run in parallel.
- Asset editing needs and whether JsonToAsset or manual editor work is expected.
- Build, automation, TestPlay, or manual validation steps mapped to acceptance criteria.
- Risks, assumptions, open questions, and blockers that affect implementation.

## Planning Readiness Gate

Before writing a plan, check whether the input is ready enough to plan.

Ready inputs include:

- Observable runtime or editor behavior is defined.
- Target systems, classes, assets, or discovery paths are known or can be identified with focused inspection.
- Acceptance criteria or expected validation outcomes are stated or can be safely derived.
- Major networking, persistence, UI, animation, data, and asset ownership decisions are either specified or irrelevant.

If the input is not ready, do not invent a detailed plan. Provide the smallest useful gap report and route back to `ue-spec` or ask focused clarifying questions.

Planning-blocking gaps include:

- The target feature behavior is ambiguous enough that different implementations would be valid.
- Multiple implementation surfaces are plausible and would produce different user-visible behavior.
- Required target classes, maps, widgets, assets, or systems are unknown and cannot be found with focused project inspection.
- Networking authority, replication, or persistence requirements are relevant but unspecified.
- Verification is impossible because no observable expected result is defined.

## Workflow

1. Identify the planning input.

Determine whether the source is a spec document, pasted prompt, issue, bug-to-feature request, or prior conversation context. Preserve the user's stated requirements and mark inferred items as assumptions.

2. Run the readiness gate.

Classify the input as `Ready`, `Ready with assumptions`, or `Blocked by open questions`. If blocked, stop at a gap report unless the user explicitly asks for a provisional plan.

3. Inspect project context only as needed.

Search and read enough existing C++, config, module, plugin, and asset-reference evidence to identify realistic implementation surfaces and task boundaries. Avoid broad project scans. Use `ue-analyze` when behavior must be understood before a correct plan can be written.

4. Classify the implementation surface.

Decide whether work is likely code-only, asset-only, config-only, hybrid code plus assets, plugin/editor tooling, or validation-only. Prefer C++ or config when feasible, but call out when assets are necessary.

5. Break work into executable units.

Create tasks that are small enough to implement and review independently. Each task should have a clear objective, expected files or assets, inputs, dependencies, acceptance criteria, and verification path.

6. Define sequencing and parallelism.

Order tasks by dependency. Identify independent code tasks that can be delegated in parallel with the `ue-code-writer` custom agent. Keep asset editing tasks sequential with the `ue-asset-editor` custom agent, especially JsonToAsset, Unreal Remote Execution, package saves, and editor-driven operations.

7. Map validation to acceptance criteria.

Choose the smallest useful verification for each risk: build, Unreal Automation, TestPlay, editor validation, asset compile/save confirmation, log inspection, or manual smoke test.

8. Write the plan document.

Use a durable Markdown document when the user asks for a plan document or provides a target path. If no path is specified, return the plan in the response and suggest a path only if the plan is likely to be reused.

## Task Sizing Rules

- Prefer one task per class, component, subsystem, plugin area, widget, data asset group, or validation path.
- Do not split tiny changes into artificial tasks when one focused task is clearer.
- Do not combine unrelated code and asset changes if they require different tools or sequencing.
- Do not ask two parallel agents to edit the same file unless the sequence is explicitly controlled.
- Treat `.uproject`, `.uplugin`, `.Build.cs`, and `Config/*.ini` edits as high-impact and call them out.
- Keep generated outputs under `Saved/` if the plan needs temporary evidence or generated specs.

## Plan Content Checklist

Include sections that are relevant to the feature. Omit sections that clearly do not apply.

### Summary

- Feature name and source input.
- One-paragraph implementation goal.
- Planning readiness classification.

### Assumptions And Open Questions

- Low-risk assumptions that allow implementation planning.
- Open questions that must be answered before exact implementation.
- Blockers that prevent planning, if any.

### Implementation Surface

- Code, config, asset, UI, animation, input, data, networking, persistence, plugin, or editor-tooling areas.
- Likely classes, modules, assets, maps, widgets, config files, or discovery searches.
- Asset edit requirements and whether binary assets are expected to change.

### Work Breakdown

For each task:

- Objective.
- Scope: files, classes, assets, config, or search targets.
- Dependencies.
- Implementation notes and constraints.
- Acceptance criteria.
- Verification.
- Suggested execution role: primary agent, `ue-code-writer`, `ue-asset-editor`, `ue-code-reviewer`, or `ue-tester`.

### Sequencing

- Ordered phases.
- Tasks that can run in parallel.
- Tasks that must run sequentially.
- Integration checkpoints.

### Validation Plan

- Build commands when known.
- Unreal Automation filters when relevant.
- TestPlay spec outline when runtime behavior needs PIE validation.
- Manual/editor validation steps when automated validation is not available.
- Residual risks not covered by planned validation.

### Handoff

- Exact next step for `ue-implement`.
- Any `ue-analyze` evidence still needed before implementation.
- Any assets, editor state, plugins, or external prerequisites required.

## Output Structure

Use the user's language unless they ask for another language.

For a normal implementation plan, use this structure when it fits the request:

```text
# <Feature Name> Implementation Plan

## Summary
- Source: <spec path, prompt, issue, or conversation context>
- Goal: <implementation goal>
- Readiness: Ready | Ready with assumptions | Blocked by open questions

## Assumptions
- <Assumption>

## Open Questions
1. <Question affecting implementation>

## Implementation Surface
- Code: <classes/files/modules or discovery targets>
- Config: <ini/build/project/plugin files if relevant>
- Assets: <package paths/types or discovery targets>
- Validation: <build/test/editor paths>

## Work Breakdown

### Task 1: <Task Name>
- Objective: <what changes>
- Scope: <files/assets/config/searches>
- Dependencies: <none or task names>
- Notes: <implementation constraints>
- Acceptance Criteria: <observable result>
- Verification: <build/test/manual check>
- Suggested Role: <ue-code-writer | ue-asset-editor | ue-code-reviewer | ue-tester | primary>

## Sequencing And Parallelism
- Phase 1: <ordered work>
- Parallelizable: <tasks>
- Sequential: <tasks>

## Validation Plan
- <Validation step>

## Risks
- <Implementation or verification risk>

## Handoff To Implementation
- <Concrete instruction for ue-implement>
```

For blocked input, use this shorter structure:

```text
# <Feature Name> Planning Readiness Review

## Readiness
Blocked by open questions

## Summary
<What can be understood from the input>

## Blocking Gaps
- <Missing decision that changes the implementation plan>

## Suggested Clarifications
1. <Question>

## Next Step
Use `ue-spec` to refine the requirements, then run `ue-plan` again.
```

## Handoff

When the plan is ready and the user asks to implement, use `ue-implement` and pass the plan document or plan sections as the implementation source of truth.
When current project behavior must be understood before a correct plan can be written, use the relevant parts of `ue-analyze`, then return to this planning workflow.
When validation is requested after implementation, use `ue-test`.

## Response Style

- Answer in Korean unless the user asks otherwise.
- Lead with whether the implementation plan is ready, ready with assumptions, or blocked.
- Keep task descriptions concrete and executable, not generic process advice.
- Explicitly call out binary asset, broad config, plugin, module, networking, or persistence impact.
- Do not overstate certainty when project context was not inspected.

## Safety

- Do not implement while planning.
- Do not modify Unreal assets, source files, config files, maps, or generated files while creating the plan unless the user explicitly asks for those edits.
- Do not edit `.uasset` binary files directly.
- Do not run destructive editor commands.
- Avoid broad project scans unless needed to identify safe task boundaries.
- Keep assumptions and open questions separate from confirmed requirements.
