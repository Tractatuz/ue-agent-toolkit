---
name: ue-test
description: Use when validating Unreal Engine implementation changes with build tests, Unreal Automation tests, or TestPlay PIE playtests.
---

## Purpose

Use this skill after Unreal Engine implementation work when an agent needs to validate C++, config, asset, gameplay, UI, input, or runtime behavior changes.
The goal is to choose the smallest useful verification path, run it through the focused `ue-tester` custom agent when appropriate, and report evidence rather than guesses.

## Trigger Conditions

Use this skill when the user asks to test, validate, verify, smoke test, run build checks, run Unreal automation, run PIE validation, or confirm that an Unreal implementation works.

Use this skill after `ue-implement` changes when verification is needed.

Do not use this skill for implementation-only work. Use `ue-implement` first when code, config, or assets still need to be changed.

## Delegated Role

When multi-agent tools are available and delegation is appropriate, create a focused subagent task with the installed `ue-tester` custom agent.

If multi-agent tools are unavailable, the custom agent is not installed, or policy does not allow delegation, perform the same scoped validation in the primary session while following the testing constraints in this skill.

## Test Selection

Choose tests from the implementation surface and observable risk:

- Build test: use when C++, module rules, plugin code, reflected symbols, generated code, config references, or compile-time API usage changed.
- Unreal Automation test: use when the project already has relevant Automation, Functional Test, unit-like, editor, or plugin tests that cover the change.
- TestPlay PIE test: use when runtime behavior needs a real PIE session, Enhanced Input injection, actor assertions, widget visibility/text checks, or a gameplay smoke test through a map.

Prefer the narrowest test that can catch the likely regression. Combine build plus runtime tests when code compiles but behavior still needs proof.

## Workflow

1. Identify what changed.

Inspect the implementation summary, diffs, touched C++ files, config files, assets, plugin files, and any acceptance criteria. Do not assume a test path from file names alone.

2. Choose the validation path.

Decide whether build, Automation, TestPlay, or a combination is needed. If expected runtime behavior is unclear, ask one short question before writing a TestPlay spec.

3. Delegate focused testing.

Create a focused task assigned to the `ue-tester` custom agent, with exact scope, changed files or feature summary, selected test type, commands to run when known, expected pass criteria, and any log/result files to inspect.

4. Run tests safely.

Do not run destructive editor commands. Do not modify source, config, maps, Blueprints, or binary assets while testing. Test artifacts should go under `Saved/` unless the user asks for source-controlled test files.

5. Inspect evidence.

Use command exit codes, compiler errors, Automation reports, TestPlay result JSON, logs, and TaskEvidence JSON when available. Do not report success from a launched editor process alone.

6. Report outcome.

State what was tested, command used, pass/fail result, relevant result/log paths, and any untested risk.

## Build Tests

Use UnrealBuildTool through the engine batch file. Adjust target, platform, configuration, project path, and engine path to the local project.

```shell
& "<EnginePath>\Engine\Build\BatchFiles\Build.bat" ThirdPersonEditor Win64 Development -Project="C:\Projects\Unreal\ThirdPerson\ThirdPerson.uproject" -WaitMutex -NoHotReloadFromIDE
```

Build test guidance:

- Use the editor target for most gameplay and plugin C++ changes.
- Use `Development` unless the project or existing workflow uses a different configuration.
- Read the first actionable compiler or linker error, not only the final failure line.
- If UnrealHeaderTool fails, check reflected symbols, includes, generated headers, module dependencies, and metadata first.

## Unreal Automation Tests

Use Unreal's built-in Automation framework when a relevant test already exists or the implementation added one.

```shell
& "<EnginePath>\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "C:\Projects\Unreal\ThirdPerson\ThirdPerson.uproject" -unattended -nop4 -nosplash -nullrhi -ExecCmds="Automation RunTests <Filter>; Quit" -TestExit="Automation Test Queue Empty" -ReportOutputPath="Saved\Automation"
```

Automation guidance:

- Replace `<Filter>` with the narrowest relevant test name or category.
- Use `-nullrhi` only when the test does not require rendering, Slate interaction, or viewport-dependent behavior.
- Inspect `Saved/Automation`, the editor log, and the command exit code.
- If no relevant Automation test exists, do not pretend that running an unrelated suite validates the feature.

## TestPlay PIE Tests

Use TestPlay for JSON-defined PIE playtests that need a map, spawned actors, Enhanced Input actions, or UMG widget assertions.

Prerequisites:

- The `TestPlay` plugin must be enabled for the project.
- The `TaskEvidence` plugin must be installed and available because TestPlay writes standardized evidence.
- The spec should include an explicit `map` for repeatability unless the current loaded map is intentionally part of the test.

Run TestPlay through this skill's script:

```shell
py -3 "scripts\run_testplay.py" --spec-file "Saved\TestPlay\Specs\FeatureSmoke.json" --result-json "Saved\TestPlay\Results\FeatureSmoke.json"
```

The script launches `UnrealEditor.exe` with `-TestPlayRun=<spec>`, `-TestPlayResult=<result>`, and `-TestPlayExitOnComplete`, then fails if the result JSON is missing or reports `success: false`.

Common script options:

- `--project-file <path>`: explicit `.uproject`; otherwise the script finds the project above this skill directory.
- `--engine-path <path>`: explicit Unreal Engine root. If omitted, the script resolves the engine from the project's `EngineAssociation`, registry entries, or `CODEX_UNREAL_ENGINE_PATH`.
- `--timeout-seconds <seconds>`: kill the editor if it does not exit in time.
- `--null-rhi`: add `-nullrhi` for rendering-independent smoke tests.
- `--no-exit-on-complete`: omit `-TestPlayExitOnComplete` for manual editor inspection.
- `--extra-arg <arg>`: pass an additional UnrealEditor argument. Repeat for multiple arguments.

Minimal TestPlay spec shape:

```json
{
  "name": "FeatureSmoke",
  "map": "/Game/ThirdPerson/Maps/ThirdPersonMap",
  "timeout": 30,
  "steps": [
    { "type": "wait", "seconds": 1.0 },
    { "type": "assertActorExists", "actorTag": "Player" }
  ]
}
```

Supported step patterns in the current TestPlay plugin include:

- `wait`: fields `seconds` or `wait`.
- `waitForActor`: fields `actorTag`, `tag`, `actorName`, or `name`, plus optional `timeout`.
- `assertActorExists`: fields `actorTag`, `tag`, `actorName`, or `name`.
- `assertActorLocation`: actor lookup fields, `location` as `[x, y, z]`, and optional `tolerance`.
- `assertActorDistance`: actor lookup fields, `targetTag`, `greaterThan`, and `lessThan`.
- `inputAction`: fields `action`, optional `player`, `duration`, and `value` for Enhanced Input injection.
- `waitForWidget`: fields `name` or `widget`, optional `visible`, and optional `timeout`.
- `assertWidgetVisible`: fields `name` or `widget`.
- `assertWidgetText`: fields `name` or `widget`, and `text` for `UTextBlock` widgets.
- `clickWidget`: fields `name` or `widget`, optional `offset` as `[x, y]`, and optional `button`.

TestPlay guidance:

- Use stable actor tags or widget names rather than transient generated object names when possible.
- Keep specs small and focused on one feature or regression.
- Store ad hoc generated specs under `Saved/TestPlay/Specs/`.
- Report the result JSON path and TaskEvidence path if TestPlay wrote one.

## Delegation Template

Use a prompt like this for the tester:

```text
Validate <feature or change> in this Unreal project.
Scope: <changed files/assets/config and expected behavior>.
Selected tests: <build, Automation filter, TestPlay spec, or combination>.
Commands: <exact commands if known; otherwise choose the narrowest safe commands>.
Constraints: follow AGENTS.md, do not modify source/config/assets, keep generated test artifacts under Saved/, do not run destructive editor commands.
Pass criteria: <compile succeeds, named tests pass, TestPlay result success=true, logs contain no relevant errors>.
Return: commands run, pass/fail result, result/log/evidence paths, first actionable failure if any, and residual untested risks.
```

## Response Style

- Answer in Korean unless the user asks otherwise.
- Lead with pass/fail/blocked.
- Include exact commands run and important result paths.
- If testing was skipped or blocked, state the concrete blocker and what would be needed to run it.
- Do not overstate validation coverage; name what remains untested.
