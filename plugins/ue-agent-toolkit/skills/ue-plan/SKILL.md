---
name: ue-plan
description: Turn an Unreal Engine feature spec or concrete implementation goal into an executable plan with code, asset, Unreal MCP, validation, dependency, and agent task boundaries. Use before coding when the user asks for a plan or task breakdown.
---

# UE Plan

Create a reviewable implementation plan; do not implement the feature.

## Required Reference

When the plan includes asset inspection/editing, Automation, PIE, logs, captures, or editor evidence, read `../../UNREAL_MCP.md` completely and plan against that contract.

## Readiness Gate

Classify the input as `Ready`, `Ready with assumptions`, or `Blocked by open questions`.

A plan is ready when observable behavior, likely target systems, acceptance criteria, and relevant networking/persistence/asset constraints are known or can be found with focused inspection. Do not invent detailed tasks when different unresolved choices would materially change behavior or architecture.

Route requirements gaps to `ue-spec`; route current-behavior investigation to `ue-analyze`.

## Workflow

1. Identify the source spec, prompt, issue, or prior result packet.
2. Preserve stated requirements and label every inference as an assumption.
3. Inspect only enough project context to name realistic classes, modules, config, assets, maps, and tests.
4. Classify the implementation surface: code, config, asset, UI, animation, input, data, map, networking, persistence, plugin/editor tooling, or hybrid.
5. Split work into executable units with an objective, scope, dependencies, constraints, acceptance criteria, and verification.
6. Sequence code/config work and editor work. Independent filesystem tasks may be parallel; Unreal MCP mutations, compile/save calls, PIE, Automation, and shared editor state must be sequential.
7. Map each acceptance criterion to build, Automation, Unreal MCP PIE, asset read-back/compile/save, log/capture, or a clearly labeled manual check.
8. Identify prerequisites: editor/server state, required toolset suffixes, engine version, source-control permission, map/test data, and expected evidence packet paths.
9. Produce the plan or a concise blocking-gap report.

## Unreal MCP Planning Rules

- Plan discovery as `list_toolsets → describe_toolset → call_tool`; never bake in unverified argument schemas.
- For analysis tasks, name likely toolset suffixes such as `AssetTools`, `ObjectTools`, `BlueprintTools`, `UMGToolSet`, or a specialized project toolset.
- For asset writes, require `can_edit_asset`, before-state inspection, focused type-specific calls, compile/validation, read-back, explicit package save, and clean dirty-state verification.
- For runtime checks, require explicit map/load intent, bounded `StartPIE`/`StopPIE`, observable assertions, scoped logs/captures, and cleanup verification.
- For Automation, require discovery, exact test selection, terminal status/results, and timeout cleanup.
- For editor validation, plan an `ue.mcp.evidence.v1` file under `Saved/Agent/Evidence/` written through Unreal MCP.
- If direct action-level Enhanced Input injection is required, plan `PlaytestToolset` calls and explicit injection cleanup; do not assume a focused Slate key press is equivalent.

## Task Sizing And Roles

- Prefer one task per class/component/subsystem, coherent asset group, or validation path.
- Do not split trivial work artificially or combine unrelated code and binary-asset changes.
- Do not assign parallel writers to the same file.
- Suggested roles: primary agent, `ue-code-reader`, `ue-code-writer`, `ue-code-reviewer`, `ue-asset-scanner`, `ue-asset-editor`, or `ue-tester`.
- Assign exactly one sequential asset editor against a shared Unreal session.
- The primary agent owns integration checkpoints and acceptance-criteria evaluation.

## Plan Structure

Use the user's language and this structure when useful:

```text
# <Feature> Implementation Plan

## Summary
- Source: <spec/prompt/path>
- Goal: <observable result>
- Readiness: Ready | Ready with assumptions | Blocked by open questions

## Assumptions And Open Questions
- <labeled item>

## Implementation Surface
- Code/Config: <files, classes, modules>
- Assets: <package paths/types or discovery targets>
- Unreal MCP: <required toolset suffixes and editor prerequisites>
- Validation: <build, Automation, PIE, evidence packet>

## Work Breakdown

### Task 1: <name>
- Objective: <result>
- Scope: <files/assets/config/searches>
- Dependencies: <tasks/prerequisites>
- Constraints: <Unreal/editor/safety constraints>
- Acceptance Criteria: <observable checks>
- Verification: <exact path>
- Suggested Role: <role>

## Sequencing And Integration
- Phase 1: <ordered tasks>
- Parallelizable: <independent tasks>
- Sequential editor work: <MCP calls/assets/tests>
- Integration checkpoints: <checks>

## Risks And Handoff
- <risk, blocker, residual uncertainty>
- Next: use ue-implement with this plan.
```

For blocked input, return the understood goal, planning-blocking gaps, focused questions, and the next `ue-spec` step rather than a fictional plan.

## Safety

- Do not edit source, config, assets, maps, or generated files while planning unless separately requested.
- Do not call mutating Unreal MCP tools.
- Treat `.uproject`, `.uplugin`, `.Build.cs`, `Config/*.ini`, binary assets, networking, persistence, and plugin dependencies as high-impact.
- Keep confirmed project evidence, assumptions, and open questions separate.
