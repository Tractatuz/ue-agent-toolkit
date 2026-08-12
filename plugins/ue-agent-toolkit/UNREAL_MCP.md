# Unreal MCP Workflow Contract

Use this contract whenever a toolkit skill or custom agent needs Unreal Editor state. It replaces the former AssetToJson, JsonToAsset, TestPlay, and TaskEvidence-specific paths.

## Connection And Discovery

The Codex plugin declares the local Streamable HTTP endpoint as `http://127.0.0.1:8000/mcp`. The project must be open in Unreal Editor with the engine `ModelContextProtocol` server started and the required Toolset plugins enabled. The Python-based EditorToolset registrations such as `AssetTools`, `BlueprintTools`, and `ObjectTools` also require the project owner to review and explicitly enable `PythonScriptPlugin`; the toolkit must not auto-enable that editor scripting capability.

Never guess a callable name or argument schema. In every new editor session:

1. Call the Unreal MCP server's `list_toolsets` tool.
2. Match toolsets by their final class name, because the module-qualified prefix can vary.
3. Call `describe_toolset` for every toolset that will be used.
4. Invoke operations with `call_tool`, passing the exact returned `toolset_name`, bare `tool_name`, and schema-conforming `arguments`.

Typical engine 5.8 toolset suffixes are:

- `AssetTools`, `BlueprintTools`, `ObjectTools`, `ActorTools`, `SceneTools`, and `ProgrammaticToolset` from `EditorToolset`.
- `EditorAppToolset` and `LogsToolset` from `EditorToolset`.
- `AutomationTestToolset` for Automation discovery and execution.
- `SlateInspectorToolset` for Slate snapshots, clicks, typing, and key presses.
- `UMGToolSet` for Widget Blueprint tree inspection and editing.
- `AnimBlueprintToolset` from the bundled `UnrealMCPToolsets` plugin.
- `PlaytestToolset` from the bundled plugin for Enhanced Input injection during PIE.

Treat a missing required suffix or failed `describe_toolset` call as a blocker for that operation. Do not fall back to Python Remote Execution or direct binary asset access.

## Asset Inspection

Use tool-native structured results instead of exporting one monolithic asset JSON document:

- Discover assets, tags, classes, dependencies, and referencers with `AssetTools`.
- Find Blueprint-derived classes with `ObjectTools.search_subclasses`, then correlate class paths to assets with `AssetTools.find_assets` and asset tags.
- Load an asset with `AssetTools.load_asset` only when an object reference is needed by another tool.
- Inspect Blueprint parent, graphs, functions, events, variables, node data, connected subgraphs, and graph DSL with `BlueprintTools`.
- Inspect CDOs, components, data assets, input assets, and other UObject properties with `ObjectTools.list_properties` followed by a narrow `get_properties` call.
- Inspect Widget Blueprint trees with `UMGToolSet` and Animation Blueprint state machines with specialized toolsets.

Inspection is read-only. Do not call setters, save tools, compile tools, write tools, or editor actions that mutate state.

## Asset Editing

Use focused Unreal tool calls instead of applying a generic JSON patch:

1. Describe the specific editing toolsets.
2. Confirm the package path and call `AssetTools.can_edit_asset` before changing an existing asset.
3. Read the current structure and defaults needed to construct the smallest change.
4. Use the type-specific creation/editing toolset. For Blueprints, prefer `BlueprintTools.write_graph_dsl` for graph changes and `ObjectTools.set_properties` for narrow defaults. Use `UMGToolSet`, data, material, scene, or bundled domain toolsets when applicable.
5. Compile the affected Blueprint or Widget Blueprint where supported.
6. Re-read the edited state and compare it with the requested result.
7. Save only explicit package paths with `AssetTools.save_assets` after successful verification.
8. Confirm `AssetTools.is_dirty` is false for every saved package.

Run mutating editor calls sequentially. Do not use broad save-all, destructive delete/move, or `ProgrammaticToolset` for a mutation when focused tools exist. If a multi-call atomic edit genuinely needs `ProgrammaticToolset`, inspect its schema first, rely on its rollback behavior, and commit only after every check succeeds.

## PIE And Automation Validation

Use Unreal MCP instead of launching a separate JSON playtest runner:

- Use `SceneTools.load_level` before PIE when the map is part of the acceptance criteria.
- Use `EditorAppToolset.StartPIE`, `IsPIERunning`, and `StopPIE` for a bounded in-process PIE session.
- Query PIE actors with `SceneTools.find_actors`; inspect transforms, tags, components, and UObject properties with `ActorTools` and `ObjectTools`.
- Inject Enhanced Input through `PlaytestToolset`: use `InjectInputAction` for one frame, `InjectInputActionForDuration` for a bounded hold, or the start/update/stop calls for a controlled sequence. The bounded call refuses an action already under continuous injection. Always stop any continuous injection during cleanup.
- Inspect and operate UI through `SlateInspectorToolset` snapshots and action tools. `PressKey` drives focused Slate/viewport input; use `PlaytestToolset` when the acceptance criterion names an Enhanced Input action.
- Use `LogsToolset.get_log_entries` for scoped error and warning evidence.
- Use `EditorAppToolset.CaptureViewport`, `CaptureEditorImage`, or `CaptureAssetImage` when visual proof matters.
- Use `AutomationTestToolset.DiscoverTests`, `ListTests`, `RunTests` or `RunTestsByFilter`, then `GetTestStatus` and `GetTestResults` for deterministic Automation coverage.

Always stop PIE in cleanup, including after a failed assertion. Editor launch or PIE startup alone is not a passing test.

## MCP Evidence Packet

Replace a dedicated evidence plugin with a compact evidence packet written through `AssetTools.write_file` to `Saved/Agent/Evidence/<test-name>.json`. The packet is evidence, not a source-controlled project artifact.

Use this shape:

```json
{
  "schema": "ue.mcp.evidence.v1",
  "name": "FeatureSmoke",
  "status": "pass",
  "scope": "Short description of the behavior checked",
  "toolsets": ["resolved toolset names"],
  "checks": [
    {
      "id": "player-exists",
      "status": "pass",
      "tool": "SceneTools.find_actors",
      "result": "One actor with tag Player"
    }
  ],
  "artifacts": [],
  "errors": [],
  "residual_risks": []
}
```

Use `pass`, `fail`, or `blocked`. Record concise inputs/results, relevant Automation summaries, log excerpts, and artifact identifiers or paths. Do not store secrets, huge raw MCP payloads, or base64 image bodies in the JSON. A packet must not say `pass` unless every required check was actually observed.

## Safety And Reporting

- Use exact `/Game/...` package paths and explicit asset lists.
- Never edit `.uasset` bytes directly.
- Never infer absent Blueprint behavior from an unavailable MCP connection.
- Distinguish source/config static analysis, MCP-observed editor state, build proof, Automation proof, and PIE proof.
- Report resolved toolset names, important calls, changed or inspected package paths, evidence packet paths, failures, and untested risks.
