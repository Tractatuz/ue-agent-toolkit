#!/usr/bin/env python3
"""Install UE Agent Toolkit custom agents into an Unreal project."""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
from pathlib import Path


AGENT_FILENAMES = (
    "ue-code-reader.toml",
    "ue-code-writer.toml",
    "ue-code-reviewer.toml",
    "ue-asset-scanner.toml",
    "ue-asset-editor.toml",
    "ue-tester.toml",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install the UE Agent Toolkit custom-agent TOML files into "
            "<project>/.codex/agents."
        )
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Unreal project directory containing a .uproject file (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without creating or replacing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace conflicting agent files. Use only with explicit user approval.",
    )
    return parser.parse_args()


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def validate_project_root(project_root: Path) -> Path:
    resolved = project_root.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"Project root does not exist or is not a directory: {resolved}")

    project_files = sorted(resolved.glob("*.uproject"))
    if not project_files:
        raise ValueError(f"No .uproject file found directly under project root: {resolved}")

    return resolved


def validate_destination(project_root: Path, destination: Path) -> None:
    project_text = os.path.normcase(str(project_root))
    destination_text = os.path.normcase(str(destination.resolve()))
    if os.path.commonpath((project_text, destination_text)) != project_text:
        raise ValueError(f"Agent destination escapes the project root: {destination}")


def classify(source: Path, destination: Path, force: bool) -> str:
    if not destination.exists():
        return "install"
    if filecmp.cmp(source, destination, shallow=False):
        return "unchanged"
    if force:
        return "replace"
    return "conflict"


def main() -> int:
    args = parse_args()

    try:
        project_root = validate_project_root(args.project_root)
        source_dir = plugin_root() / "assets" / "agents"
        destination_dir = project_root / ".codex" / "agents"
        validate_destination(project_root, destination_dir)

        missing_sources = [
            filename for filename in AGENT_FILENAMES if not (source_dir / filename).is_file()
        ]
        if missing_sources:
            raise ValueError(
                "Plugin agent templates are missing: " + ", ".join(missing_sources)
            )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    actions = []
    for filename in AGENT_FILENAMES:
        source = source_dir / filename
        destination = destination_dir / filename
        actions.append((classify(source, destination, args.force), source, destination))

    conflicts = [destination.name for action, _, destination in actions if action == "conflict"]
    for action, _, destination in actions:
        prefix = "WOULD " if args.dry_run and action in {"install", "replace"} else ""
        print(f"{prefix}{action.upper()}: {destination}")

    if conflicts:
        print(
            "ERROR: Conflicting agent files were not changed. Re-run with --force only after "
            "explicit approval: " + ", ".join(conflicts),
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        return 0

    destination_dir.mkdir(parents=True, exist_ok=True)
    for action, source, destination in actions:
        if action in {"install", "replace"}:
            shutil.copy2(source, destination)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
