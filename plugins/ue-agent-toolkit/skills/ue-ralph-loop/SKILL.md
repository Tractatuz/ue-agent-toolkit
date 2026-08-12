---
name: ue-ralph-loop
description: Run an end-to-end Unreal Engine development loop from spec and plan through implementation, Unreal MCP validation, structured evidence, self-evaluation, iteration, and review handoff. Use when the user asks for autonomous or full-loop delivery.
---

# UE Ralph Loop

Coordinate one bounded pass at a time: requirements, plan, focused analysis, smallest implementation, validation, evidence, evaluation, and a deliberate next attempt when needed.

## Required Reference

Before any Unreal MCP call, read `../../UNREAL_MCP.md` completely. Every editor/asset/test/evidence step must follow that contract.

## Ordered Attempt

1. **Read goal and prior state.** Inspect the user goal, current working tree, spec, plan, previous result/evidence packets, and known failures. Do not trust hidden memory in place of artifacts.
2. **Re-check the spec.** Use `ue-spec`. Classify `Ready`, `Ready with assumptions`, or `Blocked by open questions`.
3. **Revise the plan.** Use `ue-plan`. Update tasks and validation whenever evidence invalidates an assumption or reveals a dependency.
4. **Analyze current context.** Use `ue-analyze` for the source/config/assets needed by the next task. Asset/editor evidence comes through Unreal MCP.
5. **Implement the next smallest change.** Use `ue-implement`. Keep unrelated discoveries out of the change set.
6. **Validate.** Use `ue-test` for build, Automation, and/or bounded MCP PIE checks. Produce an `ue.mcp.evidence.v1` packet for editor-driven validation.
7. **Evaluate.** Compare implementation and evidence with the goal, current spec, plan, and every acceptance criterion.
8. **Decide.** Stop as complete/blocked, or create a self-contained re-entry packet and start the next attempt sequentially.

## Status Contract

Use one terminal evaluation status:

- `Complete`: all required criteria are implemented and proven.
- `Complete with residual risk`: required criteria pass, with explicitly bounded untested risk.
- `Partial`: useful implementation exists but required work remains.
- `Validation failed`: implementation exists and a required check failed.
- `Blocked`: a concrete external prerequisite, permission, requirement, editor/server/toolset, or project state prevents progress.

Do not mark complete from static inspection, a successful build alone when runtime behavior matters, editor launch, PIE startup, or the existence of an evidence file.

## Unreal MCP Gates

Before editor work in each fresh task:

1. Confirm the local Unreal MCP server is callable.
2. Call `list_toolsets`.
3. Match and describe every required toolset.
4. Record resolved names in the attempt/result packet.

Asset inspection uses tool-native structured reads. Asset mutation requires permission, before-state, focused type-specific calls, compile/validation, read-back, explicit save, and clean dirty-state verification. Mutating MCP work runs sequentially.

Automation requires discovery, exact test selection, terminal results, and timeout cleanup. PIE requires an explicit map when relevant, bounded start/stop, observable assertions, scoped logs/captures, and confirmed cleanup. Write the final evidence packet through `AssetTools.write_file` under `Saved/Agent/Evidence/`.

If Unreal MCP is unavailable:

- code/config-only analysis or implementation may continue only when asset/editor state cannot alter correctness;
- never infer missing asset behavior;
- do not claim runtime validation;
- report the exact server/toolset/setup blocker.

## Artifacts

- Source-controlled spec and plan documents: use the project documentation convention when the user requests durable artifacts.
- Temporary attempt packets, logs, command output, and status JSON: `Saved/Agent/RalphLoop/`.
- MCP validation evidence: `Saved/Agent/Evidence/` with schema `ue.mcp.evidence.v1`.
- Do not put source-controlled implementation under `Saved/`.

Each re-entry packet must include:

- goal and current readiness;
- spec/plan paths or embedded summaries;
- current working-tree state and changed paths;
- resolved Unreal MCP toolsets and editor/server prerequisites;
- last validation status, evidence path, and first actionable failure;
- next smallest task, constraints, and stop conditions.

## Fresh Attempt Helper

When the user asked for autonomous fresh-session iteration, use `scripts/run_ue_ralph_loop.py` beside this skill:

```bash
python "scripts/run_ue_ralph_loop.py" --feature "<feature>" --goal "<goal>"
```

Useful options include `--goal-file`, `--input-packet`, `--spec`, `--plan`, `--max-iterations`, `--model`, `--permission-mode`, `--claude-bin`, `--timeout-seconds`, `--artifacts-dir`, and `--dry-run`.

- Run attempts sequentially because they share a working tree and Unreal Editor.
- Default to `acceptEdits`; use `bypassPermissions` only with explicit user authorization and appropriate isolation.
- Each fresh `claude -p` session must load the ue-agent-toolkit plugin's Unreal MCP connection and start by rediscovering live toolsets.
- Stop on complete, complete-with-residual-risk, a genuine blocker, user cancellation, or the iteration limit.

## Delegation

Use specialized agents only when the user or active policy permits it:

- `ue-code-reader`: read-only C++/config evidence.
- `ue-asset-scanner`: read-only Unreal MCP asset evidence.
- `ue-code-writer`: scoped C++/config changes.
- `ue-asset-editor`: one sequential Unreal MCP asset flow.
- `ue-tester`: build, Automation, MCP PIE, and evidence.
- `ue-code-reviewer`: independent C++/config review.

Give write ownership explicitly, never assign overlapping files, and never parallelize mutations, saves, Automation, PIE, or shared editor state. The coordinator owns integration and evaluation.

## Safety

- Follow `CLAUDE.md`; preserve user changes and never revert without permission.
- Prefer the smallest correct change and keep high-impact files explicit.
- Never edit `.uasset` bytes or generated directories.
- Keep tool schemas live: discover and describe rather than guessing.
- Stop destructive or materially broader actions for user approval.

## Final Handoff

Answer in the user's language. Lead with the final status. Summarize implemented files/assets, resolved MCP toolsets, build/Automation/PIE results, evidence/result packet paths, cleanup state, review findings, blockers, and residual risks. Clearly distinguish static, build, editor, Automation, and PIE proof.
