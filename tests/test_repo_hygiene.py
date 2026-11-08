"""Guards that keep private Bible modules out of the public repository."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Only these public sample modules may be tracked in the public repository.
ALLOWED_MODULE_FILES = {
    "data/KJV1611.SQLite3",
    "data/KJV+.SQLite3",
}


def _tracked_files() -> list[str]:
    try:
        output = subprocess.check_output(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "ls-files",
                "-z",
                "--full-name",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("git is not available; skipping repository hygiene checks")
    return [path for path in output.split("\0") if path]


def test_no_private_module_files_are_tracked() -> None:
    tracked = _tracked_files()
    tracked_modules = [
        path
        for path in tracked
        if path.lower().endswith((".sqlite3", ".bundle.zip"))
    ]
    unexpected = [
        path for path in tracked_modules if path not in ALLOWED_MODULE_FILES
    ]
    assert not unexpected, (
        "Private or unreviewed module files are tracked in the public repository: "
        + ", ".join(sorted(unexpected))
    )


def test_private_modules_container_keeps_its_readme() -> None:
    readme = REPO_ROOT / "private_modules/README.md"
    assert readme.is_file(), "private_modules/README.md is the tracked corpus guide"


def test_no_private_submodule_is_declared() -> None:
    gitmodules = REPO_ROOT / ".gitmodules"
    if not gitmodules.exists():
        return
    text = gitmodules.read_text(encoding="utf-8", errors="replace")
    assert "private_modules" not in text, (
        "Do not add the private module corpus as a public submodule"
    )
