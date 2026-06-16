#!/usr/bin/env python3
"""Accept preflight gate — runs a pipeline of deliverable/repo checks before accept.

Called by PreToolUse hook to mechanically block mst:accept if any wired gate
finds a blocking violation. Finds HTML/CSS files from the REQ worktree or linked
project directory and runs the gate pipeline against them.

Wired gates (AGI-004 verification hardening):
    1. validate-semantic.py     — HTML/CSS conventions (CRITICAL ≥1 blocks)
    2. check-output-boundary.py — raw extraction dumps mistaken for deliverable
    3. check-mixed-styles.py    — dropped per-segment colors (needs spec.json)
    4. check-deprecated-tools.py— resurrected/invoked deprecated tools (repo-level)
    5. check-workflow-order.py  — screenshot-first 2-pass order (needs ledger)
    6. check-extraction-provenance.py — known AI provider (needs ledger)

Each gate gracefully SKIPs when its inputs are absent, so a gate only blocks when
it has its inputs AND finds a real violation. The ledger gates (5,6) auto-activate
once the conversion pipeline writes .gran-maestro/workflow-ledger.json.

Usage:
    python3 tools/accept-preflight-verify.py --req REQ-NNN [--project-root /path]

Exit codes:
    0 = PASS (accept allowed)
    1 = FAIL (accept blocked — blocking violations found)
    2 = SKIP (no HTML/CSS found — non-publishing REQ, allow accept)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
VALIDATE_SCRIPT = TOOLS_DIR / "validate-semantic.py"

# Gate status constants
PASS = "pass"
BLOCK = "block"
SKIP = "skip"


def find_project_root() -> Path:
    candidate = Path.cwd()
    while candidate != candidate.parent:
        if (candidate / ".gran-maestro").is_dir():
            return candidate
        candidate = candidate.parent
    return Path.cwd()


def find_html_css_in_dir(search_dir: Path) -> tuple[Path | None, Path | None, str | None]:
    """Find HTML and CSS files in a directory. Returns (html, css, img_dir)."""
    html_candidates = []
    css_candidates = []

    # Look for page/ subdirectory first (common project structure)
    page_dir = search_dir / "page"
    if page_dir.is_dir():
        html_candidates.extend(page_dir.glob("*.html"))
    html_candidates.extend(search_dir.glob("*.html"))

    css_dir = search_dir / "css"
    if css_dir.is_dir():
        css_candidates.extend(css_dir.glob("common.css"))
        css_candidates.extend(css_dir.glob("*.css"))

    # Filter and prioritize
    html_file = None
    for h in html_candidates:
        if h.name == "index.html":
            html_file = h
            break
    if not html_file and html_candidates:
        html_file = html_candidates[0]

    css_file = None
    for c in css_candidates:
        if c.name == "common.css":
            css_file = c
            break
    if not css_file and css_candidates:
        css_file = css_candidates[0]

    img_dir = None
    for candidate_img in [search_dir / "img", search_dir / "images"]:
        if candidate_img.is_dir():
            img_dir = str(candidate_img)
            break

    return html_file, css_file, img_dir


def find_spec_files(search_dir: Path) -> list[Path]:
    """Return all *_spec.json (extracted/ first, then dir root)."""
    for base in (search_dir / "extracted", search_dir):
        if base.is_dir():
            specs = sorted(base.glob("*_spec.json"))
            if specs:
                return specs
    return []


def find_spec_file(search_dir: Path) -> Path | None:
    """Find a *_spec.json (extracted/ first, then dir root) for mixed-style check."""
    specs = find_spec_files(search_dir)
    return specs[0] if specs else None


def spec_has_font_metadata(spec_files: list[Path]) -> bool:
    """True if any spec.json carries real typography (a text_node with fontSize)."""
    for path in spec_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        nodes = data.get("text_nodes")
        if isinstance(nodes, list) and any(
            isinstance(n, dict) and n.get("fontSize") for n in nodes
        ):
            return True
    return False


def find_verify_report(output_dir: Path | None, project_root: Path) -> Path | None:
    """Locate a pm-verify evidence report (emitted via pm-verify --emit-report)."""
    candidates = []
    if output_dir:
        candidates.append(output_dir / ".gran-maestro" / "pm-verify-report.json")
        candidates.append(output_dir / "pm-verify-report.json")
    candidates.append(project_root / ".gran-maestro" / "pm-verify-report.json")
    for c in candidates:
        if c.is_file():
            return c
    # default location even if absent — verify-evidence-gate reports it as missing
    if output_dir:
        return output_dir / ".gran-maestro" / "pm-verify-report.json"
    return project_root / ".gran-maestro" / "pm-verify-report.json"


def find_ledger(project_root: Path, output_dir: Path | None) -> Path | None:
    """Find a workflow-ledger.json. Returns None (→ skip) when not present yet."""
    candidates = []
    if output_dir:
        candidates.append(output_dir / ".gran-maestro" / "workflow-ledger.json")
        candidates.append(output_dir / "workflow-ledger.json")
    candidates.append(project_root / ".gran-maestro" / "workflow-ledger.json")
    for c in candidates:
        if c.is_file():
            return c
    return None


def detect_profile(css_path: Path) -> str:
    """Detect landing/basic profile from CSS content."""
    try:
        css_text = css_path.read_text(encoding="utf-8", errors="ignore")
        if "[data-delay]" in css_text or "section_on" in css_text:
            return "landing"
    except Exception:
        pass
    return "basic"


def find_req_output_dir(project_root: Path, req_id: str) -> Path | None:
    """Find the output directory for a REQ from worktree metadata or request.json."""
    # Check worktree metadata
    worktree_dir = project_root / ".gran-maestro" / "worktrees"
    if worktree_dir.is_dir():
        for meta_file in worktree_dir.glob(f"{req_id}-*.meta.json"):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                wt_path = meta.get("path")
                if wt_path and Path(wt_path).is_dir():
                    return Path(wt_path)
            except Exception:
                continue

    # Check request.json for linked project path
    req_dir = project_root / ".gran-maestro" / "requests" / req_id
    req_json = req_dir / "request.json"
    if req_json.exists():
        try:
            req = json.loads(req_json.read_text(encoding="utf-8"))
            # Check tasks for output paths
            tasks = req.get("tasks", [])
            for task in tasks:
                if isinstance(task, dict):
                    output_dir = task.get("output_dir") or task.get("worktree_path")
                    if output_dir and Path(output_dir).is_dir():
                        return Path(output_dir)
            # Check spec description for project path hints
            for task in tasks:
                if isinstance(task, dict):
                    spec = task.get("spec", "")
                    if isinstance(spec, str):
                        # Look for paths like D:\위링\...\html or /mnt/d/위링/.../html
                        for match in re.finditer(r'[A-Za-z]:\\[^\s"]+|/mnt/[^\s"]+', spec):
                            candidate = Path(match.group(0).rstrip(".,;)"))
                            if candidate.is_dir():
                                return candidate
        except Exception:
            pass

    # Check agile objective for project path
    agile_dir = project_root / ".gran-maestro" / "agile"
    if agile_dir.is_dir():
        for agi_dir in sorted(agile_dir.iterdir(), reverse=True):
            obj_file = agi_dir / "objective" / "objective.md"
            if obj_file.exists():
                try:
                    obj_text = obj_file.read_text(encoding="utf-8", errors="ignore")
                    for match in re.finditer(r'[A-Za-z]:\\[^\s"]+|/mnt/[^\s"]+', obj_text):
                        candidate = Path(match.group(0).rstrip(".,;)"))
                        if candidate.is_dir():
                            return candidate
                except Exception:
                    continue

    return None


def _run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(TOOLS_DIR.parent),
        )
        return result.returncode, (result.stdout + result.stderr)
    except subprocess.TimeoutExpired:
        return -1, f"{Path(cmd[1]).name} timed out"
    except Exception as e:  # noqa: BLE001
        return -1, f"{Path(cmd[1]).name} error: {e}"


def _result(name: str, status: str, detail: str) -> dict:
    return {"name": name, "status": status, "detail": detail}


# --- individual gates -------------------------------------------------------

def gate_validate_semantic(html_path: Path | None, css_path: Path | None, profile: str) -> dict:
    name = "validate-semantic"
    if not html_path or not css_path:
        return _result(name, SKIP, "no html/css")
    rc, output = _run([
        sys.executable, str(VALIDATE_SCRIPT),
        "--html", str(html_path), "--css", str(css_path), "--profile", profile,
    ])
    if rc < 0:
        return _result(name, SKIP, f"runner error: {output[:120]}")
    critical = output.count("[CRITICAL]")
    if critical > 0:
        lines = [l.strip()[:100] for l in output.split("\n") if "[CRITICAL]" in l]
        return _result(name, BLOCK, f"{critical} CRITICAL: " + "; ".join(lines[:5]))
    return _result(name, PASS, f"clean (profile={profile})")


def gate_output_boundary(deliverable_dir: Path | None) -> dict:
    name = "output-boundary"
    if not deliverable_dir or not deliverable_dir.is_dir():
        return _result(name, SKIP, "no deliverable dir")
    rc, output = _run([
        sys.executable, str(TOOLS_DIR / "check-output-boundary.py"),
        "--deliverable", str(deliverable_dir),
    ])
    if rc < 0:
        return _result(name, SKIP, f"runner error: {output[:120]}")
    if rc == 1:
        return _result(name, BLOCK, output.strip().replace("\n", " ")[:300])
    return _result(name, PASS, "boundary clean")


def gate_mixed_styles(spec_file: Path | None, html_path: Path | None, css_path: Path | None) -> dict:
    name = "mixed-styles"
    if not spec_file or not html_path or not css_path:
        return _result(name, SKIP, "no spec.json / html / css")
    rc, output = _run([
        sys.executable, str(TOOLS_DIR / "check-mixed-styles.py"),
        "--spec", str(spec_file), "--html", str(html_path), "--css", str(css_path),
    ])
    if rc < 0:
        return _result(name, SKIP, f"runner error: {output[:120]}")
    if rc == 1:
        return _result(name, BLOCK, output.strip().replace("\n", " ")[:300])
    return _result(name, PASS, "segments preserved")


def gate_deprecated_tools(project_root: Path) -> dict:
    name = "deprecated-tools"
    rc, output = _run([
        sys.executable, str(TOOLS_DIR / "check-deprecated-tools.py"),
        "--root", str(project_root),
    ])
    if rc < 0:
        return _result(name, SKIP, f"runner error: {output[:120]}")
    if rc == 1:
        return _result(name, BLOCK, output.strip().replace("\n", " ")[:300])
    return _result(name, PASS, "no deprecated tool usage")


def gate_workflow_order(ledger: Path | None) -> dict:
    name = "workflow-order"
    if not ledger or not ledger.is_file():
        return _result(name, SKIP, "no workflow ledger (pending #4)")
    rc, output = _run([
        sys.executable, str(TOOLS_DIR / "check-workflow-order.py"),
        "--ledger", str(ledger),
    ])
    if rc < 0:
        return _result(name, SKIP, f"runner error: {output[:120]}")
    if rc == 1:
        return _result(name, BLOCK, output.strip().replace("\n", " ")[:300])
    return _result(name, PASS, "2-pass order ok")


def gate_extraction_provenance(ledger: Path | None) -> dict:
    name = "extraction-provenance"
    if not ledger or not ledger.is_file():
        return _result(name, SKIP, "no workflow ledger (pending #4)")
    rc, output = _run([
        sys.executable, str(TOOLS_DIR / "check-extraction-provenance.py"),
        "--ledger", str(ledger),
    ])
    if rc < 0:
        return _result(name, SKIP, f"runner error: {output[:120]}")
    if rc == 1:
        return _result(name, BLOCK, output.strip().replace("\n", " ")[:300])
    return _result(name, PASS, "provenance ok")


def gate_spec_measured(spec_files: list[Path]) -> dict:
    """FORCE Figma 실측: a publishing deliverable must ship extracted/*_spec.json
    with real typography. No spec / no fontSize = the agent guessed instead of
    measuring → BLOCK (no silent skip)."""
    name = "spec-measured"
    if not spec_files:
        return _result(name, BLOCK,
                       "extracted/*_spec.json 없음 — Figma 실측 누락. "
                       "figma-section-spec.py --download-assets 로 spec 추출 필수")
    if not spec_has_font_metadata(spec_files):
        return _result(name, BLOCK,
                       "spec.json 에 폰트 메타데이터(fontSize) 없음 — MCP 폴백/추측 의심. "
                       "figma-section-spec.py 로 재추출 필요")
    return _result(name, PASS, f"{len(spec_files)} spec.json (typography ok)")


def gate_verify_evidence(html_path: Path | None, css_path: Path | None, report: Path | None) -> dict:
    """FORCE 검증툴 실행: completion requires a fresh pm-verify report sha-bound to
    the current html/css. No report (= pm-verify never run) or stale → BLOCK."""
    name = "verify-evidence"
    if not html_path or not css_path or not report:
        return _result(name, BLOCK, "pm-verify 증거 리포트 경로 불명")
    rc, output = _run([
        sys.executable, str(TOOLS_DIR / "verify-evidence-gate.py"),
        "--html", str(html_path), "--css", str(css_path), "--report", str(report),
    ])
    if rc < 0:
        return _result(name, BLOCK, f"runner error: {output[:120]}")
    if rc == 1:
        # no_evidence / stale_evidence / verification_failed
        return _result(name, BLOCK,
                       output.strip().replace("\n", " ")[:200]
                       + " — pm-verify --emit-report 로 검증 후 재제출")
    return _result(name, PASS, "fresh pm-verify evidence")


def evaluate_gates(
    deliverable_dir: Path | None,
    html_path: Path | None,
    css_path: Path | None,
    spec_file: Path | None,
    project_root: Path,
    ledger: Path | None,
    profile: str,
    spec_files: list[Path] | None = None,
    verify_report: Path | None = None,
) -> list[dict]:
    """Run all wired gates and return their results in order."""
    return [
        gate_spec_measured(spec_files if spec_files is not None else ([spec_file] if spec_file else [])),
        gate_verify_evidence(html_path, css_path, verify_report),
        gate_validate_semantic(html_path, css_path, profile),
        gate_output_boundary(deliverable_dir),
        gate_mixed_styles(spec_file, html_path, css_path),
        gate_deprecated_tools(project_root),
        gate_workflow_order(ledger),
        gate_extraction_provenance(ledger),
    ]


def summarize(gate_results: list[dict]) -> tuple[str, str]:
    """Collapse gate results to (decision, reason). decision in {allow, block}."""
    blocked = [g for g in gate_results if g["status"] == BLOCK]
    if blocked:
        parts = [f"{g['name']}: {g['detail']}" for g in blocked]
        return "block", "[accept-preflight] BLOCKED — " + " | ".join(parts)
    passed = [g["name"] for g in gate_results if g["status"] == PASS]
    skipped = [g["name"] for g in gate_results if g["status"] == SKIP]
    reason = (
        "[accept-preflight] PASS — "
        f"passed: {', '.join(passed) or 'none'}"
        + (f"; skipped: {', '.join(skipped)}" if skipped else "")
    )
    return "allow", reason


def main() -> int:
    parser = argparse.ArgumentParser(description="Accept preflight pm-verify gate")
    parser.add_argument("--req", required=True, help="REQ ID (e.g. REQ-047)")
    parser.add_argument("--project-root", help="Project root override")
    parser.add_argument("--html", help="Direct HTML path override")
    parser.add_argument("--css", help="Direct CSS path override")
    parser.add_argument("--json", action="store_true", help="JSON output for hook consumption")
    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else find_project_root()

    # Find HTML/CSS files
    html_path = Path(args.html) if args.html else None
    css_path = Path(args.css) if args.css else None
    output_dir: Path | None = None

    if not html_path or not css_path:
        # Try to find from REQ output directory
        output_dir = find_req_output_dir(project_root, args.req)
        if output_dir:
            found_html, found_css, _ = find_html_css_in_dir(output_dir)
            html_path = html_path or found_html
            css_path = css_path or found_css

        # Also search in project root html/ subdirectory
        if not html_path or not css_path:
            html_subdir = project_root / "html"
            if html_subdir.is_dir():
                output_dir = output_dir or html_subdir
                found_html, found_css, _ = find_html_css_in_dir(html_subdir)
                html_path = html_path or found_html
                css_path = css_path or found_css

    if not html_path or not css_path:
        msg = f"[accept-preflight] SKIP — no HTML/CSS found for {args.req} (non-publishing REQ)"
        if args.json:
            print(json.dumps({"decision": "allow", "reason": msg}))
        else:
            print(msg)
        return 2

    if not html_path.exists() or not css_path.exists():
        msg = f"[accept-preflight] SKIP — files not found: html={html_path}, css={css_path}"
        if args.json:
            print(json.dumps({"decision": "allow", "reason": msg}))
        else:
            print(msg)
        return 2

    # Resolve the deliverable dir from the html file location when not yet known.
    if output_dir is None:
        output_dir = html_path.parent
        if output_dir.name == "page":  # page/ lives inside the deliverable root
            output_dir = output_dir.parent

    profile = detect_profile(css_path)
    spec_files = find_spec_files(output_dir) if output_dir else []
    spec_file = spec_files[0] if spec_files else None
    ledger = find_ledger(project_root, output_dir)
    verify_report = find_verify_report(output_dir, project_root)

    gate_results = evaluate_gates(
        deliverable_dir=output_dir,
        html_path=html_path,
        css_path=css_path,
        spec_file=spec_file,
        project_root=project_root,
        ledger=ledger,
        profile=profile,
        spec_files=spec_files,
        verify_report=verify_report,
    )
    decision, reason = summarize(gate_results)

    if args.json:
        print(json.dumps({"decision": "block" if decision == "block" else "allow", "reason": reason}))
    else:
        print(reason)
        for g in gate_results:
            mark = {"pass": "✓", "block": "✗", "skip": "·"}[g["status"]]
            print(f"  {mark} {g['name']}: {g['detail']}")

    return 1 if decision == "block" else 0


if __name__ == "__main__":
    sys.exit(main())
