#!/usr/bin/env python3
"""Self-check for install_plugins.py version drift detection and install classification.

Run: py -3 scripts/test_install_plugins.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

INSTALLER = Path(__file__).resolve().parent / "install_plugins.py"
PAYLOAD = Path(__file__).resolve().parents[1] / "assets" / "Plugins" / "UnrealMCPToolsets"
DESCRIPTOR = PAYLOAD / "UnrealMCPToolsets.uplugin"


def payload_version() -> int:
    return int(json.loads(DESCRIPTOR.read_text(encoding="utf-8-sig"))["Version"])


def run(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INSTALLER), *args],
        cwd=project_root,
        capture_output=True,
        text=True,
    )


def make_project(root: Path, installed_version: int | None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "Fixture.uproject").write_text("{}", encoding="utf-8")
    if installed_version is not None:
        descriptor = root / "Plugins" / "UnrealMCPToolsets" / "UnrealMCPToolsets.uplugin"
        descriptor.parent.mkdir(parents=True, exist_ok=True)
        descriptor.write_text(
            json.dumps({"FileVersion": 3, "Version": installed_version, "VersionName": "fixture"}),
            encoding="utf-8",
        )
    return root


def advisory(result: subprocess.CompletedProcess[str]) -> str:
    assert result.returncode == 0, result.stderr
    if not result.stdout.strip():
        return ""
    payload = json.loads(result.stdout)
    return payload["hookSpecificOutput"]["additionalContext"]


def main() -> int:
    current = payload_version()

    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)

        # A non-Unreal directory must stay completely silent.
        plain = temp_root / "plain"
        plain.mkdir()
        assert advisory(run(plain, "--check")) == ""

        # Bundled but not installed.
        assert "not installed" in advisory(run(make_project(temp_root / "absent", None), "--check"))

        # Same version: silent even though the fixture bytes differ from the payload.
        same = make_project(temp_root / "same", current)
        assert advisory(run(same, "--check")) == ""

        # Older install: advise the update.
        older = make_project(temp_root / "older", current - 1)
        assert "now bundles" in advisory(run(older, "--check"))

        # Newer install: warn instead of advising an overwrite, and block the downgrade.
        newer = make_project(temp_root / "newer", current + 1)
        assert "newer than the bundled" in advisory(run(newer, "--check"))
        blocked = run(newer, "--dry-run")
        assert blocked.returncode == 2, blocked.stdout
        assert "DOWNGRADE" in blocked.stdout
        assert "would downgrade" in blocked.stderr

        # Fresh install, then a second run reports it as unchanged.
        fresh = make_project(temp_root / "fresh", None)
        installed = run(fresh, "--project-root", str(fresh))
        assert installed.returncode == 0, installed.stderr
        assert (fresh / "Plugins" / "UnrealMCPToolsets" / "UnrealMCPToolsets.uplugin").is_file()
        assert "UNCHANGED" in run(fresh, "--project-root", str(fresh)).stdout
        assert advisory(run(fresh, "--check")) == ""

    print("install_plugins self-check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
