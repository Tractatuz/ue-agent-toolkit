---
name: install-ue-agents
description: Install or update the UE Agent Toolkit native Codex custom-agent TOML files in an Unreal project's .codex/agents directory. Use when a user asks to install, restore, distribute, sync, or update the plugin's ue-code-reader, ue-code-writer, ue-code-reviewer, ue-asset-scanner, ue-asset-editor, or ue-tester agents.
---

# Install UE Agents

Install the six native Codex custom agents bundled with this plugin into the target Unreal project. Treat existing agent files as user-owned configuration and never overwrite a conflict without explicit approval.

## Workflow

1. Resolve the target project root.

Use the directory containing the target `.uproject`. Do not install into the plugin cache or the toolkit source repository unless that directory is itself the user's intended Unreal project.

2. Resolve the installer.

Use `scripts/install_agents.py` beside this `SKILL.md`. The script reads agent templates from the plugin's `assets/agents/` directory.

3. Preview the installation.

Run:

```shell
py -3 "<skill-directory>\scripts\install_agents.py" --project-root "<unreal-project-root>" --dry-run
```

If the machine exposes Python as `python3` instead of `py -3`, use that launcher.

4. Handle conflicts safely.

- If every destination is missing or identical, continue.
- If the preview reports a conflict, show the affected agent filenames and stop for explicit overwrite approval.
- Never use `--force` based on an assumption.

5. Install the agents.

Run the same command without `--dry-run`. Add `--force` only after the user explicitly approves replacing the reported conflicting files.

6. Verify the result.

Confirm that these files exist under `<unreal-project-root>/.codex/agents/`:

- `ue-code-reader.toml`
- `ue-code-writer.toml`
- `ue-code-reviewer.toml`
- `ue-asset-scanner.toml`
- `ue-asset-editor.toml`
- `ue-tester.toml`

Report installed, unchanged, and replaced files separately. Tell the user to start a new Codex task so the newly installed custom agents are loaded.
