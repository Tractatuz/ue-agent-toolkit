# UnrealMCPToolsets

`UnrealMCPToolsets` is an editor-only Unreal Engine plugin that supplies
project-specific toolsets and enables the engine toolset stack used by the UE
Agent Toolkit through Unreal MCP.

The `0.2.x` series contains the Animation Blueprint state-machine toolset and
a focused PIE Enhanced Input toolset. The public reflected tool schemas are
`UAnimBlueprintToolset` and `UPlaytestToolset`.

## Requirements

- Unreal Engine 5.8
- The engine `ModelContextProtocol`, `ToolsetRegistry`, `EditorToolset`, and
  `EnhancedInput` plugins
- Optional engine `AutomationTestToolset`, `SlateInspectorToolset`, and
  `UMGToolSet` plugins, enabled explicitly when those workflows are needed
- The engine `PythonScriptPlugin`, enabled explicitly by the project owner, for
  the Python-based `AssetTools`, `BlueprintTools`, `ObjectTools`, and related
  EditorToolset registrations
- An editor target; the plugin is not loaded by runtime or packaged game targets

## Installation

Copy this directory to `<ProjectRoot>/Plugins/UnrealMCPToolsets`, enable the
plugin, and rebuild the project editor target. Start the MCP server from the
engine setting or launch the editor with `-ModelContextProtocolStartServer`.
The default endpoint is `http://127.0.0.1:8000/mcp`.

`UnrealMCPToolsets` does not auto-enable `PythonScriptPlugin`. Review that
editor scripting capability and enable it explicitly when the Python-based
EditorToolset operations are required.

Only source files are distributed. Do not copy `Binaries/`, `Intermediate/`,
`Saved/`, or other generated directories between projects.

## Project-specific toolset

`UAnimBlueprintToolset` provides:

- `ListStateMachines`
- `GetStateMachine`
- `CreateState`
- `DeleteState`
- `CreateTransition`
- `DeleteTransition`
- `SetTransitionSettings`

Read operations inspect existing Animation Blueprint state machines. Write
operations can optionally compile and save the modified asset.

Asset discovery, Blueprint and UObject inspection/editing, PIE control, log
access, and viewport capture come from `EditorToolset`. Automation and
Slate/UMG operations come from their separately enabled optional engine
toolsets. Codex discovers their live schemas with `list_toolsets` and
`describe_toolset` before calling them through Unreal MCP.

`UPlaytestToolset` complements those engine toolsets with:

- `InjectInputAction`
- `StartInputAction`
- `UpdateInputAction`
- `StopInputAction`
- `IsInputActionInjected`
- `InjectInputActionForDuration`

These calls operate only on local players in an active in-process PIE session.
They accept an Enhanced Input action, a vector value that is converted to the
action's declared value type, and a player index. The duration call is bounded
to 30 seconds, refuses to take over an already injected action, and stops its
own continuous injection before completing.

## Compatibility

Version `0.2.0` targets Unreal Engine 5.8. Support for additional
engine versions must be demonstrated by an editor-target build and tool smoke
test before it is added to the compatibility matrix.

## Smoke test

`Tests/SmokeTest.py` validates plugin loading, ToolsetRegistry registration,
both complete tool schemas, Animation Blueprint read/write operations,
compile/save options, cleanup, and representative errors. Runtime input calls
still require a live PIE smoke test with a project Input Action.

Enable the engine `PythonScriptPlugin` for the test run and execute the script
with `UnrealEditor-Cmd`. By default it looks for an Animation Blueprint from
the UE Third Person template variants. For another project, set
`UNREAL_MCP_TOOLSETS_TEST_ASSET` to an Animation Blueprint asset path such as
`/Game/Characters/ABP_Player`.

The write test works only on a uniquely named temporary duplicate under
`/Game/__UnrealMCPToolsetsSmoke` and removes that duplicate before finishing.

## License

MIT. See `LICENSE`.
