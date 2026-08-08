---
name: ue-analyze
description: Use when analyzing Unreal Engine gameplay behavior across C++, Config, Blueprint, and asset data.
---

## Purpose

Use this skill as the primary workflow when an agent needs to analyze all or part of an Unreal Engine project.
The goal is to explain runtime behavior from evidence across source code, config, Blueprint graphs, component defaults, CDO values, input assets, animation/UI assets, content references and so on.

## Prerequisites

- The project must have the `AssetToJson` editor plugin enabled when asset internals need inspection.
- The Unreal Editor for the current project must be running with Python Remote Execution available for `scripts/find_derived_blueprint_assets.py` and `scripts/read_asset_json.py`.
- If the plugin, editor, or remote execution is unavailable, report that asset inspection could not be performed; do not infer that assets have no relevant behavior.

## Workflow

1. Clarify Scope First

If the requested analysis scope is ambiguous, do not begin code/config/asset inspection immediately. Ask the user's intent first.

If the request is broad, lacks a stated focus/depth/goal, or cannot be answered deterministically, ask clarifying questions using the available tool.

Subagent orchestration:

- When multi-agent tools are available and delegation is appropriate, create focused subagent tasks with the matching installed custom agent.
- Use the `ue-code-reader` custom agent for independent C++ and config evidence-gathering scopes. Multiple code-reading tasks may run in parallel when they only search or read files.
- Use the `ue-asset-scanner` custom agent for Blueprint and asset evidence that requires Unreal Asset Registry, AssetToJson, or Python Remote Execution. Run asset-scanning tasks sequentially, one asset-discovery or asset-read scope at a time.
- Resolve helper scripts from the `scripts/` directory beside this `SKILL.md`. When delegating asset work, pass its absolute path along with the relevant class paths, asset paths, search roots, and whether detailed node properties are needed.
- The primary agent remains responsible for combining subagent reports, cross-validating code/config evidence with asset evidence, and writing the final analysis. Do not forward subagent conclusions without checking how they fit the full runtime path.

2. Classify what must be inspected.

Identify the likely relevant source files, config files, assets, Blueprints, input mappings, animation assets, widgets, maps, data assets, and references needed to answer the user's question.

3. Read source and config evidence.

Search and read relevant C++ headers, C++ implementation files, `.Build.cs`, target files, and `Config/*.ini`. Use source code to identify class ownership, inheritance, Blueprint hooks, reflected properties, input bindings, delegates, components, constructors, lifecycle functions, and runtime control flow.

If a relevant `UPROPERTY` can be edited or overridden by Blueprint defaults (`EditDefaultsOnly`, `EditAnywhere`, `EditInstanceOnly`, `ExposeOnSpawn`, instanced subobjects, or asset-assigned defaults), classify the owning Blueprint asset as required evidence and read it before finalizing the analysis.

4. Inspect assets when asset data affects the answer.

Locate related assets from C++ properties, config paths, soft object references, input mapping contexts, animation classes, widgets, Blueprint class references, maps, naming patterns, or asset registry relationships.

When source analysis starts from a C++ class and Blueprint subclasses may override defaults, components, graphs, animation classes, widgets, events, or exposed properties, first discover derived Blueprint assets with `scripts/find_derived_blueprint_assets.py`. Use the discovered assets to decide which specific Blueprints must be inspected with `scripts/read_asset_json.py`.

When binary asset data must be read, use `scripts/read_asset_json.py`, such as for Blueprint graphs, Blueprint variables, component defaults, CDO values, timelines, Enhanced Input assets, widget structure, animation data, or asset metadata. Do not treat `.uasset` binary files as directly readable source.

5. Cross-validate the evidence.

Connect C++ implementation, config values, Blueprint graph execution, component defaults, CDO/default values, and asset references into one runtime explanation. Prefer explaining behavior over listing files or nodes.

6. Report confidence and limits.

State what evidence was used, what was cross-validated, and what could not be inspected. Distinguish confirmed behavior from inference.

## C++ And Config Analysis

- Read the local class hierarchy first, especially base character, pawn, controller, component, ability, animation, UI, and feature-specific classes.
- Inspect `UPROPERTY` and `UFUNCTION` metadata to understand Blueprint-facing extension points and defaults.
- When a relevant `UPROPERTY` is Blueprint-editable, Blueprint-readable with asset-assigned defaults, exposed on spawn, instanced, or otherwise likely to differ from the C++ constructor value, inspect the owning Blueprint before treating the C++ value as final behavior.
- If the owning Blueprint is not already known, search for Blueprint assets derived from the relevant native or Blueprint parent class before finalizing the analysis.
- Check constructors, `BeginPlay`, `SetupPlayerInputComponent`, tick functions, overlap callbacks, delegates, timers, RPCs, and component initialization.
- Check relevant `.ini` files for maps, GameMode, input settings, redirects, collision channels, plugin settings, and project defaults.
- Preserve Unreal terminology precisely: package path, object path, generated class, CDO, component, graph, pin, node, mapping context, action, and asset registry data.

## Derived Blueprint Discovery

Use this step when you know a C++ or Blueprint parent class but do not know which Blueprint assets inherit from it. The helper uses Unreal Asset Registry derived-class data, so indirect inheritance through native C++ classes and Blueprint generated classes is included unless `--direct-only` is specified. For example, searching `/Script/Engine.Actor` can return Blueprints whose immediate parent is a project C++ class that ultimately derives from `AActor`.

Run the helper with the Bash tool. Set the Bash tool `workdir` to the directory that contains this `SKILL.md` unless you use an absolute script path:

```shell
py -3 "scripts\find_derived_blueprint_assets.py" --class-path "/Script/ThirdPerson.ThirdPersonCharacter" --no-output-file
```

Supported options:

- `--class-path <path>`: parent class path, usually `/Script/<Module>.<ClassName>` for native C++ classes or a generated class path for Blueprint classes.
- `--search-paths <paths>`: content roots to scan, default is `/Game`.
- `--direct-only`: include only Blueprints whose immediate parent class is the target class.
- `--no-output-file`: return JSON in command output for immediate context.
- `--output-json <path>`: save JSON to a specific path.
- `--timeout-seconds <seconds>`: remote execution node discovery timeout.
- `--engine-path <path>`: explicit Unreal Engine root. If omitted, the helper resolves the engine from the project's `EngineAssociation`, registry entries, or `CODEX_UNREAL_ENGINE_PATH`.

The helper requires an editor instance with Python Remote Execution available. If no remote node is found, report that Blueprint discovery could not be performed; do not guess that no derived Blueprints exist.

Run derived Blueprint discovery commands sequentially. Do not run multiple `find_derived_blueprint_assets.py` instances in parallel, and do not parallelize them with other Unreal Remote Execution commands, because the editor command socket can reject or reset concurrent connections.

Interpret the returned JSON fields:

- `assets[].path`: package path to pass to `scripts/read_asset_json.py`.
- `assets[].object_path`: full Blueprint asset object path.
- `assets[].parent_class`: immediate parent class.
- `assets[].generated_class`: generated class for runtime inheritance checks.
- `assets[].is_direct_child`: whether the Blueprint directly inherits from the searched class.

If many assets are returned, prioritize ones referenced by maps, config, GameMode defaults, input/animation/widget properties, nearby feature folders, or naming patterns. Then read the selected assets with `scripts/read_asset_json.py`.

## Asset Path Normalization

Accept common Unreal asset path forms and convert them to a long package path or object path as needed:

```text
/Game/<FolderPath>/<AssetName>
/Game/<FolderPath>/<AssetName>.<AssetName>
Content/<FolderPath>/<AssetName>.uasset
<AssetName> when the location is obvious from search results
```

If the path is ambiguous, locate it with file search, usually by searching `Content/**/*.uasset` for the asset name.

## Asset JSON Helper

Use `scripts/read_asset_json.py` only when asset internals are needed for the analysis.

Run the helper with the Bash tool. Set the Bash tool `workdir` to the directory that contains this `SKILL.md` unless you use an absolute script path:

```shell
py -3 "scripts\read_asset_json.py" --asset-path "/Game/<FolderPath>/<AssetName>" --no-output-file
```

Supported options:

- `--asset-path <path>`: Unreal package path, object path, or recognizable asset file path.
- `--include-node-properties`: include detailed Blueprint node properties when needed.
- `--no-output-file`: return JSON in command output for immediate context.
- `--output-json <path>`: save JSON to a specific output path.
- `--timeout-seconds <seconds>`: remote execution node discovery timeout.
- `--engine-path <path>`: explicit Unreal Engine root. If omitted, the helper resolves the engine from the project's `EngineAssociation`, registry entries, or `CODEX_UNREAL_ENGINE_PATH`.

Examples:

```shell
py -3 "scripts\read_asset_json.py" --asset-path "/Game/<FolderPath>/<AssetName>" --no-output-file
py -3 "scripts\read_asset_json.py" --asset-path "/Game/<FolderPath>/<AssetName>" --include-node-properties --no-output-file
py -3 "scripts\read_asset_json.py" --asset-path "/Game/<FolderPath>/<AssetName>" --output-json "Saved/AssetToJson/<AssetName>.json"
```

If multiple assets must be inspected, export and read them one at a time.

## Blueprint Interpretation

For Blueprint visual scripts, interpret these JSON sections when present:

- `asset`: parent class, generated class, object path
- `blueprint`: type and compile status
- `graphs`: graph name/type, nodes, pins, and links
- `variables`: Blueprint-declared variables and default text values
- `components`: Blueprint SCS component tree

Build execution flows from linked exec pins first, then data pins.

- Identify entry nodes: events, function entries, construction script entries, timeline updates, delegate events.
- Follow output exec pins to call nodes, branch nodes, macro nodes, timeline nodes, and latent nodes.
- Map important data connections: event parameters, variable gets/sets, function inputs, default objects, and default scalar values.
- Ignore comment nodes except when they clarify intent.

If asset data is missing, stale, inaccessible, or only partially exported, say so explicitly and report what was still observable.

## Response Style

- Answer in Korean unless the user asks otherwise.
- Start with the main gameplay conclusion when the task is analysis-oriented.
- Mention the evidence used: C++ files, config files, asset paths, exported JSON, or cached JSON.
- Include exact class names, function names, asset paths, and key defaults when they matter.
- For Blueprint visual scripts, explain runtime behavior rather than only listing nodes.
- State limitations clearly, including inaccessible assets, unavailable exports, stale cached data, or inferred behavior.

## Safety

- Do not modify assets while inspecting them.
- Do not save the project or resave packages unless the user explicitly asks.
- Do not run destructive editor commands.
- Keep generated JSON under `Saved/` unless the user asks for another output path.
