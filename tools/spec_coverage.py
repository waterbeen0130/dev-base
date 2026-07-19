from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


SPEC_COVERAGE_MIN_TEXT_NODES = 5
SPEC_COVERAGE_MIN_RATIO = 0.3
VISIBLE_TEXT_TAGS = {
    "p", "span", "a", "li", "strong", "em", "b", "i", "small", "mark",
    "figcaption", "dt", "dd", "label", "button", "td", "th", "blockquote",
    "cite", "summary", "legend", "h1", "h2", "h3", "h4", "h5", "h6",
}
IGNORED_TEXT_TAGS = {"script", "style", "noscript"}


@dataclass
class _VisibleFrame:
    tag: str
    has_text: bool
    is_outermost: bool


class VisibleTextBlockCounter(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._visible_stack: list[_VisibleFrame] = []
        self._count = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in IGNORED_TEXT_TAGS:
            self._ignored_depth += 1
        if tag in VISIBLE_TEXT_TAGS:
            self._visible_stack.append(
                _VisibleFrame(
                    tag=tag,
                    has_text=False,
                    is_outermost=not self._visible_stack,
                )
            )

    def handle_endtag(self, tag: str) -> None:
        if tag in VISIBLE_TEXT_TAGS:
            for index in range(len(self._visible_stack) - 1, -1, -1):
                frame = self._visible_stack[index]
                if frame.tag != tag:
                    continue
                closed = self._visible_stack.pop(index)
                if closed.is_outermost and closed.has_text:
                    self._count += 1
                break
        if tag in IGNORED_TEXT_TAGS and self._ignored_depth > 0:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth > 0 or not data.strip():
            return
        for frame in self._visible_stack:
            frame.has_text = True

    @property
    def count(self) -> int:
        return self._count


def count_html_text_blocks_from_source(html_source: str) -> int:
    parser = VisibleTextBlockCounter()
    parser.feed(html_source)
    parser.close()
    return parser.count


def count_html_text_blocks(html_path: Path | None) -> int | None:
    if not html_path or not html_path.is_file():
        return None
    return count_html_text_blocks_from_source(html_path.read_text(encoding="utf-8"))


def count_spec_text_nodes(spec_files: list[Path]) -> int:
    count = 0
    for path in spec_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        nodes = data.get("text_nodes")
        if isinstance(nodes, list):
            count += sum(1 for node in nodes if isinstance(node, dict))
    return count


def build_spec_sha_map(spec_files: list[Path]) -> dict[str, str]:
    spec_shas: dict[str, str] = {}
    for path in spec_files:
        try:
            spec_shas[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception:
            continue
    return spec_shas


def _evaluate_spec_file(spec_path: Path, html_text_blocks: int) -> dict[str, object]:
    spec_text_nodes = count_spec_text_nodes([spec_path])
    effective_min_nodes = min(
        SPEC_COVERAGE_MIN_TEXT_NODES,
        max(html_text_blocks, 1),
    )
    ratio = round(spec_text_nodes / html_text_blocks, 4) if html_text_blocks > 0 else 1.0
    passed = (
        spec_text_nodes >= effective_min_nodes
        and ratio >= SPEC_COVERAGE_MIN_RATIO
    )
    return {
        "spec_text_nodes": spec_text_nodes,
        "html_text_blocks": html_text_blocks,
        "ratio": ratio,
        "threshold_ratio": SPEC_COVERAGE_MIN_RATIO,
        "min_nodes": SPEC_COVERAGE_MIN_TEXT_NODES,
        "effective_min_nodes": effective_min_nodes,
        "passed": passed,
        "target_spec_paths": [str(spec_path)],
    }


def measure_spec_coverage(
    spec_files: list[Path],
    html_text_blocks: int | None,
) -> dict[str, object] | None:
    if html_text_blocks is None:
        return None
    if not spec_files:
        effective_min_nodes = min(
            SPEC_COVERAGE_MIN_TEXT_NODES,
            max(html_text_blocks, 1),
        )
        return {
            "spec_text_nodes": 0,
            "html_text_blocks": html_text_blocks,
            "ratio": 0.0 if html_text_blocks > 0 else 1.0,
            "threshold_ratio": SPEC_COVERAGE_MIN_RATIO,
            "min_nodes": SPEC_COVERAGE_MIN_TEXT_NODES,
            "effective_min_nodes": effective_min_nodes,
            "passed": False,
            "target_spec_paths": [],
        }

    measurements = [_evaluate_spec_file(path, html_text_blocks) for path in spec_files]
    # Pick the worst per-spec verdict so one shell spec cannot be masked by another.
    measurements.sort(
        key=lambda item: (
            bool(item["passed"]),
            float(item["ratio"]),
            int(item["spec_text_nodes"]),
            item["target_spec_paths"][0],
        )
    )
    measurement = dict(measurements[0])
    measurement["evaluated_spec_paths"] = [str(path) for path in spec_files]
    return measurement


def format_spec_coverage_detail(measurement: dict[str, object]) -> str:
    return (
        "spec_text_nodes={spec_text_nodes}, html_text_blocks={html_text_blocks}, "
        "ratio={ratio:.2f}, threshold_ratio={threshold_ratio:.2f}, "
        "min_nodes={min_nodes}, effective_min_nodes={effective_min_nodes}, "
        "target_spec_paths={target_spec_paths}"
    ).format(**measurement)
