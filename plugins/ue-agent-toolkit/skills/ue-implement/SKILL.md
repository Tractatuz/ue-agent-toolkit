---
name: ue-implement
description: Implement Unreal Engine features through focused C++ or Config changes and Unreal MCP asset creation or editing. Use when the user asks to add, change, or fix Unreal behavior.
---

# UE Implement

Choose the correct Unreal implementation surface, make the smallest correct change, and verify code/asset integration. Prefer C++ or config when feasible; use Unreal MCP when authored assets must change.

## Required Reference

Before any Unreal MCP call, read `../../UNREAL_MCP.md` completely and follow its connection, discovery, editing, safety, and evidence contract.

## Routing

- Use this skill for implementation requests with sufficiently clear behavior and acceptance criteria.
- Use `ue-spec` first when the observable result or major constraints are ambiguous.
- Use `ue-plan` first when the user asks for a reviewable task plan before coding.
- Use `ue-analyze` for analysis-only questions.
- Use `ue-test` after implementation when validation is requested or appropriate.

## Prerequisites For Asset Work

- The project must be open in Unreal Editor with the local Unreal MCP server started.
- Required engine/project toolsets must appear in `list_toolsets`.
- Existing assets must pass `AssetTools.can_edit_asset` before mutation.
- If the server, toolset, source-control permission, or editor state is unavailable, stop the asset portion and report the blocker. Never edit `.uasset` bytes directly.

## Core Decision

- Prefer C++ or config for runtime logic, authority, replication, reusable behavior, persistence, component composition, input binding code, and validation.
- Prefer assets for authored defaults, Blueprint graphs, Widget Blueprint layout, animation state, input/data assets, tables, materials, maps, and content references.
- Use a hybrid when code supplies reflected extension points and assets supply authored structure/defaults.
- If either surface would produce a materially different user-visible result and the request does not decide, ask one focused question.

## Workflow

1. **Understand the request.** Identify observable behavior, target systems, networking/persistence constraints, asset impact, and verification criteria.
2. **Inspect existing patterns.** Read nearby C++, config, and relevant asset state. Do not assume stock Unreal architecture.
3. **Declare the surface.** State code-only, config-only, asset-only, or hybrid, and call out why binary assets are necessary.
4. **Implement code/config.** Follow `CLAUDE.md`, preserve reflected API compatibility, networking intent, ownership/lifetime, and existing style.
5. **Discover MCP schemas.** For asset work, call `list_toolsets` and `describe_toolset` for each required toolset before mutation.
6. **Edit assets sequentially.** Read current state, apply the smallest type-specific change, compile where supported, and read back the result.
7. **Save explicitly.** Save only named packages with `AssetTools.save_assets` after verification, then confirm each package is no longer dirty.
8. **Integrate and review.** Inspect diffs and ensure reflected symbols, paths, references, defaults, and asset state agree.
9. **Verify.** Build C++ changes when possible and route runtime/Automation validation to `ue-test`.

## Unreal MCP Editing

Use focused toolsets rather than a generic patch format:

- `AssetTools`: discovery, `can_edit_asset`, create/duplicate operations where exposed, explicit save, and dirty/source-control checks.
- `BlueprintTools`: create Blueprint assets, edit variables/functions/events/nodes, use `write_graph_dsl` for graph changes, compile, and read back graph DSL.
- `ObjectTools`: list/get exact properties before narrow `set_properties` calls on CDOs, components, and data assets.
- `ActorTools` and `SceneTools`: editor-world actor/component work only when maps or level-authored content are explicitly in scope.
- `UMGToolSet`: Widget Blueprint creation, tree edits, event binding, and compile.
- Specialized data, table, material, mesh, texture, animation, gameplay, or bundled toolsets for their own asset domains.
- `ProgrammaticToolset`: only for a genuinely atomic multi-tool edit that focused calls cannot express. Inspect its schema, preserve rollback, and commit only after all checks succeed.

Never guess a tool name or argument. Match toolsets by final class name and use the exact module-qualified name returned by discovery.

### Asset Transaction Checklist

For every changed package:

1. Record the exact package path and intended change.
2. Confirm edit permission for an existing asset.
3. Capture the relevant before-state.
4. Apply focused MCP calls sequentially.
5. Compile or validate the asset type.
6. Re-read the changed structure/properties/references.
7. Save the explicit package path.
8. Confirm clean dirty state and report the result.

If an operation partially fails, do not save. Use Unreal undo/transaction rollback when available and report any dirty in-memory packages that remain.

## Delegated Roles

When the user or active policy permits delegation:

- `ue-code-writer`: focused C++/config work with non-overlapping file ownership.
- `ue-asset-editor`: exactly one sequential Unreal MCP asset-editing flow.
- `ue-code-reviewer`: independent review of non-trivial C++/config changes.

Do not assign two writers to the same file or run concurrent mutating calls against one Unreal Editor session. The primary agent owns integration and final verification.

## Code Rules

- Follow `CLAUDE.md` and existing naming, pointer, module, and reflection style.
- Avoid gameplay logic in constructors beyond default subobjects/default values.
- Preserve RPC, authority, replication, GC, serialization, and lifecycle intent.
- Avoid Tick unless necessary; prefer events, delegates, timers, components, and subsystems.
- Treat `.uproject`, `.uplugin`, `.Build.cs`, and `Config/*.ini` as high-impact.
- Never edit generated output under `Binaries/`, `Intermediate/`, `Saved/`, or `DerivedDataCache/`.

## Response

Answer in the user's language. Lead with the implemented outcome and selected surface. List changed source/config files and exact asset package paths. For asset work, include resolved toolsets, important MCP calls, compile/read-back/save results, and any dirty or blocked packages. Report builds/tests run and residual untested risks without overstating proof.
