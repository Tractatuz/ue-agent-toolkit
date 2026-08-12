---
name: ue-analyze
description: Analyze Unreal Engine gameplay behavior across C++, Config, Blueprint, and asset data, using Unreal MCP for editor and asset evidence. Use for analysis-only questions about how an Unreal project currently works.
---

# UE Analyze

Explain current Unreal behavior from cross-validated source, config, Blueprint, asset, and editor evidence. Do not edit project state.

## Required Reference

Before any Unreal MCP call, read `../../UNREAL_MCP.md` completely and follow its connection, discovery, inspection, safety, and reporting contract.

## Prerequisites

- The target `.uproject` and intended analysis scope must be known.
- C++ and config analysis can proceed without the editor.
- Asset or live editor conclusions require the project to be open in Unreal Editor, the local Unreal MCP server to be started, and the relevant toolsets to be present.
- If MCP is unavailable, report the exact missing evidence. Never infer that an asset contains no behavior merely because it could not be inspected.

## Workflow

1. **Resolve scope.** Identify the user question, target feature, expected depth, and likely code/config/asset surfaces. Ask only when different scopes would produce materially different answers.
2. **Read source and config.** Inspect relevant headers, implementations, module files, target files, and `Config/*.ini`. Trace ownership, inheritance, lifecycle, delegates, timers, input, networking, replication, and Blueprint-facing hooks.
3. **Identify asset-owned decisions.** Treat Blueprint-editable properties, asset references, generated classes, widgets, animation classes, input assets, maps, data assets, and component defaults as required asset evidence when they affect the answer.
4. **Discover Unreal MCP tools.** Call `list_toolsets`, match required suffixes, and call `describe_toolset` before the first use of each toolset. Use the exact returned schemas with `call_tool`.
5. **Inspect only relevant assets.** Read the smallest set of packages that can confirm or reject the runtime hypothesis.
6. **Cross-validate.** Connect native control flow, config values, Blueprint graphs, CDO/default values, components, asset references, and observed editor state into one runtime explanation.
7. **Report confidence.** Separate confirmed source facts, MCP-observed asset/editor facts, inferences, inaccessible evidence, and untested runtime behavior.

## MCP Asset Inspection

Use tool-native structured results:

- `AssetTools`: `find_assets`, `get_asset_tags`, `get_asset_class`, `get_dependencies`, `get_referencers`, and `load_asset` when an object reference is required.
- `ObjectTools`: `search_subclasses`, `list_properties`, and narrow `get_properties` reads.
- `BlueprintTools`: parent class, graph/function/event lists, variables, nodes, connected subgraphs, and `read_graph_dsl`.
- `ActorTools` and `SceneTools`: current map and actor/component state when live or PIE state is explicitly in scope.
- `UMGToolSet`: Widget Blueprint hierarchy and structure.
- `AnimBlueprintToolset` or other specialized toolsets: asset-type-specific state unavailable from generic tools.
- `LogsToolset`: scoped editor/runtime log evidence.

Toolset names are module-qualified and may vary. Match by final class name and use the exact name returned by `list_toolsets`; do not hardcode a prefix.

### Derived Blueprint Discovery

When starting from a native or Blueprint parent class:

1. Use `ObjectTools.search_subclasses` with the parent class and an optional class-name filter.
2. Use `AssetTools.find_assets` under focused content roots.
3. Correlate generated-class and parent-class tags to the discovered class paths.
4. Prioritize packages referenced by maps, GameMode defaults, nearby feature folders, input/animation/widget properties, dependencies, and referencers.
5. Inspect selected Blueprints with `BlueprintTools` and `ObjectTools`.

Include indirect descendants unless the user explicitly asks for direct children only.

### Blueprint Interpretation

- Follow linked execution pins before data pins.
- Identify events, function entries, construction scripts, delegates, timelines, latent nodes, branches, calls, and variable reads/writes.
- Use `read_graph_dsl` for a compact graph view; use node and connected-subgraph tools for focused detail.
- Read Blueprint CDO and component properties only when they affect the question.
- Explain runtime behavior instead of returning a node inventory.

## Delegated Roles

When the user or active policy permits delegation:

- Use `ue-code-reader` for independent source/config scopes.
- Use `ue-asset-scanner` for read-only Unreal MCP asset scopes.
- Parallelize independent filesystem reads if useful, but serialize editor-driven MCP work against the same Unreal session.
- The primary agent must integrate and cross-check all reports.

If delegation is unavailable or not permitted, perform the same workflow directly.

## Safety

- Do not call setters, creation tools, compile tools, save tools, `write_file`, or mutating editor actions.
- Do not edit `.uasset` bytes or treat them as source text.
- Do not save or resave packages.
- Do not use `ProgrammaticToolset` merely to bypass focused read-only tools.
- Use exact `/Game/...` package paths and keep searches narrow.

## Response

Answer in the user's language. Lead with the gameplay conclusion. Include relevant files/classes, asset paths, resolved MCP toolsets, and decisive observations. End with explicit limits, especially unavailable assets, stale editor state, inferred behavior, or runtime behavior that was not tested.
