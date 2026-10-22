"""Check tracked distribution files for obvious private inputs and credentials.

This is a guard, not a substitute for reviewing everything staged for publication.
"""
from pathlib import Path
import argparse
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"gm_framework", "tests", "docs", "roll20", "tools", ".github"}
ROOT_FILES = {"README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE", "pyproject.toml", ".gitignore", ".gitattributes"}


def inspect_text(label, text, terms):
    patterns = [r"gh[pousr]_[A-Za-z0-9]{30,}", r"sk-[A-Za-z0-9_-]{32,}",
                r"(?i)[A-Z]:[/\\]Users[/\\][^\s/\\]+[/\\]", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    problems = []
    if any(re.search(p, text) for p in patterns):
        problems.append(f"Possible credential/private path: {label}")
    if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I) for term in terms):
        # Do not repeat sensitive names in logs or commit them as a public denylist.
        problems.append(f"Private-term match: {label}")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-terms", type=Path, help="External UTF-8 file, one private name/phrase per line; never commit it")
    parser.add_argument("--staged", action="store_true", help="Inspect complete index contents instead of working files")
    parser.add_argument("--history", action="store_true", help="Also inspect all locally reachable historical blobs and paths")
    args = parser.parse_args(argv)
    terms = [s.strip() for s in args.private_terms.read_text(encoding="utf-8-sig").splitlines() if s.strip()] if args.private_terms else []
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
    if result.returncode:
        print("Run after git init and staging the intended distribution", file=sys.stderr)
        return 2
    paths = [Path(p) for p in result.stdout.decode("utf-8").split("\0") if p]
    if not paths:
        print("No tracked files to check", file=sys.stderr)
        return 2
    problems = []
    for relative in paths:
        problems.extend(inspect_text(str(relative), relative.as_posix(), terms))
        if relative.parts[0] not in ALLOWED and str(relative) not in ROOT_FILES:
            problems.append(f"Unexpected distribution path: {relative}")
        if any(p.lower() in {"receipts", "private", "campaigns", "rejected", "node_modules", ".venv"} for p in relative.parts):
            problems.append(f"Private/generated directory tracked: {relative}")
        path = ROOT / relative
        if path.is_symlink():
            problems.append(f"Symlink in distribution: {relative}")
            continue
        try:
            if args.staged:
                text = subprocess.check_output(["git", "show", ":" + relative.as_posix()], cwd=ROOT).decode("utf-8")
            else:
                text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            problems.append(f"Unexpected missing/binary file: {relative}")
            continue
        problems.extend(inspect_text(str(relative), text, terms))
    historical = 0
    if args.history:
        objects = subprocess.check_output(["git", "rev-list", "--objects", "--all"], cwd=ROOT).decode("utf-8").splitlines()
        for row in objects:
            sha, _, name = row.partition(" ")
            if not name:
                continue
            problems.extend(inspect_text(sha + " path", name, terms))
            kind = subprocess.check_output(["git", "cat-file", "-t", sha], cwd=ROOT).strip()
            if kind != b"blob":
                continue
            historical += 1
            body = subprocess.check_output(["git", "cat-file", "blob", sha], cwd=ROOT)
            try:
                text = body.decode("utf-8")
            except UnicodeError:
                problems.append(f"Unreviewed historical binary: {sha}")
                continue
            problems.extend(inspect_text(sha + ":" + name, text, terms))
    for problem in problems:
        print(problem)
    if not problems:
        print(f"Checked {len(paths)} tracked text files and {historical} historical blobs: no detected distribution violations. Manual publication review still required.")
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
