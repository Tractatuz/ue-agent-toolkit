---
name: ue-spec
description: Use when creating or reviewing an Unreal Engine feature spec from prompts, rough requirements, or existing spec documents before implementation planning.
---

## Purpose

Use this skill before implementation planning when the user provides an Unreal Engine feature idea, rough implementation prompt, partial requirements, bug-to-feature request, gameplay/system concept, informal design note, or existing spec document.
The goal is to transform input into a concrete spec document and/or review an existing spec so it becomes detailed enough to create an actionable implementation plan without inventing unconfirmed core requirements.

This skill produces or reviews a spec document. It does not implement the feature and should not edit project source, config, or assets unless the user separately asks for implementation.

## Trigger Conditions

Use this skill when the user asks to create, refine, expand, formalize, review, critique, validate, or make a spec from an Unreal Engine feature request, implementation prompt, or existing spec document.
Typical create triggers include "write a spec", "turn this into a spec", "make this concrete", "prepare this for implementation planning", "feature spec", pasted gameplay/UI/input/animation/data requirements, and rough prompts describing what should be built.
Typical review triggers include "review this spec", "is this enough to plan", "find gaps", "what is missing", "validate this spec", and pasted or referenced spec documents.

Do not use this skill for analysis of existing runtime behavior only. Use `ue-analyze` for that.
Do not use this skill once the user has already approved a concrete spec and asks to build it. Use `ue-implement` for that.

## Core Outcome

Create or review a structured Unreal Engine feature spec that makes these implementation-planning decisions clear enough:

- The user-visible outcome and runtime behavior.
- The likely Unreal implementation surface: C++, Config, Blueprint, assets, UI, animation, input, data, networking, persistence, or plugins.
- Required systems, classes, assets, maps, widgets, data, and references when known.
- Explicit assumptions where the prompt is incomplete.
- Open questions where guessing would materially change the implementation plan.
- Acceptance criteria and verification paths.

The generated or reviewed spec may include assumptions, but assumptions must be labeled and must not silently become requirements.

## Modes

### Create Mode

Use Create Mode when the user provides a rough prompt, feature idea, partial requirements, or informal implementation request and asks for a spec or planning-ready requirements.

Create Mode output is a complete spec document. After drafting it, run Review Mode against the generated spec before finalizing the response. Apply obvious fixes directly, then leave remaining material gaps as open questions.

### Review Mode

Use Review Mode when the user provides an existing spec document or explicitly asks for a review, validation, gap analysis, planning-readiness check, or critique.

Review Mode output is a spec review, not a replacement spec unless the user asks for a rewrite. It should identify whether the document is ready for implementation planning, what is already clear, what is missing, which assumptions are unsafe, and what revisions would make it planning-ready.

If the user asks to both review and improve a spec, first provide the review findings, then provide a revised spec or patch-style revision notes according to the user's request.

## Create Mode Workflow

1. Extract the implementation intent.

Identify the feature, target user/player/designer, desired outcome, and any named Unreal classes, assets, maps, systems, or plugins from the prompt.

2. Classify the likely implementation surface.

Decide whether the feature likely touches C++, Config, Blueprint, assets, UI widgets, animation, Enhanced Input, data assets/tables, maps, networking, save data, plugins, or editor tooling.
This classification guides which spec sections need detail; it is not a final implementation plan.

3. Ground the spec in the project only when necessary.

If the prompt references existing systems, classes, assets, maps, modes, characters, controllers, widgets, abilities, inventory, quests, combat, animation, input, or save data, inspect only enough project source/config/asset references to use correct names and avoid impossible or misleading spec details.
Do not perform broad implementation analysis unless the user asks for it.

4. Expand underspecified requirements.

Convert vague intent into concrete behavior, state transitions, data needs, integration points, and acceptance criteria.
When a missing detail has a low-risk default, include it as an explicit assumption.
When a missing detail would materially change architecture, networking, assets, UX, or verification, leave it as an open question instead of choosing for the user.

5. Produce the spec document.

Write a spec that is detailed enough for another agent or developer to create an implementation plan from it.
Keep it practical and implementation-facing; avoid product-marketing language.

6. Self-review the generated spec.

Run Review Mode against the spec you just created. Fix gaps that can be resolved from the original prompt or low-risk assumptions. Keep unresolved planning-impacting gaps in `Open Questions`.

7. Report readiness.

At the end, state whether the spec is ready for detailed implementation planning, ready with assumptions, or blocked by open questions.

## Review Mode Workflow

1. Identify the spec's intended feature.

Summarize what the existing spec appears to ask for. If the document is too ambiguous to identify the feature, mark it blocked and ask for the missing context.

2. Classify the likely implementation surface.

Identify likely C++, Config, Blueprint, asset, UI, animation, input, data, networking, persistence, plugin, or editor tooling impact. Use this classification to judge whether the spec contains the necessary details.

3. Check planning readiness.

Evaluate the spec against the Spec Content Checklist, Assumption Rules, and blocking gap rules. Missing items are blockers only when they would change implementation planning or user-visible behavior.

4. Separate findings by impact.

Report blockers first, then non-blocking assumptions, then polish or optional improvements. Do not bury architecture, networking, asset ownership, or verification gaps under style feedback.

5. Recommend revisions.

Provide the smallest set of concrete revisions or clarifying questions needed to make the spec ready for implementation planning. If the user asked for a rewrite, include the revised spec after the review findings.

6. State readiness.

Classify the reviewed spec as `Ready`, `Ready with assumptions`, or `Blocked by open questions`.

## Spec Content Checklist

Include sections that are relevant to the prompt. Omit sections that clearly do not apply.

### Feature Summary

- Short name for the feature.
- One-paragraph description of the intended result.
- Primary user/player/designer value.

### Goals And Non-Goals

- What must be implemented.
- What is explicitly out of scope.
- Any placeholder behavior that is acceptable for now.

### User-Facing Behavior

- Trigger conditions, inputs, interactions, and state transitions.
- Success, failure, cancel, cooldown, reset, and edge-case behavior.
- Feedback requirements: UI, animation, sound, VFX, camera, logs, debug display, or editor feedback.
- Important values: ranges, durations, speeds, costs, limits, priorities, probabilities, distances, tags, names, or tunable defaults.

### Unreal Integration

- Likely classes, components, subsystems, GameMode, controllers, pawns/characters, widgets, animation blueprints, data assets, maps, or plugins involved.
- Expected implementation surface: C++, Blueprint, config, data assets/tables, widgets, animation assets, or a hybrid.
- Reflected symbols, Blueprint extension points, exposed defaults, asset references, package paths, and naming conventions when known.
- Lifecycle expectations such as constructor defaults, BeginPlay, input binding, replication setup, save/load, async loading, collision, timers, delegates, or editor-only behavior.

### Assets And Authored Data

- Required asset types and package paths when known.
- Blueprint defaults, widget layout expectations, animation states/montages/notifies, input mapping contexts/actions, data rows, materials, meshes, sounds, VFX, and icons when relevant.
- Whether binary assets must be created or modified.
- Acceptable placeholders for art, sound, VFX, animation, or UI polish.

### Networking And Persistence

- Whether the feature is single-player only, listen-server, dedicated-server, client-predicted, replicated, cosmetic-only, or editor-only.
- Authority, ownership, RPC, replication conditions, relevancy, rollback/prediction, and late-join expectations when relevant.
- Whether state persists across respawn, level transition, save/load, reconnect, or editor sessions.

### Constraints And Compatibility

- Platform, performance, memory, scalability, accessibility, localization, and input-device constraints when relevant.
- Dependencies, plugin requirements, engine-version assumptions, and project coding/asset rules.
- Migration, backward compatibility, serialized asset compatibility, and reflected API stability requirements if existing content may depend on the change.

### Acceptance Criteria

- Observable conditions that prove the feature works.
- Important negative cases and regression risks.
- Manual validation steps.
- Automated build/test/editor validation paths when known.

### Assumptions

- Low-risk choices made to complete the spec.
- Defaults that should be confirmed but do not block initial planning.

### Open Questions

- Questions that must be answered before implementation planning can be fully precise.
- Prioritize architecture and ownership questions first, networking/persistence second, asset/data/UI/animation specifics third, and tuning/polish last.

## Assumption Rules

Use an assumption when the choice is reversible, low-risk, and unlikely to change the implementation architecture.
Examples:

- Placeholder UI text, icon, sound, or VFX is acceptable.
- Tuning values can be exposed as editable defaults.
- A feature can start single-player only because the prompt does not mention multiplayer and the project context does not imply networked play.
- A new component or data asset name can be provisional.

Do not assume when the choice would materially change the implementation plan.
Leave an open question instead for these cases:

- Target actor/class/component/widget/asset is unknown and multiple candidates are plausible.
- Network authority or replication behavior is relevant but unspecified.
- The feature could be implemented in code or assets with materially different outcomes and no preference or constraint is given.
- Core gameplay rules, state transitions, or acceptance criteria are missing.
- Required data values or asset references are missing and cannot be represented as configurable placeholders.
- Existing serialized/reflected API behavior may change and compatibility requirements are unknown.
- Verification is impossible because no observable expected result is stated.

## Output Structure

Use the user's language unless they ask for another language.

For Create Mode, use this structure when it fits the request:

```text
# <Feature Name> Spec

## Summary
<Concrete feature summary>

## Goals
- <Goal>

## Non-Goals
- <Out-of-scope item>

## User-Facing Behavior
- <Runtime behavior>

## Unreal Integration
- <Likely implementation surface and project integration points>

## Assets And Data
- <Required assets/data or placeholders>

## Networking And Persistence
- <Relevant authority/replication/save behavior, or explicit non-applicability>

## Constraints
- <Constraints and compatibility notes>

## Acceptance Criteria
- <Observable pass criteria>

## Assumptions
- <Labeled assumption>

## Open Questions
1. <Question that affects planning>

## Planning Readiness
Ready | Ready with assumptions | Blocked by open questions
```

If the user asks for a shorter spec, keep the same intent but compress sections.
If the user provides a template, follow that template while preserving the required content.

For Review Mode, use this structure when it fits the request:

```text
# <Feature Name> Spec Review

## Planning Readiness
Ready | Ready with assumptions | Blocked by open questions

## Summary
<What the spec is asking for and whether it is implementation-plannable>

## Clear Enough
- <Requirement or decision that is already concrete>

## Blocking Gaps
- <Missing or ambiguous item that changes the implementation plan>

## Risky Assumptions
- <Assumption the spec appears to make but does not state safely>

## Suggested Revisions
- <Concrete change to the spec>

## Clarifying Questions
1. <Question that must be answered before planning>
```

Omit empty sections. If there are no blocking gaps, explicitly state that the spec is ready for implementation planning.

## Handoff

When the resulting or reviewed spec is ready and the user asks for a detailed implementation plan, create the plan from the spec and clearly carry forward assumptions and open questions.
When the user asks to implement after the spec is ready, use `ue-implement`.
When current project behavior must be understood before a correct spec can be written, use the relevant parts of `ue-analyze` for focused evidence gathering, then return to spec writing.

## Safety

- Do not invent product requirements to make the spec look complete.
- Clearly label assumptions and keep open questions separate.
- When reviewing, do not rewrite the user's intent silently; call out proposed changes as revisions.
- Do not modify Unreal assets, source files, config, or generated files while writing the spec.
- Avoid broad project scans unless they are necessary to write correct integration details.
- If asset inspection is unavailable, state that asset-dependent spec details could not be fully grounded in project evidence.
