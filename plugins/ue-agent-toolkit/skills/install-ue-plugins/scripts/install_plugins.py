#!/usr/bin/env python3
"""Install bundled Unreal Engine plugins into an Unreal project."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


IGNORED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".vs",
        "Binaries",
        "DerivedDataCache",
        "Intermediate",
        "Saved",
    }
)


@dataclass(frozen=True)
class PluginAction:
    name: str
    source: Path
    destination: Path
    action: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install the Unreal Engine plugins bundled with UE Agent Toolkit into "
            "<project>/Plugins."
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
        help="Preview changes without installing, replacing, or backing up files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Replace conflicting plugin directories after backing them up. "
            "Use only with explicit user approval."
        ),
    )
    return parser.parse_args()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def validate_project_root(project_root: Path) -> Path:
    resolved = project_root.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"Project root does not exist or is not a directory: {resolved}")

    project_files = sorted(resolved.glob("*.uproject"))
    if not project_files:
        raise ValueError(f"No .uproject file found directly under project root: {resolved}")

    return resolved


def ensure_within_project(project_root: Path, path: Path, label: str) -> None:
    project_text = os.path.normcase(str(project_root.resolve()))
    path_text = os.path.normcase(str(path.resolve()))
    if os.path.commonpath((project_text, path_text)) != project_text:
        raise ValueError(f"{label} escapes the project root: {path}")


def validate_plugin_sources(payload_root: Path) -> list[tuple[str, Path]]:
    if not payload_root.is_dir():
        raise ValueError(f"Bundled plugin payload directory is missing: {payload_root}")

    sources: list[tuple[str, Path]] = []
    for entry in sorted(payload_root.iterdir(), key=lambda item: item.name.casefold()):
        if not entry.is_dir() or entry.name.startswith("."):
            raise ValueError(f"Unexpected entry in bundled Plugins directory: {entry}")

        descriptor = entry / f"{entry.name}.uplugin"
        if not descriptor.is_file():
            raise ValueError(
                f"Bundled plugin descriptor does not match its directory name: {descriptor}"
            )

        for path in entry.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Bundled plugin payload cannot contain symlinks: {path}")
            if path.is_dir() and path.name in IGNORED_DIRECTORY_NAMES:
                raise ValueError(f"Bundled plugin payload contains generated directory: {path}")

        sources.append((entry.name, entry.resolve()))

    if not sources:
        raise ValueError(f"No bundled Unreal plugins found under: {payload_root}")

    return sources


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, tuple[int, str]]:
    if root.is_symlink():
        raise ValueError(f"Plugin directory cannot be a symlink: {root}")

    result: dict[str, tuple[int, str]] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRECTORY_NAMES for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Plugin directory cannot contain symlinks: {path}")
        if path.is_file():
            result[relative.as_posix()] = (path.stat().st_size, hash_file(path))
    return result


def ensure_no_symlinks(root: Path) -> None:
    if root.is_symlink():
        raise ValueError(f"Plugin directory cannot be a symlink: {root}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Plugin directory cannot contain symlinks: {path}")


def classify(source: Path, destination: Path, force: bool) -> str:
    if not destination.exists():
        return "install"
    if not destination.is_dir():
        raise ValueError(f"Plugin destination exists but is not a directory: {destination}")
    ensure_no_symlinks(destination)
    if inventory(source) == inventory(destination):
        return "unchanged"
    return "replace" if force else "conflict"


def backup_root(project_root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return (
        project_root
        / ".ue-agent-toolkit"
        / "backups"
        / "unreal-plugins"
        / timestamp
    )


def sync_payload(source: Path, destination: Path) -> None:
    source_inventory = inventory(source)
    destination_inventory = inventory(destination)

    for relative in sorted(source_inventory):
        source_file = source / Path(relative)
        destination_file = destination / Path(relative)
        if destination_file.exists() and not destination_file.is_file():
            raise ValueError(
                f"Cannot replace non-file plugin entry with a file: {destination_file}"
            )
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination_file)

    extra_files = sorted(
        set(destination_inventory).difference(source_inventory), reverse=True
    )
    for relative in extra_files:
        extra_file = destination / Path(relative)
        extra_file.unlink()

    directories = sorted(
        (path for path in destination.rglob("*") if path.is_dir()),
        key=lambda path: len(path.relative_to(destination).parts),
        reverse=True,
    )
    for directory in directories:
        relative = directory.relative_to(destination)
        if any(part in IGNORED_DIRECTORY_NAMES for part in relative.parts):
            continue
        try:
            directory.rmdir()
        except OSError:
            pass


def install_plugin(
    action: PluginAction,
    project_root: Path,
    run_backup_root: Path | None,
) -> Path | None:
    backup_path: Path | None = None

    action.destination.parent.mkdir(parents=True, exist_ok=True)
    if action.action == "install":
        shutil.copytree(action.source, action.destination)
    elif action.action == "replace":
        if run_backup_root is None:
            raise ValueError("Replacement requires a backup destination")
        backup_path = run_backup_root / action.name
        ensure_within_project(project_root, backup_path, "Backup directory")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if backup_path.exists():
            raise ValueError(f"Backup destination already exists: {backup_path}")
        shutil.copytree(action.destination, backup_path)
        try:
            sync_payload(action.source, action.destination)
        except Exception as exc:
            raise OSError(
                f"Plugin update failed after creating backup {backup_path}: {exc}"
            ) from exc

    if inventory(action.source) != inventory(action.destination):
        backup_note = f" Backup: {backup_path}" if backup_path is not None else ""
        raise ValueError(
            f"Installed plugin verification failed: {action.destination}.{backup_note}"
        )
    return backup_path


def main() -> int:
    args = parse_args()

    try:
        project_root = validate_project_root(args.project_root)
        payload_root = skill_root() / "assets" / "Plugins"
        plugin_sources = validate_plugin_sources(payload_root)

        actions: list[PluginAction] = []
        for name, source in plugin_sources:
            destination = project_root / "Plugins" / name
            ensure_within_project(project_root, destination, "Plugin destination")
            actions.append(
                PluginAction(
                    name=name,
                    source=source,
                    destination=destination,
                    action=classify(source, destination, args.force),
                )
            )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    conflicts = [action.name for action in actions if action.action == "conflict"]
    for action in actions:
        if args.dry_run and action.action in {"install", "replace"}:
            print(f"WOULD {action.action.upper()}: {action.name} -> {action.destination}")
        elif action.action in {"unchanged", "conflict"}:
            print(f"{action.action.upper()}: {action.name} -> {action.destination}")

    if conflicts:
        print(
            "ERROR: Conflicting Unreal plugins were not changed. Re-run with --force only "
            "after explicit approval: " + ", ".join(conflicts),
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        return 0

    replacements = [action for action in actions if action.action == "replace"]
    run_backup_root = backup_root(project_root) if replacements else None

    try:
        for action in actions:
            if action.action not in {"install", "replace"}:
                continue
            backup_path = install_plugin(action, project_root, run_backup_root)
            completed_verb = "INSTALLED" if action.action == "install" else "REPLACED"
            print(f"{completed_verb}: {action.name} -> {action.destination}")
            if backup_path is not None:
                print(f"BACKUP: {action.name} -> {backup_path}")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
