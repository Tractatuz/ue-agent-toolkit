---
name: ue-spec
description: Create or review an implementation-ready Unreal Engine feature specification, including observable behavior, Unreal integration, asset ownership, Unreal MCP validation signals, assumptions, and open questions. Use before detailed planning when requirements need definition or review.
---

# UE Spec

Create or review a practical Unreal feature specification. Do not plan tasks or implement the feature.

## Required Reference

When the feature depends on authored assets, editor state, Automation, PIE, logs, or visual evidence, read `../../UNREAL_MCP.md` completely so requirements and acceptance criteria use capabilities that the Unreal MCP workflow can actually observe.

## Modes

- **Create:** turn a prompt or rough requirement into an implementation-ready spec.
- **Review:** evaluate an existing spec and identify only gaps that affect planning, architecture, user-visible behavior, or verification.

Classify the result as `Ready`, `Ready with assumptions`, or `Blocked by open questions`.

## Workflow

1. Identify the feature, target player/user/designer, desired outcome, and explicit non-goals.
2. Classify likely Unreal surfaces: C++, config, Blueprint, UI, animation, Enhanced Input, data, maps, networking, persistence, plugins, or editor tooling.
3. Inspect focused project context only when existing class/asset/map names are required for a credible spec. Use read-only `ue-analyze` behavior when necessary.
4. Convert vague intent into observable triggers, state transitions, success/failure/cancel/reset behavior, feedback, data, and edge cases.
5. Mark reversible low-risk choices as assumptions. Keep choices that alter architecture, networking, persistence, asset ownership, UX, or verification as open questions.
6. Define acceptance criteria that a later build, Automation test, Unreal MCP asset read-back, PIE observation, log query, or capture can actually prove.
7. Self-review the completed spec and report planning readiness.

## Unreal MCP-Aware Requirements

When relevant, specify:

- exact or discoverable `/Game/...` package paths and asset types;
- what asset state must be observable through `AssetTools`, `ObjectTools`, `BlueprintTools`, `UMGToolSet`, or a specialized toolset;
- which asset changes require compile, read-back, explicit save, and clean dirty state;
- the map and warmup needed for a repeatable in-process PIE check;
- actor tags/classes/properties, UI labels/roles, log categories, and visual results that form stable assertions;
- an exact Automation test/filter when deterministic input or complex behavior is needed;
- an `ue.mcp.evidence.v1` packet under `Saved/Agent/Evidence/` for editor-driven validation.

Use the bundled `PlaytestToolset` when acceptance criteria require action-level Enhanced Input injection, and specify value, player index, duration/sequence, and cleanup. Do not make a successful editor/PIE start an acceptance criterion by itself.

## Content Checklist

Include only relevant sections:

- **Summary:** feature and intended value.
- **Goals / Non-Goals:** required and excluded behavior.
- **User-Facing Behavior:** inputs, transitions, feedback, timing, limits, success/failure, and edge cases.
- **Unreal Integration:** likely classes/components/subsystems, lifecycle, Blueprint extension points, config, maps, and plugins.
- **Assets And Data:** asset types/paths, authored defaults, widgets, animation, input/data assets, and placeholder policy.
- **Networking And Persistence:** authority, ownership, replication/prediction, late join, save/load, respawn, and level transitions.
- **Constraints:** platform, performance, compatibility, migration, reflection/serialization, accessibility, localization, and engine/plugin prerequisites.
- **Acceptance Criteria:** positive, negative, regression, build, Automation, MCP PIE, and evidence requirements.
- **Assumptions / Open Questions:** clearly separated by risk.

## Blocking Gaps

Treat these as blocking when relevant:

- multiple target classes/assets/maps are plausible;
- networking authority or persistence behavior is unspecified;
- code and asset implementations would produce materially different outcomes;
- core rules/state transitions/acceptance signals are absent;
- reflected or serialized compatibility may change without a migration decision;
- no stable observable condition can prove the behavior.

## Output

Use the user's language. A normal spec may use:

```text
# <Feature> Spec
## Summary
## Goals
## Non-Goals
## User-Facing Behavior
## Unreal Integration
## Assets And Data
## Networking And Persistence
## Constraints
## Acceptance Criteria
## Assumptions
## Open Questions
## Planning Readiness
```

For review mode, lead with readiness, then list blockers, risky assumptions, suggested revisions, and focused questions. If ready, say so explicitly.

## Safety

- Do not invent product requirements merely to complete the template.
- Do not modify source, config, assets, maps, or generated files.
- Do not call mutating Unreal MCP tools.
- Distinguish requirements from current project evidence and proposed implementation details.
