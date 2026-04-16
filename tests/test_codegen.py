import hashlib
import html
import importlib.util
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "figma-section-spec.py"
SECTION_SPEC_PATH = ROOT / "extracted" / "section_03_spec.json"


spec = importlib.util.spec_from_file_location("figma_section_spec", SCRIPT_PATH)
figma_section_spec = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["figma_section_spec"] = figma_section_spec
spec.loader.exec_module(figma_section_spec)


class _TagCounter(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.counts: dict[str, int] = {}

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: D401
        self.counts[tag] = self.counts.get(tag, 0) + 1

    def handle_startendtag(self, tag: str, attrs) -> None:  # noqa: D401
        self.counts[tag] = self.counts.get(tag, 0) + 1


def _base_name_from_spec(spec_path: Path) -> str:
    stem = spec_path.stem
    return stem[: -len("_spec")] if stem.endswith("_spec") else stem


def _load_section_spec() -> dict:
    return json.loads(SECTION_SPEC_PATH.read_text(encoding="utf-8"))


def _extraction_result_from_payload(payload: dict):
    return figma_section_spec.ExtractionResult(
        section=payload["section"],
        text_nodes=payload.get("text_nodes", []),
        frame_nodes=payload.get("frame_nodes", []),
        vector_nodes=payload.get("vector_nodes", []),
        interactions=payload.get("interactions", []),
        image_refs=set(payload.get("images", {}).keys()),
    )


def _run_main(monkeypatch: pytest.MonkeyPatch, cli_args: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["figma-section-spec.py", *cli_args])
    return figma_section_spec.main()


def _parse_single_line_css(css_text: str) -> dict[str, str]:
    rules: dict[str, str] = {}
    for line in css_text.splitlines():
        line = line.strip()
        if not line:
            continue
        matched = re.match(r"^(?P<selector>[^{}]+)\{(?P<body>[^{}]*)\}$", line)
        if matched:
            rules[matched.group("selector").strip()] = matched.group("body").strip()
    return rules


def test_codegen_generates_files(tmp_path, monkeypatch):
    monkeypatch.setattr(figma_section_spec, "require_figma_token", lambda: pytest.fail("offline --from-spec should not request FIGMA_TOKEN"))
    output_dir = tmp_path / "out"
    exit_code = _run_main(
        monkeypatch,
        ["--from-spec", str(SECTION_SPEC_PATH), "--output", str(output_dir), "--codegen"],
    )

    assert exit_code == 0
    base_name = _base_name_from_spec(SECTION_SPEC_PATH)
    assert (output_dir / f"{base_name}_spec.json").exists()
    assert (output_dir / f"{base_name}_spec.md").exists()
    assert (output_dir / f"{base_name}_base.html").exists()
    assert (output_dir / f"{base_name}_base.css").exists()
    assert (output_dir / "tokens.json").exists()


def test_base_html_structure():
    payload = _load_section_spec()
    result = _extraction_result_from_payload(payload)
    section_name = "section_03"
    html_output = figma_section_spec.generate_base_html(result, section_name)

    parser = _TagCounter()
    parser.feed(html_output)
    assert parser.counts.get("div", 0) >= len(result.frame_nodes)
    assert parser.counts.get("span", 0) == len(result.text_nodes)

    for text_node in result.text_nodes:
        expected = html.escape(text_node.get("characters", ""), quote=False).replace("\xa0", "&nbsp;").replace("\n", "<br>")
        assert expected in html_output


def test_css_deterministic():
    payload = _load_section_spec()
    result = _extraction_result_from_payload(payload)
    css_1 = figma_section_spec.generate_base_css(result, "section_03")
    css_2 = figma_section_spec.generate_base_css(result, "section_03")

    assert css_1 == css_2
    assert hashlib.sha256(css_1.encode("utf-8")).hexdigest() == hashlib.sha256(css_2.encode("utf-8")).hexdigest()


def test_vertical_no_gap():
    payload = _load_section_spec()
    result = _extraction_result_from_payload(payload)
    css_text = figma_section_spec.generate_base_css(result, "section_03")
    rules = _parse_single_line_css(css_text)

    column_bodies = [body for body in rules.values() if "flex-direction:column" in body]
    assert column_bodies
    assert all("gap:" not in body for body in column_bodies)
    assert any("flex-direction:row" in body and "gap:" in body for body in rules.values())


def test_tokens_color_dedup():
    payload = _load_section_spec()
    result = _extraction_result_from_payload(payload)
    tokens = figma_section_spec.generate_tokens(result)

    colors = {key: value.lower() for key, value in tokens.get("colors", {}).items()}
    assert colors
    assert any(value == "#454545" for value in colors.values())


def test_no_codegen_flag_backward_compat(tmp_path, monkeypatch):
    monkeypatch.setattr(figma_section_spec, "require_figma_token", lambda: pytest.fail("offline --from-spec should not request FIGMA_TOKEN"))
    output_dir = tmp_path / "out"
    exit_code = _run_main(
        monkeypatch,
        ["--from-spec", str(SECTION_SPEC_PATH), "--output", str(output_dir)],
    )

    assert exit_code == 0
    base_name = _base_name_from_spec(SECTION_SPEC_PATH)
    assert (output_dir / f"{base_name}_spec.json").exists()
    assert (output_dir / f"{base_name}_spec.md").exists()
    assert not (output_dir / f"{base_name}_base.html").exists()
    assert not (output_dir / f"{base_name}_base.css").exists()
    assert not (output_dir / "tokens.json").exists()


def test_css_conversion_rules_padding_ratio_letterspacing_and_radius():
    result = figma_section_spec.ExtractionResult(
        section={"id": "1:1", "name": "Example", "bbox": {"x": 0, "y": 0, "w": 1000, "h": 600}},
        text_nodes=[
            {
                "id": "1:3",
                "name": "Title",
                "characters": "Heading",
                "fontFamily": "Pretendard",
                "fontSize": 20,
                "fontWeight": 700,
                "lineHeightPx": 30,
                "letterSpacing": 2,
                "color": "#ffffff",
            }
        ],
        frame_nodes=[
            {
                "id": "1:2",
                "name": "Frame",
                "bbox": {"x": 0, "y": 0, "w": 200, "h": 40},
                "layoutMode": "HORIZONTAL",
                "paddingTop": 120,
                "paddingRight": 0,
                "paddingBottom": 0,
                "paddingLeft": 0,
                "itemSpacing": 16,
                "fills": "#090944",
                "cornerRadius": 999,
            }
        ],
        vector_nodes=[],
        interactions=[],
        image_refs=set(),
    )

    css_text = figma_section_spec.generate_base_css(result, "example")
    assert "clamp(72px,120px,144px)" in css_text
    assert "line-height:1.5;" in css_text
    assert "letter-spacing:0.1em;" in css_text
    assert "border-radius:2em;" in css_text
