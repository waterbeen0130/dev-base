#!/usr/bin/env python3
"""
PM verification — simplified, trustworthy subset.

Replaces post-impl-verify.py for the human-in-the-loop publishing
workflow. Runs three categories of checks and filters out known
false-positive categories from figma-validate.py.

TRUSTED categories (reported):
  - 텍스트 byte-exact
  - 폰트 5필드 완결성 (fontFamily, fontSize, fontWeight, lineHeightPx, color)
  - fills color hex 일치
  - HTML/CSS conventions from validate-semantic.py (except noisy rules)
  - broken link check (all <img src> files exist)

NOISY/FALSE-POSITIVE categories (suppressed, listed at end as notes):
  - frame padding/gap 반영
  - v2.layoutSizing.match
  - v2.opacity.match
  - [POLICY-1] VERTICAL frame itemSpacing
  - column flex gap 금지
  - clamp 적용
  - asset_manifest 일치

Usage:
    python3 pm-verify.py \
        --spec-dir path/to/extracted/ \
        --html path/to/index.html \
        --css path/to/css/common.css \
        --img path/to/img/ \
        [--profile landing]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from html.parser import HTMLParser


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from spec_coverage import (  # noqa: E402
    build_spec_sha_map,
    count_html_text_blocks_from_source,
    format_border_radius_detail,
    format_spec_coverage_detail,
    measure_border_radius_check,
    measure_spec_coverage as shared_measure_spec_coverage,
)

TRUSTED_FIGMA_CATEGORIES = {
    "텍스트 byte-exact",
    "줄바꿈 보존",
    "폰트 5필드 완결성",
    "lineHeight 비율 일치",
    "fills color hex 일치",
    "text-align 일치",
    "interaction URL 일치",
    "텍스트 위변조",
    # Promoted from noise after measuring zero false-positives on correctly-paired
    # schema_v2 output (true-positive on real mismatch, clean pass when correct).
    # Frame-matched only — unmatched ("미매칭") lines are demoted in parse_figma_validate.
    "v2.cornerRadii.match",
    "v2.fills.solid.match",
}

# Categories gated only when the frame/text node was actually matched to a CSS
# rule. The frame→selector matcher is heuristic, so verdicts on unmatched
# ("미매칭") frames are unreliable and demoted to noise.
MATCHED_ONLY_FIGMA_CATEGORIES = {
    "v2.cornerRadii.match",
    "v2.fills.solid.match",
}

NOISY_FIGMA_CATEGORIES = {
    "frame padding/gap 반영",
    "clamp 적용",
    "column flex gap 금지",
    "[POLICY-1] VERTICAL frame itemSpacing must map to margin-bottom",
    "asset_manifest 일치",
    "v2.layoutSizing.match",
    "v2.opacity.match",
    "v2.strokes.match",
    "v2.effects.match",
    "v2.textCase.match",
}

NOISY_SEMANTIC_RULES = {
    # Contradicts modern CSS (gap) — covered already by POLICY-1 upstream
    "vertical_frame_margin_bottom",
    # Hard cap that breaks legitimate designs (e.g. hero with bg layer + content layer)
    "inner_wrapper_limit",
    # Flags Figma-exact ratios like 1.0 / 1.5 as "too tidy" — false positive when spec is exact
    "line_height_tidy_ratio",
    # False positives — flags body{word-break} as duplicate even when reset.css doesn't define it
    "reset_duplicate",
}


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def _normalize_text_for_match(text: str) -> str:
    """Normalize text for byte-exact comparison fallback.

    Handles the common false-negative patterns found in publishing projects:
      - spec.json uses \\n but HTML uses <br>
      - NBSP \\xa0 vs plain space or &nbsp;
      - HTML-escaped characters (& → &amp;)
      - trailing \\r / \\r\\n
    """
    import html as _html
    text = _html.unescape(text)          # &amp; → &, &nbsp; → \xa0
    # Validator-printed escape sequences (literal backslash-n etc.)
    text = text.replace("\\r\\n", " ")
    text = text.replace("\\n", " ")
    text = text.replace("\\r", "")
    text = text.replace("\\xa0", " ")
    text = text.replace("\\u2028", " ")
    # Real control characters
    text = text.replace("\xa0", " ")     # NBSP → space
    text = text.replace(" ", " ")   # line separator → space
    text = text.replace("\r", "")        # strip CR
    text = text.replace("\n", " ")       # linebreak → space
    return " ".join(text.split()).lower()  # collapse whitespace + case insensitive


def _decode_validator_text(text: str) -> str:
    """Decode validator-printed escape sequences into comparable text."""
    text = html.unescape(text)
    text = text.replace("\\r\\n", "\n")
    text = text.replace("\\n", "\n")
    text = text.replace("\\r", "\r")
    text = text.replace("\\xa0", "\xa0")
    text = text.replace("\\u2028", "\u2028")
    return text


def _extract_text_body_from_html(html_text: str) -> str:
    """Strip HTML tags and normalize for byte-exact comparison fallback."""
    # Replace <br> with space before stripping tags
    html_text = re.sub(r"<br\s*/?>", " ", html_text, flags=re.IGNORECASE)
    # Strip all tags
    plain = re.sub(r"<[^>]+>", " ", html_text)
    # HTML unescape (&amp; → &)
    plain = html.unescape(plain)
    return _normalize_text_for_match(plain)


class _HTMLNode:
    def __init__(
        self,
        *,
        tag: str,
        attrs: dict[str, str],
        parent: "_HTMLNode | None",
        children: list["_HTMLNode | str"] | None = None,
    ) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = children or []


def _soft_match_text(spec_text: str, html_normalized: str) -> bool:
    """Return True if normalized spec_text appears in normalized HTML body."""
    spec_norm = _normalize_text_for_match(spec_text)
    if not spec_norm:
        return True
    return spec_norm in html_normalized


class _LinebreakHTMLParser(HTMLParser):
    """Collect text lines separated by <br> and block boundaries."""

    _BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._current: list[str] = []
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered == "br":
            self._flush_line()
        elif lowered in self._BLOCK_TAGS:
            self._flush_line()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "br":
            self._flush_line()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._BLOCK_TAGS:
            self._flush_line()

    def handle_data(self, data: str) -> None:
        self._current.append(data)

    def close(self) -> None:
        super().close()
        self._flush_line()

    def _flush_line(self) -> None:
        normalized = _normalize_text_for_match("".join(self._current))
        if normalized:
            self.parts.append(normalized)
        self._current.clear()


def _extract_html_line_parts(html_text: str) -> list[str]:
    """Return normalized text parts split by explicit/structural line boundaries."""
    parser = _LinebreakHTMLParser()
    parser.feed(html_text)
    parser.close()
    return parser.parts


class _ScopedHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _HTMLNode(tag="__root__", attrs={}, parent=None, children=[])
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _HTMLNode(
            tag=tag.lower(),
            attrs={key.lower(): (value or "") for key, value in attrs},
            parent=self._stack[-1],
            children=[],
        )
        self._stack[-1].children.append(node)
        self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _HTMLNode(
            tag=tag.lower(),
            attrs={key.lower(): (value or "") for key, value in attrs},
            parent=self._stack[-1],
            children=[],
        )
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == lowered:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self._stack[-1].children.append(data)


def _parse_html_tree(html_text: str) -> _HTMLNode:
    parser = _ScopedHTMLParser()
    parser.feed(html_text)
    parser.close()
    return parser.root


def _parse_scope_selector(line: str) -> str | None:
    marker = " @ "
    if marker not in line:
        return None
    return line.rsplit(marker, 1)[1].strip()


def _node_has_class(node: _HTMLNode, class_name: str) -> bool:
    return class_name in node.attrs.get("class", "").split()


def _node_matches_selector(node: _HTMLNode, selector: str) -> bool:
    selector = selector.strip()
    if not selector:
        return False
    if selector.startswith("."):
        return _node_has_class(node, selector[1:])
    if selector.startswith("#"):
        return node.attrs.get("id") == selector[1:]
    return node.tag == selector.lower()


def _find_nodes_for_selector(root: _HTMLNode, selector: str) -> list[_HTMLNode]:
    matched: list[_HTMLNode] = []
    stack = list(reversed(root.children))
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            continue
        if _node_matches_selector(current, selector):
            matched.append(current)
        stack.extend(reversed(current.children))
    return matched


def _collect_node_line_parts(node: _HTMLNode) -> list[str]:
    parts: list[str] = []
    current: list[str] = []

    def flush() -> None:
        normalized = _normalize_text_for_match("".join(current))
        if normalized:
            parts.append(normalized)
        current.clear()

    def visit(child: _HTMLNode | str) -> None:
        if isinstance(child, str):
            current.append(child)
            return
        if child.tag == "br":
            flush()
            return
        if child.tag in _LinebreakHTMLParser._BLOCK_TAGS:
            flush()
        for nested in child.children:
            visit(nested)
        if child.tag in _LinebreakHTMLParser._BLOCK_TAGS:
            flush()

    for child in node.children:
        visit(child)
    flush()
    return parts


def _split_expected_linebreak_segments(spec_text: str) -> list[str]:
    """Split spec text into normalized segments separated by intended line breaks."""
    decoded = _decode_validator_text(spec_text)
    return [segment for segment in (_normalize_text_for_match(part) for part in decoded.split("\n")) if segment]


def _linebreaks_preserved(spec_text: str, html_text: str, scope_selector: str | None = None) -> bool:
    """Return True when HTML preserves the spec line-break count for the text."""
    expected_segments = _split_expected_linebreak_segments(spec_text)
    if len(expected_segments) <= 1:
        return False

    if scope_selector:
        root = _parse_html_tree(html_text)
        nodes = _find_nodes_for_selector(root, scope_selector)
        if nodes:
            for node in nodes:
                html_parts = _collect_node_line_parts(node)
                if len(html_parts) < len(expected_segments):
                    continue
                for start in range(len(html_parts) - len(expected_segments) + 1):
                    window = html_parts[start:start + len(expected_segments)]
                    if window == expected_segments:
                        return True
            return False

    html_parts = _extract_html_line_parts(html_text)
    if len(html_parts) < len(expected_segments):
        return False

    for start in range(len(html_parts) - len(expected_segments) + 1):
        window = html_parts[start:start + len(expected_segments)]
        if window == expected_segments:
            return True
    return False


def parse_figma_validate(output: str, html_text: str = "") -> tuple[list[str], list[str]]:
    """Return (trusted_violations, noisy_notes) — each as list of lines.

    Byte-exact text keeps the historical soft-match fallback to avoid known
    false negatives. Linebreak preservation is stricter: the violation is
    cleared only when the HTML preserves the same line-break count with <br>
    tags or equivalent block-element boundaries between the matched text parts.
    """
    html_normalized = _extract_text_body_from_html(html_text) if html_text else ""
    trusted = []
    noisy = []
    softmatched = []
    linebreak_matched = []
    for line in output.splitlines():
        if "|" not in line:
            continue
        parts = line.split("|")
        category = parts[0].strip()

        # Skip category-summary lines (e.g. "텍스트 byte-exact | 4")
        if len(parts) == 2 and parts[1].strip().isdigit():
            continue

        if category in TRUSTED_FIGMA_CATEGORIES:
            if len(parts) >= 3:
                expected = parts[2].strip()
                if expected.startswith("'") and expected.endswith("'"):
                    expected = expected[1:-1]

                if category == "텍스트 byte-exact" and html_normalized:
                    if _soft_match_text(expected, html_normalized):
                        softmatched.append(line.strip())
                        continue

                if category == "줄바꿈 보존" and html_text:
                    if _linebreaks_preserved(expected, html_text, _parse_scope_selector(line)):
                        linebreak_matched.append(line.strip())
                        continue

            # fills color on inherit chain (anything ending in '> span'):
            # validator can't resolve CSS inherit — demote to noisy
            if category == "fills color hex 일치" and "> span" in line:
                noisy.append(f"[span-inherit] {line.strip()}")
                continue

            # frame-matched-only categories: the heuristic matcher couldn't locate
            # a CSS rule for this frame ("미매칭") — can't trust the verdict, demote.
            if category in MATCHED_ONLY_FIGMA_CATEGORIES and "미매칭" in line:
                noisy.append(f"[unmatched-frame] {line.strip()}")
                continue

            trusted.append(line.strip())
        elif category in NOISY_FIGMA_CATEGORIES:
            noisy.append(line.strip())

    if softmatched:
        noisy.extend([f"[soft-match] {line}" for line in softmatched])
    if linebreak_matched:
        noisy.extend([f"[linebreak-match] {line}" for line in linebreak_matched])
    return trusted, noisy


def parse_semantic(output: str) -> tuple[list[str], list[str]]:
    """Return (critical_major, noisy)."""
    trusted = []
    noisy = []
    for line in output.splitlines():
        m = re.match(r"\[(CRITICAL|MAJOR|MINOR)\]\s+(\S+)", line.strip())
        if not m:
            continue
        severity, rule = m.group(1), m.group(2)
        if rule in NOISY_SEMANTIC_RULES:
            noisy.append(line.strip())
        elif severity in ("CRITICAL", "MAJOR"):
            trusted.append(line.strip())
    return trusted, noisy


def check_broken_links(html_path: Path, img_dir: Path | None) -> list[str]:
    html = html_path.read_text(encoding="utf-8")
    srcs = re.findall(r'src="([^"]+)"', html)
    missing = []
    base = html_path.parent
    for s in srcs:
        if s.startswith(("http://", "https://", "//", "data:")):
            continue
        target = (base / s).resolve()
        if not target.exists():
            missing.append(s)
    return missing


def measure_spec_coverage(spec_dir: Path, html_source: str) -> dict[str, object]:
    spec_files = sorted(spec_dir.glob("*_spec.json")) if spec_dir.exists() else []
    html_text_blocks = count_html_text_blocks_from_source(html_source)
    measurement = shared_measure_spec_coverage(spec_files, html_text_blocks)
    assert measurement is not None
    measurement["spec_shas"] = build_spec_sha_map(spec_files)
    return measurement


def measure_border_radius(spec_dir: Path, css_source: str, html_source: str) -> dict[str, object]:
    spec_files = sorted(spec_dir.glob("*_spec.json")) if spec_dir.exists() else []
    return measure_border_radius_check(spec_files, css_source, html_source)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--spec-dir", required=True)
    parser.add_argument("--html", required=True)
    parser.add_argument("--css", required=True)
    parser.add_argument("--img", help="Image directory for broken link check")
    parser.add_argument("--profile", default="landing")
    parser.add_argument("--emit-report", help="Write verification evidence JSON (DOD-006) to this path")
    parser.add_argument("--allow-missing-spec", action="store_true", help="Allow verification to pass even when spec.json has no font metadata (escape hatch — default: hard fail to force Figma 실측)")
    parser.add_argument("--allow-low-coverage", action="store_true", help="Allow verification to pass with low spec coverage and record the exception in the evidence report")
    parser.add_argument("--section", help="Section name — when set, records the 'verify' step in the workflow ledger (AGI-004 #4)")
    parser.add_argument("--ledger", help="Workflow ledger path override (default: <root>/.gran-maestro/workflow-ledger.json)")
    args = parser.parse_args()

    html_path = Path(args.html)
    css_path = Path(args.css)
    if not html_path.exists() or not css_path.exists():
        print(f"ERROR: html or css not found", file=sys.stderr)
        return 2

    print("=" * 80)
    print("PM 검증 — 신뢰할 수 있는 카테고리만 리포트")
    print("=" * 80)

    # 0. spec font metadata pre-check
    spec_dir = Path(args.spec_dir)
    _spec_has_font = False
    if spec_dir.exists():
        import json as _json
        for sf in sorted(spec_dir.glob("*_spec.json")):
            try:
                sd = _json.loads(sf.read_text(encoding="utf-8"))
                tn = sd.get("text_nodes")
                if isinstance(tn, list) and tn and any(
                    isinstance(n, dict) and n.get("fontSize") for n in tn
                ):
                    _spec_has_font = True
                    break
            except Exception:
                pass
    spec_missing = not _spec_has_font
    if spec_missing:
        if args.allow_missing_spec:
            print("\n⚠️  WARNING: spec에 font 메타데이터 없음 — 폰트 5필드 검증 불가 (--allow-missing-spec)")
            print("   figma-section-spec.py --download-assets 로 재추출하세요")
        else:
            print("\n❌ FAIL: spec.json 폰트 메타데이터(fontSize) 없음 — Figma 실측 누락(추측 의심).")
            print("   figma-section-spec.py --download-assets 로 실측 추출 필수.")
            print("   (정당한 예외 시에만 --allow-missing-spec)")

    html_source = html_path.read_text(encoding="utf-8")
    css_source = css_path.read_text(encoding="utf-8")
    spec_coverage = measure_spec_coverage(spec_dir, html_source)
    spec_coverage_fail = not spec_coverage["passed"]
    if spec_coverage_fail:
        detail = format_spec_coverage_detail(spec_coverage)
        if args.allow_low_coverage:
            print(f"\n⚠️  WARNING: spec 커버리지 낮음 — {detail}")
            print("   감사 기록을 남기고 계속 진행합니다 (--allow-low-coverage).")
        else:
            print(f"\n❌ FAIL: spec 커버리지 부족 — {detail}")
            print("   껍데기 spec 가능성. spec 보강 또는 정당한 예외 시 --allow-low-coverage 사용.")

    border_radius_check = measure_border_radius(spec_dir, css_source, html_source)
    border_radius_fail = border_radius_check["status"] == "failed"
    border_radius_warning = border_radius_check["status"] == "skipped" or bool(border_radius_check["warnings"])
    if border_radius_fail:
        detail = format_border_radius_detail(border_radius_check)
        print(f"\n❌ FAIL: border-radius 검사 실패 — {detail}")
    elif border_radius_warning:
        detail = format_border_radius_detail(border_radius_check)
        print(f"\n⚠️  WARNING: border-radius 검사 {border_radius_check['status']} — {detail}")

    # 1. figma-validate (trusted categories only)
    print("\n[1] Figma 충실도 (텍스트 + 폰트 + 색상)")
    rc_fig, out_fig = run([
        sys.executable,
        str(TOOLS_DIR / "figma-validate.py"),
        "--spec-dir", args.spec_dir,
        "--html", str(html_path),
        "--css", str(css_path),
    ])
    trusted_fig, noisy_fig = parse_figma_validate(out_fig, html_source)
    if trusted_fig:
        print(f"  ✗ {len(trusted_fig)} 위반")
        for v in trusted_fig[:20]:
            print(f"    {v}")
        if len(trusted_fig) > 20:
            print(f"    ... ({len(trusted_fig)-20} 건 생략)")
    else:
        print("  ✓ PASS")

    # 2. validate-semantic (CRITICAL/MAJOR only, filter noisy)
    print("\n[2] HTML/CSS 컨벤션")
    rc_sem, out_sem = run([
        sys.executable,
        str(TOOLS_DIR / "validate-semantic.py"),
        "--html", str(html_path),
        "--css", str(css_path),
        "--profile", args.profile,
    ])
    trusted_sem, noisy_sem = parse_semantic(out_sem)
    if trusted_sem:
        print(f"  ✗ {len(trusted_sem)} 위반 (CRITICAL/MAJOR)")
        for v in trusted_sem[:20]:
            print(f"    {v}")
        if len(trusted_sem) > 20:
            print(f"    ... ({len(trusted_sem)-20} 건 생략)")
    else:
        print("  ✓ PASS")

    # 3. Broken links
    print("\n[3] Broken link (모든 <img src> 실존)")
    missing = check_broken_links(html_path, Path(args.img) if args.img else None)
    if missing:
        print(f"  ✗ {len(missing)} 건 누락")
        for s in missing[:10]:
            print(f"    MISSING: {s}")
    else:
        print("  ✓ PASS")

    # 4. Noisy categories summary (for reference only, not gating)
    if noisy_fig or noisy_sem:
        print(f"\n[참고] 억제된 노이즈 카테고리 — 자동화 한계로 false-positive 다수, 사람 눈으로 필요 시 별도 확인")
        print(f"  figma-validate 노이즈: {len(noisy_fig)} 건 (layoutSizing/opacity/frame/clamp 등)")
        print(f"  validate-semantic 노이즈: {len(noisy_sem)} 건")

    # Gate — missing Figma 실측(spec font metadata) is a hard fail unless escaped.
    spec_gate_fail = spec_missing and not args.allow_missing_spec
    coverage_gate_fail = spec_coverage_fail and not args.allow_low_coverage
    fail = bool(trusted_fig or trusted_sem or missing or spec_gate_fail or coverage_gate_fail or border_radius_fail)

    # DOD-006: emit verification execution evidence (sha-bound to current files)
    if args.emit_report:
        import hashlib
        import json as _json
        from datetime import datetime, timezone
        report = {
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "html_path": str(html_path),
            "css_path": str(css_path),
            "html_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),
            "css_sha256": hashlib.sha256(css_path.read_bytes()).hexdigest(),
            "profile": args.profile,
            "exit_code": 1 if fail else 0,
            "passed": not fail,
            "trusted_figma_violations": len(trusted_fig),
            "trusted_semantic_violations": len(trusted_sem),
            "broken_links": len(missing),
            "spec_coverage": {
                **spec_coverage,
                "allow_low_coverage": args.allow_low_coverage,
                "passed": not coverage_gate_fail,
            },
            "border_radius_check": border_radius_check,
        }
        Path(args.emit_report).write_text(_json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[evidence] 검증 증거 기록: {args.emit_report}")

    # AGI-004 #4: record the verify step in the workflow ledger (opt-in via --section).
    if args.section:
        ledger_cmd = [sys.executable, str(TOOLS_DIR / "workflow-ledger.py")]
        if args.ledger:
            ledger_cmd += ["--ledger", args.ledger]
        ledger_cmd += ["append", "--step", "verify", "--provider", "pm-verify", "--section", args.section]
        rc_led, out_led = run(ledger_cmd)
        tag = "ledger" if rc_led == 0 else "ledger-warn"
        print(f"\n[{tag}] {out_led.strip()}")

    print("\n" + "=" * 80)
    if fail:
        spec_note = ", spec실측누락" if spec_gate_fail else ""
        coverage_note = ", spec커버리지부족" if coverage_gate_fail else ""
        print(f"결과: ✗ FAIL — Figma 위반 {len(trusted_fig)}, 컨벤션 위반 {len(trusted_sem)}, broken {len(missing)}{spec_note}{coverage_note}")
        return 1
    print("결과: ✓ PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
