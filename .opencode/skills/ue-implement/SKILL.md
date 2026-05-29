---
name: ue-implement
description: Use when implementing Unreal Engine features with C++/Config code changes or JsonToAsset asset creation/modification.
---

## Purpose

Use this skill as the primary workflow when an agent needs to implement Unreal Engine gameplay, UI, input, animation, data, or content-facing features.
The goal is to decide whether the requested behavior belongs in source code, project config, Unreal assets, or a combination, then coordinate focused implementation agents safely.

## Trigger Conditions

Use this skill when the user asks to add, change, or fix Unreal Engine behavior and implementation is expected.
Typical triggers include C++ gameplay code, components, actors, pawns, controllers, widgets, animation hooks, Enhanced Input setup, data assets, Blueprint-backed defaults, JsonToAsset-generated assets, and asset edits.

Do not use this skill as the first step for a very rough feature request where the behavior is not yet specified. Use the `question` tool to ask whether the user wants to create or refine a spec first.
If the user chooses spec-first, use `ue-spec`; return to this skill only after the spec is ready for implementation.

Do not use this skill for analysis-only questions. Use `ue-analyze` instead when the user asks how existing gameplay works and does not ask for implementation.

## Prerequisites

- The project must have the `JsonToAsset` editor plugin enabled for asset patching.
- The Unreal Editor for the current project must be running with Python Remote Execution available for `scripts/apply_json_to_asset.py`.
- JsonToAsset currently patches Blueprint assets. To add a Blueprint asset, use the helper's `--create-missing-blueprint` option to create an empty Blueprint before applying the patch.
- If the plugin, editor, or remote execution is unavailable, report that asset editing could not be performed; do not modify `.uasset` files directly.

## Core Decision

First classify the requested implementation surface:

- Prefer C++ or config when the change is runtime logic, networking authority, replication, component composition, input binding code, validation, persistence, or broadly reusable behavior.
- Prefer assets when the change is primarily authored data, visual structure, Blueprint graph/default changes, widgets/layouts, animation assets, input mapping assets, data tables, data assets, maps, or content references.
- Use both when code needs reflected extension points, properties, or classes, and assets must provide defaults, references, or authored content.
- Ask one short clarifying question if choosing code versus asset would change the user-visible result and the request does not provide enough information.

When in doubt, keep the smallest correct implementation in code and avoid binary asset edits unless the feature clearly requires assets.

## Required Agents

Use the Task tool with these project subagents after opencode has been restarted and the agents are available:

- `ue-code-writer`: implements C++ and config changes. Launch multiple instances in parallel only when their file scopes are independent.
- `ue-asset-editor`: implements asset additions or modifications through JsonToAsset. Launch exactly one instance and run asset work sequentially.

If these subagents are unavailable in the running session, state that opencode must be restarted after the `.opencode` changes, then continue with the best available built-in agent only if the user asks you to proceed immediately.

## Workflow

1. Understand the request.

Identify the feature, expected runtime behavior, target classes/assets, networking requirements, editor/runtime constraints, and verification path.

2. Inspect existing patterns.

Read nearby C++ headers and implementation files, module files, relevant `Config/*.ini`, and existing assets or asset JSON when they affect the implementation. Do not assume project architecture from Unreal defaults.

3. Decide code, asset, or hybrid.

Record the decision briefly before delegating. Include why asset changes are necessary if any `.uasset` or JsonToAsset operation will be used.

4. Split code work for parallel implementation.

When code changes are needed, create focused `ue-code-writer` tasks with non-overlapping responsibilities, such as one class/component per task or one subsystem plus its tests/config. Give each task exact files or search targets, expected behavior, constraints, and verification commands.

Do not ask two `ue-code-writer` agents to edit the same file unless the sequence is explicitly controlled by the primary agent.

5. Run asset work sequentially.

When asset creation or modification is needed, create one `ue-asset-editor` task. Provide the intended package paths, asset types, references, properties, and any source code symbols that the asset must bind to.

Do not parallelize JsonToAsset work, Unreal Remote Execution work, package saves, or editor-driven asset operations.

6. Integrate results.

Review every agent result, inspect diffs, resolve conflicts manually, and ensure code and assets reference each other correctly. Do not assume a subagent's final message is sufficient verification.

7. Verify.

Build after C++ changes when possible. Run targeted tests or editor validation when available. For asset work, verify JsonToAsset output, asset paths, references, compile status, and package save status.

## Code Implementation Rules

- Follow `AGENTS.md` and existing Unreal project style.
- Prefer minimal C++ changes over Blueprint or binary asset edits when feasible.
- Preserve reflected API compatibility unless the user explicitly approves renames/removals.
- Avoid gameplay logic in constructors beyond default subobject creation and default values.
- Preserve networking authority, RPC, and replication intent.
- Avoid adding Tick unless there is a clear need.
- Prefer events, delegates, timers, components, subsystems, or data-driven configuration.
- Treat `.uproject`, `.uplugin`, `.Build.cs`, and `Config/*.ini` edits as high-impact and call them out.
- Do not edit generated output under `Binaries/`, `Intermediate/`, `Saved/`, or `DerivedDataCache/`.

## Asset Implementation Rules

- Use `scripts/apply_json_to_asset.py` for Blueprint asset creation or modification through JsonToAsset.
- Do not edit `.uasset` binary content directly.
- Keep asset package paths explicit and stable.
- Use source-controlled asset JSON or JsonToAsset inputs when available; otherwise have `ue-asset-editor` create the smallest required JsonToAsset input.
- Save or resave only the packages needed for the requested feature.
- Do not run destructive editor commands.
- If the editor, JsonToAsset plugin, or required remote execution path is unavailable, stop asset editing and report the blocker.
- Call out every created or modified asset path in the final response.

## JsonToAsset Helper

Run the helper with the Bash tool. Set the Bash tool `workdir` to the directory that contains this `SKILL.md` unless you use an absolute script path:

```powershell
py -3 "scripts\apply_json_to_asset.py" --json-file "Saved/JsonToAsset/Patch.json"
```

Common options:

- `--json-file <path>`: JsonToAsset patch JSON file. Relative paths are resolved from the project root.
- `--result-json <path>`: result JSON path. Defaults to `Saved/JsonToAsset/<patch-name>.result.json`.
- `--create-missing-blueprint`: create the target Blueprint if it does not exist before applying the patch.
- `--parent-class <path>`: parent class for `--create-missing-blueprint`, default `/Script/Engine.Actor`.
- `--no-save`: apply without saving the asset package.
- `--no-compile`: apply without compiling the Blueprint.
- `--no-graph-changes`: patch class/component defaults only.
- `--allow-structural-changes`: pass through JsonToAsset's structural-change opt-in. The current plugin may warn if unsupported.
- `--validate-json-only`: validate the local JSON shape and target path without contacting Unreal.
- `--timeout-seconds <seconds>`: remote execution node discovery timeout.
- `--engine-path <path>`: explicit Unreal Engine root. If omitted, the helper resolves the engine from the project's `EngineAssociation`, registry entries, or `OPENCODE_UNREAL_ENGINE_PATH`.

Minimal patch JSON shape:

```json
{
  "schema": "ue.json_to_asset.patch.v1",
  "asset": {
    "path": "/Game/Blueprints/BP_Example"
  },
  "class_defaults": {
    "properties": [
      { "name": "SomeProperty", "value": "42" }
    ]
  }
}
```

Patch fields supported by the current plugin include:

- `asset.path` or `asset.object_path`: target Blueprint package or object path.
- `class_defaults.properties[]`: CDO property imports using Unreal text export values.
- `components[]`: existing SCS component defaults, matched by `variable_name` or `component_template`.
- `graphs[]`: existing graph node comments, positions, pin defaults, and rebuilt links.

The helper is sequential by design. Do not run multiple instances in parallel, and do not parallelize it with other Unreal Remote Execution commands.

## Delegation Templates

Use a prompt like this for each parallel code task:

```text
Implement the code portion of <feature> in this Unreal project.
Scope: <specific classes/files or search targets>.
Expected behavior: <runtime behavior>.
Constraints: follow AGENTS.md, preserve reflected API compatibility, avoid asset edits, do not touch unrelated files.
Verification: <build/test command if known>.
Return: files changed, behavior implemented, verification result, and any integration notes.
```

Use a prompt like this for the single asset task:

```text
Implement the asset portion of <feature> using JsonToAsset in this Unreal project.
Scope: <asset package paths and asset types>.
Inputs: <properties, references, classes, defaults, source JSON if any>.
Constraints: use scripts/apply_json_to_asset.py, one sequential asset editing flow, do not edit binary assets directly, save only required packages.
Verification: confirm created/modified package paths, references, compile/status results, helper output, and result JSON.
Return: assets changed, JsonToAsset patch JSON, helper command used, verification result, and any required code integration notes.
```

## Response Style

- Answer in Korean unless the user asks otherwise.
- State the implementation surface selected: code, asset, or hybrid.
- Mention whether parallel `ue-code-writer` agents and/or the sequential `ue-asset-editor` agent were used.
- Summarize changed files and asset paths.
- Report build/test/editor verification, or explain why verification was skipped.
- Explicitly call out binary asset, broad config, plugin, or module changes.
