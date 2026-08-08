# UnrealMCPToolsets

`UnrealMCPToolsets` is an editor-only Unreal Engine plugin that exposes focused
asset inspection and editing operations through the experimental
`ToolsetRegistry` plugin.

The initial `0.1.x` series contains the existing Animation Blueprint state
machine toolset. The public reflected tool schema remains named
`UAnimBlueprintToolset` so consumers do not need to migrate tool names while
the containing plugin and module become domain-neutral.

## Requirements

- Unreal Engine 5.8
- The engine `ToolsetRegistry` plugin
- An editor target; the plugin is not loaded by runtime or packaged game targets

## Installation

Copy this directory to `<ProjectRoot>/Plugins/UnrealMCPToolsets`, enable the
plugin, and rebuild the project editor target.

Only source files are distributed. Do not copy `Binaries/`, `Intermediate/`,
`Saved/`, or other generated directories between projects.

## Initial toolset

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

## Compatibility

Version `0.1.0` is validated against Unreal Engine 5.8. Support for additional
engine versions must be demonstrated by an editor-target build and tool smoke
test before it is added to the compatibility matrix.

## Smoke test

`Tests/SmokeTest.py` validates plugin loading, ToolsetRegistry registration,
the complete seven-tool schema, read operations, state and transition editing,
compile/save options, cleanup, and representative error messages.

Enable the engine `PythonScriptPlugin` for the test run and execute the script
with `UnrealEditor-Cmd`. By default it looks for an Animation Blueprint from
the UE Third Person template variants. For another project, set
`UNREAL_MCP_TOOLSETS_TEST_ASSET` to an Animation Blueprint asset path such as
`/Game/Characters/ABP_Player`.

The write test works only on a uniquely named temporary duplicate under
`/Game/__UnrealMCPToolsetsSmoke` and removes that duplicate before finishing.

## License

MIT. See `LICENSE`.
