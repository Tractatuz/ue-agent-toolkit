---
name: ue-test
description: Validate Unreal Engine changes with builds, Automation tests, or observable PIE checks driven through Unreal MCP, and write structured MCP evidence packets. Use for test, validation, smoke-test, or verification requests.
---

# UE Test

Choose the narrowest validation that can catch the likely regression and report concrete evidence. Unreal MCP owns editor Automation, PIE control, runtime inspection, UI interaction, logs, captures, and evidence-file creation.

## Required Reference

Before any Unreal MCP call, read `../../UNREAL_MCP.md` completely and follow its connection, discovery, PIE, Automation, evidence, cleanup, and reporting contract.

## Test Selection

- **Build:** C++, reflected symbols, module/plugin rules, config references, or compile-time API usage changed.
- **Automation:** a relevant Unreal Automation, Functional Test, editor test, or project/plugin test exists.
- **MCP PIE:** runtime actor/component state, a map smoke test, viewport output, logs, or UI behavior must be observed in a real in-process PIE session.
- **Build + runtime:** compilation and observable behavior both matter.

Do not run an unrelated suite and claim it covers the feature. If action-level Enhanced Input injection is required, discover and use the bundled `PlaytestToolset`; a focused Slate key press is not equivalent proof.

## Workflow

1. **Identify the risk.** Inspect diffs, changed assets/config, implementation summary, and acceptance criteria.
2. **Choose pass criteria.** Define observable checks before running anything.
3. **Run the build if needed.** Use the project editor target and read the first actionable error.
4. **Discover MCP tools.** Call `list_toolsets`, match required suffixes, then call `describe_toolset` for each before use.
5. **Run Automation or PIE.** Follow the bounded workflows below.
6. **Collect evidence.** Record exact results, scoped logs, captures, failures, and cleanup state.
7. **Write the evidence packet.** Through `AssetTools.write_file`, write `Saved/Agent/Evidence/<test-name>.json` using schema `ue.mcp.evidence.v1`.
8. **Report coverage.** State pass, fail, or blocked and identify residual untested risks.

## Build Validation

Use UnrealBuildTool through the engine batch file, adjusted to the current engine/project/target:

```powershell
& "<EnginePath>\Engine\Build\BatchFiles\Build.bat" <ProjectEditorTarget> Win64 Development -Project="<ProjectPath>" -WaitMutex -NoHotReloadFromIDE
```

- Prefer the editor target for gameplay and editor-plugin changes.
- Do not build merely to diagnose an analysis-only request.
- Record exit code and the first compiler, UHT, or linker error.

## Automation Through Unreal MCP

1. Discover and describe `AutomationTestToolset`.
2. Call `DiscoverTests` once for the editor session.
3. Use `ListTests` to confirm the exact name/filter.
4. Call `RunTests` for explicit names or `RunTestsByFilter` for a justified filter.
5. Poll `GetTestStatus` only as needed and obtain the terminal `GetTestResults` summary.
6. Call `StopTests` on timeout or user cancellation.
7. Put the exact selected tests and returned summary in the evidence packet.

A successful dispatch is not a passing test; only terminal results count.

## PIE Through Unreal MCP

Use this bounded sequence:

1. Discover and describe the needed `SceneTools`, `EditorAppToolset`, `ActorTools`, `ObjectTools`, `PlaytestToolset`, `SlateInspectorToolset`, `LogsToolset`, and `AssetTools` toolsets.
2. If the acceptance criteria name a map, load it with `SceneTools.load_level` before PIE and confirm the current level.
3. Start in-process PIE with `EditorAppToolset.StartPIE`, using an explicit warmup when project initialization needs it.
4. Confirm `IsPIERunning` before assertions.
5. Perform focused checks:
   - actor existence: `SceneTools.find_actors`;
   - transforms/tags/components: `ActorTools`;
   - runtime property values: narrow `ObjectTools.get_properties` reads;
   - Enhanced Input actions: `PlaytestToolset.InjectInputAction`, `InjectInputActionForDuration`, or a start/update/stop sequence;
   - UI state/actions: `SlateInspectorToolset.Snapshot`, `Click`, `Type`, or `PressKey`;
   - visual proof: viewport/editor capture tools;
   - errors/warnings: scoped `LogsToolset.get_log_entries`.
6. Compare every observed result with the predeclared pass criteria.
7. In cleanup, stop any continuous `PlaytestToolset` input injection, call `StopPIE` even after a failed check, then confirm `IsPIERunning` is false.
8. Write the evidence packet through Unreal MCP.

Do not modify source, config, maps, Blueprints, or assets while validating. Loading a map and starting/stopping PIE are allowed test-state operations; saving is not.

## Evidence Packet

Write compact JSON under `Saved/Agent/Evidence/` with:

- schema `ue.mcp.evidence.v1`;
- test name, scope, and `pass|fail|blocked` status;
- exact resolved toolsets;
- one check entry per pass criterion, with tool and concise observed result;
- Automation summary, log/capture identifiers or paths when relevant;
- errors, cleanup outcome, and residual risks.

Do not include secrets, full base64 images, or huge raw payloads. Never mark the packet `pass` when cleanup failed or a required observation is missing.

## Delegated Role

When the user or active policy permits delegation, assign one focused validation scope to `ue-tester`. Supply the changed surface, selected test type, pass criteria, exact map/test filter when known, and required evidence path. The primary agent still checks the returned evidence.

If delegation is unavailable or not permitted, run the same workflow directly.

## Response

Answer in the user's language and lead with `pass`, `fail`, or `blocked`. Include the build command and/or important MCP calls, Automation/PIE observations, cleanup result, evidence packet path, first actionable failure, and residual untested risks. Do not present static inspection as runtime proof.
