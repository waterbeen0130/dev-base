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
TEMPLATES_DIR = DEV_BASE / "templates"

GM_SUBDIRS = ("requests", "worktrees", "plans")
PUBLISHING_ROOT_DIRS = ("css", "js", "img", "extracted")

# Required keywords in deployed CLAUDE.md — new workflow enforcement (DOD-005).
# init-project.py verifies these after copy, fails with exit 1 if any missing.
CLAUDE_MD_REQUIRED_KEYWORDS = (
    "공통 영역",       # common area prefix-less classes
    "페이지 전용",     # page-scoped classes
    "시멘틱 마크업",   # semantic HTML markup
    "4-space",         # 4-space indentation
    "flexbox",         # flexbox-only layout
    "hex",             # hex color rule
    "em",              # em letter-spacing rule
    "figma-png-download",  # new workflow tools
    "asset-copy",
    "pm-verify",
    "select-ai",
    "POLICY-1",        # must be present as forbidden keyword
)


def verify_claude_md(project: Path) -> list[str]:
    """Return list of missing required keywords in deployed CLAUDE.md."""
    target = project / "CLAUDE.md"
    if not target.exists():
        return ["CLAUDE.md (file missing)"]
    content = target.read_text(encoding="utf-8")
    return [kw for kw in CLAUDE_MD_REQUIRED_KEYWORDS if kw not in content]


def init_publishing_layout(project: Path, created: list[str], skipped: list[str]) -> None:
    """Create css/, js/, img/, extracted/ + copy reset.css/font.css/font/ from templates."""
    for d in PUBLISHING_ROOT_DIRS:
        target = project / d
        if target.exists():
            skipped.append(f"{d}/")
        else:
            target.mkdir(parents=True, exist_ok=True)
            created.append(f"{d}/")

    css_src = TEMPLATES_DIR / "css"
    css_dst = project / "css"
    if css_src.exists():
        for f in ("reset.css", "font.css"):
            src = css_src / f
            dst = css_dst / f
            if dst.exists():
                skipped.append(f"css/{f}")
            elif src.exists():
                shutil.copy2(src, dst)
                created.append(f"css/{f}")

        font_src = css_src / "font"
        font_dst = css_dst / "font"
        if font_src.is_dir() and not font_dst.exists():
            shutil.copytree(font_src, font_dst)
            created.append("css/font/ (%d files)" % len(list(font_dst.iterdir())))

    # common.css skeleton (only if not present)
    common_dst = css_dst / "common.css"
    if not common_dst.exists():
        common_dst.write_text(COMMON_CSS_SKELETON, encoding="utf-8")
        created.append("css/common.css (skeleton)")


COMMON_CSS_SKELETON = """@charset "utf-8";
@import url("reset.css");
@import url("font.css");

:root {
\t--width:1480px;
\t--padding:20px;
\t--header_h:100px;
\t--point-color-1:#438eca;
}

html, body {height:auto; font-size:16px;}
body {font-family:'Pretendard', sans-serif; color:#212121; background:#fff; word-break:keep-all;}
a {color:inherit; text-decoration:none;}
.cont {width:100%; max-width:var(--width); margin:0 auto; padding:0 var(--padding);}
.img_area {display:inline-block; overflow:hidden; line-height:0;}
.img_area img {display:block; max-width:100%;}

[data-delay] {position:relative; transition:all 1s ease; opacity:0;}
[data-direction="left"] {left:-40px;}
[data-direction="right"] {right:-40px;}
[data-direction="top"] {top:-40px;}
[data-direction="bottom"] {bottom:-40px;}
.section_on [data-delay] {opacity:1;}
.section_on [data-direction="left"] {left:0;}
.section_on [data-direction="right"] {right:0;}
.section_on [data-direction="top"] {top:0;}
.section_on [data-direction="bottom"] {bottom:0;}
"""


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

    # 3. Ensure .gran-maestro/ skeleton
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

    # 4. Publishing: standard layout + config/agents templates
    if publishing:
        init_publishing_layout(project, created, skipped)

        pub_tpl = RULES_DIR / "templates" / "publishing"
        if not pub_tpl.is_dir():
            print(
                f"Error: publishing 템플릿 복사 실패: 템플릿 디렉토리 없음 ({pub_tpl})",
                file=sys.stderr,
            )
            sys.exit(1)

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
            shutil.copy2(src, dst)
            created.append(f".gran-maestro/{f}")

    if created:
        print(f"Created: {', '.join(created)}")
    if skipped:
        print(f"Skipped (already present): {', '.join(skipped)}")
    if not created and not skipped:
        print("Already initialized")

    # 5. Verify CLAUDE.md keywords (DOD-005 — new workflow enforcement)
    missing = verify_claude_md(project)
    if missing:
        print(
            f"Error: CLAUDE.md 누락 키워드: {', '.join(missing)} — init-project.py 템플릿 갱신 필요",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"OK: CLAUDE.md 새 워크플로우 키워드 {len(CLAUDE_MD_REQUIRED_KEYWORDS)}개 모두 포함")


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
