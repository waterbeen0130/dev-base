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

GM_SUBDIRS = ("requests", "worktrees", "plans")

def init_project(project_path: str, project_type: str = "basic", publishing: bool = False):
    project = Path(project_path).resolve()
    if not project.is_dir():
        print(f"Error: {project} is not a directory", file=sys.stderr)
        sys.exit(1)

    created = []
    skipped = []

    # 1. Copy CLAUDE.md
    src_claude = RULES_DIR / "CLAUDE.md"
    dst_claude = project / "CLAUDE.md"
    if dst_claude.exists():
        skipped.append("CLAUDE.md")
    elif src_claude.exists():
        shutil.copy2(src_claude, dst_claude)
        created.append("CLAUDE.md")

    # 2. Create .claude/settings.local.json
    dst_settings_dir = project / ".claude"
    dst_settings = dst_settings_dir / "settings.local.json"
    src_settings = RULES_DIR / "claude-settings-template.json"
    if dst_settings.exists():
        skipped.append(".claude/settings.local.json")
    elif src_settings.exists():
        dst_settings_dir.mkdir(exist_ok=True)
        tpl = json.loads(src_settings.read_text(encoding="utf-8"))
        tpl.pop("_comment", None)
        dst_settings.write_text(json.dumps(tpl, indent=2, ensure_ascii=False), encoding="utf-8")
        created.append(".claude/settings.local.json")

    # 3. Ensure .gran-maestro/ skeleton (.gran-maestro/ + requests/ + worktrees/ + plans/)
    gm_dir = project / ".gran-maestro"
    if gm_dir.exists():
        skipped.append(".gran-maestro/")
    else:
        gm_dir.mkdir(parents=True, exist_ok=True)
        created.append(".gran-maestro/")
    for sub in GM_SUBDIRS:
        sub_dir = gm_dir / sub
        if sub_dir.exists():
            skipped.append(f".gran-maestro/{sub}/")
        else:
            sub_dir.mkdir(parents=True, exist_ok=True)
            created.append(f".gran-maestro/{sub}/")

    # 4. Copy publishing templates if --publishing
    if publishing:
        pub_tpl = RULES_DIR / "templates" / "publishing"
        if not pub_tpl.is_dir():
            print(
                f"Error: publishing 템플릿 복사 실패: 템플릿 디렉토리 없음 ({pub_tpl})",
                file=sys.stderr,
            )
            sys.exit(1)

        publishing_copied = 0
        for f in ("config.json", "agents.json"):
            src = pub_tpl / f
            dst = gm_dir / f
            if dst.exists():
                skipped.append(f".gran-maestro/{f}")
                continue
            if not src.exists():
                print(
                    f"Error: publishing 템플릿 복사 실패: 소스 파일 없음 ({src})",
                    file=sys.stderr,
                )
                sys.exit(1)
            try:
                shutil.copy2(src, dst)
            except OSError as exc:
                print(
                    f"Error: publishing 템플릿 복사 실패: {src} -> {dst} ({exc})",
                    file=sys.stderr,
                )
                sys.exit(1)
            created.append(f".gran-maestro/{f}")
            publishing_copied += 1

        if publishing_copied == 0 and not any(
            item.startswith(".gran-maestro/") and item.endswith(".json")
            for item in skipped
        ):
            print(
                "Error: publishing 템플릿 복사 실패: 복사 대상 없음",
                file=sys.stderr,
            )
            sys.exit(1)

    if created:
        print(f"Created: {', '.join(created)}")
    if skipped:
        print(f"Skipped (already present): {', '.join(skipped)}")
    if not created and not skipped:
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
