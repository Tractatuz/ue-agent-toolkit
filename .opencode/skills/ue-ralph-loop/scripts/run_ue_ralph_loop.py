#!/usr/bin/env python3
"""Run Ralph Loop attempts in fresh opencode sessions.

This launcher starts one fresh `opencode run` attempt session per iteration.
Each attempt session follows the ordered ue-ralph-loop steps exactly once, writes a
Markdown result packet, and writes a small JSON status file.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


TERMINAL_STATUSES = {"complete", "complete_with_residual_risk", "blocked"}
CONTINUABLE_STATUSES = {"partial", "validation_failed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an Unreal Ralph Loop through fresh opencode attempt sessions."
    )
    parser.add_argument("--feature", required=True, help="Short feature name for titles and artifact files.")
    parser.add_argument("--goal", help="Original user goal. Required unless --input-packet is provided.")
    parser.add_argument("--goal-file", help="File containing the original user goal.")
    parser.add_argument("--input-packet", help="Existing Ralph Loop packet to start from.")
    parser.add_argument("--spec", help="Optional spec document path.")
    parser.add_argument("--plan", help="Optional implementation plan path.")
    parser.add_argument("--project-root", default=".", help="Project root passed to opencode --dir.")
    parser.add_argument(
        "--artifacts-dir",
        default="Saved/Agent/RalphLoop",
        help="Directory for loop packets and attempt-session logs.",
    )
    parser.add_argument("--max-iterations", type=int, default=3, help="Maximum fresh attempt sessions to run.")
    parser.add_argument("--opencode-bin", default="opencode", help="opencode executable name or path.")
    parser.add_argument("--model", help="Optional model passed to opencode run --model.")
    parser.add_argument("--agent", help="Optional agent passed to opencode run --agent.")
    parser.add_argument("--timeout-seconds", type=int, help="Timeout per fresh opencode attempt.")
    parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Pass opencode run --dangerously-skip-permissions. Use only in trusted workspaces.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the initial packet and print the first opencode command without running it.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug[:80] or "ralph-loop"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def resolve_under_project(project_root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def load_goal(args: argparse.Namespace, project_root: Path) -> str:
    if args.goal and args.goal_file:
        raise SystemExit("Use either --goal or --goal-file, not both.")
    if args.goal:
        return args.goal.strip()
    if args.goal_file:
        goal_file = resolve_under_project(project_root, args.goal_file)
        assert goal_file is not None
        return read_text(goal_file).strip()
    if args.input_packet:
        return "Continue from input packet."
    raise SystemExit("--goal or --goal-file is required unless --input-packet is provided.")


def create_initial_packet(
    packet_path: Path,
    feature: str,
    goal: str,
    spec_path: Path | None,
    plan_path: Path | None,
) -> None:
    spec_text = str(spec_path) if spec_path else "none"
    plan_text = str(plan_path) if plan_path else "none"
    write_text(
        packet_path,
        f"""# Ralph Loop Input: {feature}

## Goal
{goal}

## Spec State
- Path: {spec_text}
- Instruction: Re-check spec readiness before implementation. If no spec path is provided, reconstruct the smallest useful spec from the goal and current project evidence.

## Plan State
- Path: {plan_text}
- Instruction: Re-check or create the implementation plan before implementation. Revise the plan if project evidence or validation failures require it.

## Attempt Contract
- Follow the ordered `ue-ralph-loop` steps exactly once in this fresh session.
- Do not spawn another opencode session during this attempt.
- Re-read the spec and plan state instead of trusting previous chat context.
- Analyze only the project context needed for the current plan.
- Implement the next smallest correct change set.
- Validate, self-evaluate, and write the requested result packet and status JSON.
""",
    )


def build_attempt_prompt(
    feature: str,
    iteration: int,
    input_packet: Path,
    result_packet: Path,
    status_json: Path,
) -> str:
    return f"""Use the `ue-ralph-loop` skill and follow its ordered loop steps.

This is iteration {iteration} for feature `{feature}`. This opencode run is the fresh session for one bounded loop attempt.

Input packet path: {input_packet}
Result packet path to write: {result_packet}
Status JSON path to write: {status_json}

Attempt requirements:
- Step 1: read the input packet and current repository state.
- Step 2: re-check the spec before implementation.
- Step 3: revise or create the implementation plan before implementation.
- Step 4: re-analyze project context needed by the updated plan.
- Step 5: implement only the next smallest correct change set.
- Step 6: validate and test with the smallest useful checks.
- Step 7: evaluate and report against the goal, spec, plan, and validation evidence.
- Step 8: do not start another opencode session directly; instead write status JSON indicating whether another fresh attempt is needed.
- Always write the result packet Markdown.
- Always write the status JSON with this shape:
  {{
    "status": "complete | complete_with_residual_risk | partial | validation_failed | blocked",
    "continue": true,
    "summary": "short result summary",
    "next_starting_gate": "Spec | Plan | Analysis | Implementation | Validation | Done",
    "first_actionable_failure": "failure, blocker, or empty string",
    "result_packet": "{result_packet}"
  }}

If the result is complete or blocked, set `continue` to false. If another fresh attempt should continue, set `continue` to true and make the result packet a self-contained re-entry packet.
"""


def build_command(
    args: argparse.Namespace,
    project_root: Path,
    title: str,
    input_packet: Path,
    prompt: str,
) -> list[str]:
    command = [
        args.opencode_bin,
        "run",
        "--dir",
        str(project_root),
        "--title",
        title,
        "--file",
        str(input_packet),
    ]
    if args.model:
        command.extend(["--model", args.model])
    if args.agent:
        command.extend(["--agent", args.agent])
    if args.dangerously_skip_permissions:
        command.append("--dangerously-skip-permissions")
    command.append(prompt)
    return command


def run_child(command: list[str], timeout_seconds: int | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
    )


def timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def read_status(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def should_continue(status: dict[str, Any], iteration: int, max_iterations: int) -> bool:
    normalized = str(status.get("status", "")).strip().lower().replace(" ", "_")
    if iteration >= max_iterations:
        return False
    if normalized in TERMINAL_STATUSES:
        return False
    if normalized in CONTINUABLE_STATUSES:
        return bool(status.get("continue", True))
    return False


def main() -> int:
    args = parse_args()
    if args.max_iterations < 1:
        raise SystemExit("--max-iterations must be at least 1.")

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        raise SystemExit(f"Project root does not exist: {project_root}")

    feature = args.feature.strip()
    slug = slugify(feature)
    artifacts_dir = resolve_under_project(project_root, args.artifacts_dir)
    assert artifacts_dir is not None
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    spec_path = resolve_under_project(project_root, args.spec)
    plan_path = resolve_under_project(project_root, args.plan)
    goal = load_goal(args, project_root)

    if args.input_packet:
        input_packet = resolve_under_project(project_root, args.input_packet)
        assert input_packet is not None
        if not input_packet.exists():
            raise SystemExit(f"Input packet does not exist: {input_packet}")
    else:
        input_packet = artifacts_dir / f"{slug}-iteration-0-input.md"
        create_initial_packet(input_packet, feature, goal, spec_path, plan_path)

    print(f"Project root: {project_root}")
    print(f"Artifacts dir: {artifacts_dir}")
    print(f"Initial packet: {input_packet}")

    final_status: dict[str, Any] | None = None
    for iteration in range(1, args.max_iterations + 1):
        result_packet = artifacts_dir / f"{slug}-iteration-{iteration}-result.md"
        status_json = artifacts_dir / f"{slug}-iteration-{iteration}-status.json"
        stdout_log = artifacts_dir / f"{slug}-iteration-{iteration}-stdout.log"
        stderr_log = artifacts_dir / f"{slug}-iteration-{iteration}-stderr.log"
        title = f"Ralph Loop: {feature} iteration {iteration}"
        prompt = build_attempt_prompt(feature, iteration, input_packet, result_packet, status_json)
        command = build_command(args, project_root, title, input_packet, prompt)

        print(f"\nIteration {iteration}: starting fresh opencode session")
        print("Command: " + " ".join(json.dumps(part) for part in command[:-1]) + " <prompt>")

        if args.dry_run:
            print("Dry run enabled; stopping before opencode run.")
            return 0

        try:
            completed = run_child(command, args.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            write_text(stdout_log, timeout_output(exc.stdout))
            write_text(stderr_log, timeout_output(exc.stderr))
            write_json(
                status_json,
                {
                    "status": "blocked",
                    "continue": False,
                    "summary": "Fresh opencode attempt timed out.",
                    "next_starting_gate": "Blocked",
                    "first_actionable_failure": f"Timeout after {args.timeout_seconds} seconds.",
                    "result_packet": str(result_packet),
                },
            )
            print(f"Iteration {iteration} timed out. Status: {status_json}")
            return 1

        write_text(stdout_log, completed.stdout)
        write_text(stderr_log, completed.stderr)

        if completed.returncode != 0:
            write_json(
                status_json,
                {
                    "status": "blocked",
                    "continue": False,
                    "summary": "Fresh opencode attempt exited with a non-zero status.",
                    "next_starting_gate": "Blocked",
                    "first_actionable_failure": f"opencode exit code {completed.returncode}. See stderr log.",
                    "result_packet": str(result_packet),
                },
            )
            print(f"Iteration {iteration} failed to run. Status: {status_json}")
            return completed.returncode or 1

        status = read_status(status_json)
        if status is None:
            write_json(
                status_json,
                {
                    "status": "blocked",
                    "continue": False,
                    "summary": "Attempt session did not write a valid status JSON.",
                    "next_starting_gate": "Blocked",
                    "first_actionable_failure": "Missing or invalid attempt status JSON.",
                    "result_packet": str(result_packet),
                },
            )
            print(f"Iteration {iteration} did not produce valid status JSON: {status_json}")
            return 1

        final_status = status
        status_name = str(status.get("status", "unknown"))
        summary = str(status.get("summary", ""))
        print(f"Iteration {iteration} status: {status_name}")
        if summary:
            print(f"Summary: {summary}")

        if not should_continue(status, iteration, args.max_iterations):
            print(f"Stopping after iteration {iteration}. Result packet: {result_packet}")
            break

        input_packet = result_packet

    if final_status is None:
        return 1

    final_status_name = str(final_status.get("status", "")).strip().lower().replace(" ", "_")
    return 0 if final_status_name in {"complete", "complete_with_residual_risk"} else 1


if __name__ == "__main__":
    sys.exit(main())
