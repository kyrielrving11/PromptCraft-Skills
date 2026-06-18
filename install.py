"""PromptCraft installer — copies or symlinks the 4 skill directories into
a target AI coding agent's skills directory.

Usage:
  python install.py                     # auto-detect target, copy
  python install.py --target ~/skills   # explicit target
  python install.py --symlink           # symlink instead of copy (dev mode)
  python install.py --init-global       # also create ~/.promptcraft/ dirs
  python install.py --list              # dry-run: show what would happen
  python install.py --force             # overwrite existing without prompt
  python install.py --uninstall         # remove installed skills
  python install.py --check-update      # compare installed version vs repo
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

VERSION = "v2.1"
VERSION_FILE = ".promptcraft-version"

SKILL_NAMES = [
    "prompt-craft",
    "prompt-memory",
    "prompt-techniques",
    "prompt-review",
]

# ── target auto-detection ──────────────────────────────────────────────────

KNOWN_TARGETS = [
    Path.home() / ".claude" / "skills",       # Claude Code
    Path.home() / ".codex" / "skills",         # Codex
    Path.home() / ".codebuddy" / "skills",     # CodeBuddy
]

GLOBAL_PROMPTCRAFT = Path.home() / ".promptcraft"


def _source_dir() -> Path:
    """Directory containing this installer (repo root)."""
    return Path(__file__).resolve().parent


def _skills_source() -> Path:
    return _source_dir() / "skills"


def _detect_target() -> Path | None:
    """Return the first existing skills directory from KNOWN_TARGETS."""
    for p in KNOWN_TARGETS:
        if p.exists() and p.is_dir():
            return p
    return None


# ── file operations ────────────────────────────────────────────────────────

def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _symlink_tree(src: Path, dst: Path) -> None:
    """Create a directory symlink. On Windows this may require admin;
    fall back to copy with a warning."""
    if dst.exists():
        if dst.is_symlink():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    try:
        dst.symlink_to(src.resolve(), target_is_directory=True)
    except OSError:
        print(f"  [WARN] Symlink failed (may need admin on Windows). Falling back to copy.")
        _copy_tree(src, dst)


def _remove_tree(path: Path, name: str) -> bool:
    """Remove a directory. Returns True if removed, False if not found."""
    if not path.exists():
        return False
    shutil.rmtree(path)
    return True


# ── version tracking ───────────────────────────────────────────────────────

def _write_version(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    version_path = target / VERSION_FILE
    payload = {
        "version": VERSION,
        "installed_at": None,  # filled by shell, not critical
        "skills": SKILL_NAMES,
    }
    version_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _read_version(target: Path) -> str | None:
    version_path = target / VERSION_FILE
    if not version_path.exists():
        return None
    try:
        data = json.loads(version_path.read_text(encoding="utf-8"))
        return data.get("version")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _check_update(target: Path) -> None:
    installed = _read_version(target)
    if installed is None:
        print(f"No PromptCraft installation detected in {target}")
        print(f"Run: python install.py")
        return
    if installed == VERSION:
        print(f"PromptCraft {VERSION} is up to date in {target}")
    else:
        print(f"Installed: {installed}  →  Available: {VERSION}")
        print(f"Run: python install.py --force  to upgrade")


# ── main commands ──────────────────────────────────────────────────────────

def cmd_list(args) -> None:
    target = Path(args.target) if args.target else _detect_target()
    if target is None:
        print("No skills directory detected. Specify one with --target.")
        targets_fmt = "\n".join(f"  {p}" for p in KNOWN_TARGETS)
        print(f"Known targets:\n{targets_fmt}")
        sys.exit(1)

    source = _skills_source()
    mode = "symlink" if args.symlink else "copy"

    print(f"Source : {source}")
    print(f"Target : {target}  [{mode} mode]")
    print(f"Version: {VERSION}")
    print()

    for name in SKILL_NAMES:
        src = source / name
        dst = target / name
        status = "EXISTS (will overwrite)" if dst.exists() else "OK"
        print(f"  {name:20s} → {dst}  [{status}]")

    if args.init_global:
        print(f"\n  (--init-global) → {GLOBAL_PROMPTCRAFT}/")


def cmd_install(args) -> None:
    target = Path(args.target) if args.target else _detect_target()
    if target is None:
        print("Error: No skills directory detected. Specify one with --target.")
        targets_fmt = "\n".join(f"  {p}" for p in KNOWN_TARGETS)
        print(f"Known targets:\n{targets_fmt}")
        sys.exit(1)

    source = _skills_source()
    if not source.exists():
        print(f"Error: skills/ directory not found at {source}")
        sys.exit(1)

    operation = _symlink_tree if args.symlink else _copy_tree
    mode = "symlink" if args.symlink else "copy"

    print(f"PromptCraft {VERSION}  →  {target}  [{mode}]")
    print()

    conflicts = []
    for name in SKILL_NAMES:
        dst = target / name
        if dst.exists():
            conflicts.append(name)

    if conflicts and not args.force:
        names = ", ".join(conflicts)
        print(f"Already installed: {names}")
        print("Use --force to overwrite, or --uninstall first.")
        sys.exit(1)

    for name in SKILL_NAMES:
        src = source / name
        dst = target / name
        if not src.is_dir():
            print(f"  [SKIP] {name} — source not found at {src}")
            continue
        operation(src, dst)
        print(f"  {name:20s} → {dst}")

    _write_version(target)

    if args.init_global:
        GLOBAL_PROMPTCRAFT.mkdir(parents=True, exist_ok=True)
        (GLOBAL_PROMPTCRAFT / "prompts").mkdir(exist_ok=True)
        print(f"\n  Global vault initialized at {GLOBAL_PROMPTCRAFT}")

    print(f"\nDone. PromptCraft {VERSION} installed.")


def cmd_uninstall(args) -> None:
    target = Path(args.target) if args.target else _detect_target()
    if target is None:
        print("Error: No skills directory detected. Specify one with --target.")
        sys.exit(1)

    print(f"Uninstalling PromptCraft from {target}")
    print()

    removed = 0
    for name in SKILL_NAMES:
        dst = target / name
        if _remove_tree(dst, name):
            print(f"  [REMOVED] {name}")
            removed += 1
        else:
            print(f"  [NOT FOUND] {name}")

    # Remove version file
    version_path = target / VERSION_FILE
    if version_path.exists():
        version_path.unlink()

    if removed == 0:
        print("\nNothing to uninstall.")
    else:
        print(f"\n{removed} skill(s) removed. Vault files (.promptcraft/) are untouched.")


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"PromptCraft {VERSION} installer.",
    )
    parser.add_argument("--target", type=str, help="Target skills directory.")
    parser.add_argument("--symlink", action="store_true",
                        help="Symlink instead of copy (dev mode — edit source, target updates live).")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing skill directories without prompt.")
    parser.add_argument("--init-global", action="store_true",
                        help=f"Also create {GLOBAL_PROMPTCRAFT}/ directory structure.")
    parser.add_argument("--list", action="store_true",
                        help="Dry-run: show what would be installed and where.")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove installed PromptCraft skill directories.")
    parser.add_argument("--check-update", action="store_true",
                        help="Check if installed version is up to date.")
    args = parser.parse_args()

    if args.list:
        cmd_list(args)
    elif args.uninstall:
        cmd_uninstall(args)
    elif args.check_update:
        target = Path(args.target) if args.target else _detect_target()
        if target is None:
            print("No skills directory detected. Specify one with --target.")
            sys.exit(1)
        _check_update(target)
    else:
        cmd_install(args)


if __name__ == "__main__":
    main()
