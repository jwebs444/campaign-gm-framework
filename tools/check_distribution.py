"""Check tracked distribution files for obvious private inputs and credentials.

This is a guard, not a substitute for reviewing everything staged for publication.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"gm_framework", "tests", "docs", "roll20", "tools", ".github"}
ROOT_FILES = {"README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE", "pyproject.toml", ".gitignore", ".gitattributes"}


def main():
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
    if result.returncode:
        print("Run after git init and staging the intended distribution", file=sys.stderr)
        return 2
    paths = [Path(p) for p in result.stdout.decode("utf-8").split("\0") if p]
    if not paths:
        print("No tracked files to check", file=sys.stderr)
        return 2
    problems = []
    patterns = [r"gh[pousr]_[A-Za-z0-9]{30,}", r"sk-[A-Za-z0-9_-]{32,}",
                r"(?i)[A-Z]:[/\\]Users[/\\][^\s/\\]+[/\\]", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    for relative in paths:
        if relative.parts[0] not in ALLOWED and str(relative) not in ROOT_FILES:
            problems.append(f"Unexpected distribution path: {relative}")
        if any(p.lower() in {"receipts", "private", "campaigns", "rejected", "node_modules", ".venv"} for p in relative.parts):
            problems.append(f"Private/generated directory tracked: {relative}")
        path = ROOT / relative
        if path.is_symlink():
            problems.append(f"Symlink in distribution: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            problems.append(f"Unexpected missing/binary file: {relative}")
            continue
        if any(re.search(p, text) for p in patterns):
            problems.append(f"Possible credential/private path: {relative}")
    for problem in problems:
        print(problem)
    if not problems:
        print(f"Checked {len(paths)} tracked text files: no unexpected paths or obvious credentials. Manual publication review still required.")
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
