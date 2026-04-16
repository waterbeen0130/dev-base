#!/usr/bin/env python3
"""
dev-base project initializer
SessionStart hook calls this automatically when CLAUDE.md is missing.
Usage: python3 init-project.py <project_path> [--type basic|landing] [--publishing]
"""
import sys
import shutil
import json
from pathlib import Path

DEV_BASE = Path(__file__).resolve().parent.parent
RULES_DIR = DEV_BASE / "rules"

def init_project(project_path: str, project_type: str = "basic", publishing: bool = False):
    project = Path(project_path).resolve()
    if not project.is_dir():
        print(f"Error: {project} is not a directory", file=sys.stderr)
        sys.exit(1)

    changes = []

    # 1. Copy CLAUDE.md
    src_claude = RULES_DIR / "CLAUDE.md"
    dst_claude = project / "CLAUDE.md"
    if not dst_claude.exists() and src_claude.exists():
        shutil.copy2(src_claude, dst_claude)
        changes.append("CLAUDE.md")

    # 2. Create .claude/settings.local.json
    dst_settings_dir = project / ".claude"
    dst_settings = dst_settings_dir / "settings.local.json"
    src_settings = RULES_DIR / "claude-settings-template.json"
    if not dst_settings.exists() and src_settings.exists():
        dst_settings_dir.mkdir(exist_ok=True)
        tpl = json.loads(src_settings.read_text(encoding="utf-8"))
        tpl.pop("_comment", None)
        dst_settings.write_text(json.dumps(tpl, indent=2, ensure_ascii=False), encoding="utf-8")
        changes.append(".claude/settings.local.json")

    # 3. Copy publishing templates if --publishing
    if publishing:
        pub_tpl = RULES_DIR / "templates" / "publishing"
        gm_dir = project / ".gran-maestro"
        if pub_tpl.is_dir() and gm_dir.is_dir():
            for f in ["config.json", "agents.json"]:
                src = pub_tpl / f
                dst = gm_dir / f
                if src.exists() and not dst.exists():
                    shutil.copy2(src, dst)
                    changes.append(f".gran-maestro/{f}")

    if changes:
        print(f"Initialized: {', '.join(changes)}")
    else:
        print("Already initialized")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: init-project.py <project_path> [--type basic|landing] [--publishing]", file=sys.stderr)
        sys.exit(1)

    project_path = args[0]
    project_type = "basic"
    publishing = False

    i = 1
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            project_type = args[i + 1]
            i += 2
        elif args[i] == "--publishing":
            publishing = True
            i += 1
        else:
            i += 1

    init_project(project_path, project_type, publishing)
