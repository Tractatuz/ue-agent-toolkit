---
name: install-ue-plugins
description: Install or update the UE Agent Toolkit's bundled UnrealMCPToolsets plugin and explain the Unreal MCP server prerequisites. Use when a user asks to install, restore, distribute, sync, or update the toolkit's Unreal plugins.
---

# Install UE Plugins

Install the bundled source-only `UnrealMCPToolsets` plugin into the target project's `Plugins/` directory. Preserve existing project files and require explicit approval before replacing a conflicting plugin.

## Workflow

1. **Resolve the project.** Use the directory containing the intended `.uproject`. Do not install into the Claude Code plugin cache or toolkit repository unless it is itself the requested Unreal project.
2. **Resolve the installer.** Use `scripts/install_plugins.py` beside this `SKILL.md`. It discovers payloads under `assets/Plugins/`.
3. **Preview.** Run:

```powershell
py -3 "<skill-directory>\scripts\install_plugins.py" --project-root "<unreal-project-root>" --dry-run
```

Use another available Python launcher when `py -3` is unavailable.

4. **Handle conflicts.** Missing or identical destinations are safe. Ignore generated `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, and `.vs/` directories during comparison. Show every conflict and stop for explicit replacement approval; never assume `--force`.
5. **Install.** Run the same command without `--dry-run`. Add `--force` only after approval. Approved replacement creates a backup under `<project>/.ue-agent-toolkit/backups/unreal-plugins/` before synchronizing source files.
6. **Verify files.** Confirm `<project>/Plugins/UnrealMCPToolsets/UnrealMCPToolsets.uplugin` exists and report installed, unchanged, replaced, and backup paths separately.

## Unreal MCP Setup

Do not edit `.uproject` or project config automatically unless the user separately asks for it. Explain these post-install requirements:

1. Use Unreal Engine 5.8 and enable `UnrealMCPToolsets` for the project.
2. Its descriptor enables the core engine `EnhancedInput`, `ModelContextProtocol`, `ToolsetRegistry`, and `EditorToolset` dependencies.
3. Review and explicitly enable the engine `PythonScriptPlugin` when the Python-based `AssetTools`, `BlueprintTools`, `ObjectTools`, and related EditorToolset operations are required. The toolkit does not auto-enable this editor scripting capability.
4. Explicitly enable optional `AutomationTestToolset`, `SlateInspectorToolset`, and `UMGToolSet` only when Automation, Slate interaction, or Widget Blueprint workflows need them. These are not hard plugin dependencies because their availability/build compatibility can vary by engine distribution.
5. Rebuild the project editor target because the bundle is source-only. Rebuild any optional engine Toolset whose binary family does not match the current editor.
6. Start Unreal Editor with the project and start the MCP server either from the engine setting or with `-ModelContextProtocolStartServer`.
7. The ue-agent-toolkit Claude Code plugin connects to the default local endpoint `http://127.0.0.1:8000/mcp`.
8. Start a new Claude Code session after the editor server is running. In that session, verify `list_toolsets`, then `describe_toolset` for `AssetTools`, `BlueprintTools`, `ObjectTools`, `EditorAppToolset`, `AutomationTestToolset`, `AnimBlueprintToolset`, and `PlaytestToolset` as applicable.

If a project uses a non-default MCP port or path, explain that the plugin's `.mcp.json` or the user's Claude Code MCP configuration must be adjusted before starting the new session. Do not silently rewrite the endpoint.

## Safety And Report

- Do not launch Unreal Editor or start a build unless the user requested it.
- Treat `.uproject`, `.uplugin`, `.Build.cs`, and project config edits as high-impact.
- Do not copy generated plugin output.
- Report what was changed, what still requires user/editor action, and that a live MCP smoke test has not occurred unless it was actually run.
