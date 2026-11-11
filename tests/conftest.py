"""Shared paths and helpers for the tests."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/orchi"
SKILLS = PLUGIN / "skills"
CORE = SKILLS / "orchi-core"
REFERENCES = CORE / "references"
SCRIPTS = CORE / "scripts"
ASSETS = CORE / "assets"
AGENTS = PLUGIN / "agents"
GIT_ENV = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com", "GIT_COMMITTER_NAME": "Test",
           "GIT_COMMITTER_EMAIL": "test@example.com", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, env={**os.environ, **GIT_ENV}, check=True, capture_output=True,
                          text=True).stdout.strip()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def tree(folder: Path) -> dict:
    return {path.relative_to(folder).as_posix(): path.read_text() for path in sorted(folder.rglob("*")) if path.is_file()}
