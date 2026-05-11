"""Phase 0 safety guard for the `.env.example` template.

Runs in CI and locally as a pre-commit check. It guarantees that:

1. `.env.example` exists at the repository root.
2. Every line that defines a variable assigns a *placeholder* value — never
   something that looks like a real credential.
3. The repository `.gitignore` excludes `.env` files.

Exits 0 on success, 1 with a descriptive message on failure. Uses the
standard library only so it runs without any project dependencies installed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Placeholder fragments that the .env.example legitimately uses. A value is
# considered safe if it is empty OR contains one of these fragments.
PLACEHOLDER_MARKERS = (
    "your-",
    "replace-with-",
    "http://localhost",
    "gpt-",
    "text-embedding-",
    "admin",
)

# Patterns that signal a real secret slipped into the template.
FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9_\-]{20,}")),
    ("Notion integration secret", re.compile(r"secret_[A-Za-z0-9]{40,}")),
    ("Generic 32+ char hex token", re.compile(r"\b[a-f0-9]{32,}\b")),
    (
        "JWT-shaped token",
        re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
    ),
)


def fail(message: str) -> None:
    print(f"verify_env_safety: FAIL — {message}", file=sys.stderr)
    sys.exit(1)


def check_env_example_exists() -> Path:
    path = REPO_ROOT / ".env.example"
    if not path.is_file():
        fail(".env.example is missing at the repository root")
    return path


def check_no_real_secrets(env_path: Path) -> None:
    text = env_path.read_text(encoding="utf-8")
    for label, pattern in FORBIDDEN_PATTERNS:
        match = pattern.search(text)
        if match:
            fail(f"{label} detected in .env.example: {match.group(0)[:12]}…")


def check_values_are_placeholders(env_path: Path) -> None:
    for lineno, raw in enumerate(env_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if not value:
            continue
        if any(marker in value for marker in PLACEHOLDER_MARKERS):
            continue
        fail(
            f".env.example line {lineno}: value for {key.strip()!r} does not look "
            "like a placeholder. Expected text containing one of "
            f"{PLACEHOLDER_MARKERS}, got: {value!r}"
        )


def check_gitignore_excludes_env() -> None:
    gitignore = REPO_ROOT / ".gitignore"
    if not gitignore.is_file():
        fail(".gitignore is missing")
    content = gitignore.read_text(encoding="utf-8")
    required_lines = {".env", ".env.*"}
    present = {ln.strip() for ln in content.splitlines() if ln.strip()}
    missing = required_lines - present
    if missing:
        fail(f".gitignore is missing required entries: {sorted(missing)}")
    if "!.env.example" not in content:
        fail(".gitignore should explicitly re-include !.env.example")


def main() -> None:
    env_path = check_env_example_exists()
    check_no_real_secrets(env_path)
    check_values_are_placeholders(env_path)
    check_gitignore_excludes_env()
    print("verify_env_safety: OK")


if __name__ == "__main__":
    main()
