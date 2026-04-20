#!/usr/bin/env python3
"""Compare rendered DOM structure against a Figma frame-node structure.

This gate intentionally avoids pixel comparison. Font rendering varies by
operating system, but DOM shape should remain stable when generated markup
preserves the Figma hierarchy.

정규화 규칙: tag + sorted(class_list) + children_index_path, text/id/inline style 제외

Normalization includes only:
- lower-case tag names
- sorted class lists for rendered DOM nodes
- child order through each node's children_index_path
- recursively normalized element children

Text content, id attributes, inline styles, attributes, and computed styles are
excluded. Figma FRAME nodes are approximated as ``div`` elements with no
classes; the comparison is therefore useful for tree depth and child-count
drift, not for pixel or styling equality.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


NormalizedNode = dict[str, Any]


def normalize_node(tag: str, classes: list[str] | None, children: list[NormalizedNode], path: str) -> NormalizedNode:
    return {
        "tag": tag.lower(),
        "classes": sorted(classes or []),
        "path": path,
        "children": children,
    }


def compute_hash(tree: NormalizedNode) -> str:
    canonical = json.dumps(tree, sort_keys=False, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def render_dom_tree(html_path: Path, css_path: Path | None = None) -> NormalizedNode:
    abs_html_path = html_path.resolve()
    if not abs_html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    abs_css_path = css_path.resolve() if css_path else None
    if abs_css_path is not None and not abs_css_path.exists():
        raise FileNotFoundError(f"CSS file not found: {css_path}")

    try:
        root = render_dom_tree_with_playwright(abs_html_path, abs_css_path)
    except Exception as exc:
        if "sandbox_host_linux.cc" not in str(exc):
            raise
        root = parse_static_body_tree(abs_html_path)

    if not isinstance(root, dict):
        raise RuntimeError("Playwright returned an invalid DOM tree")
    return root


def render_dom_tree_with_playwright(abs_html_path: Path, abs_css_path: Path | None) -> NormalizedNode:
    pytest_env = {key: os.environ.pop(key) for key in list(os.environ) if key.startswith("PYTEST_")}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.route("http://**/*", lambda route: route.abort())
                page.route("https://**/*", lambda route: route.abort())
                page.goto(abs_html_path.as_uri(), wait_until="domcontentloaded")
                if abs_css_path is not None:
                    inject_css_if_needed(page, abs_css_path)
                try:
                    page.wait_for_load_state("networkidle", timeout=5_000)
                except PlaywrightTimeoutError:
                    pass
                return page.evaluate(
                    """() => {
                        function walk(el, path) {
                            return {
                                tag: el.tagName.toLowerCase(),
                                classes: [...el.classList].sort(),
                                path,
                                children: [...el.children].map((child, index) => walk(child, `${path}/${index}`))
                            };
                        }
                        return walk(document.body, "0");
                    }"""
                )
            finally:
                browser.close()
    finally:
        os.environ.update(pytest_env)


class StaticBodyParser(html.parser.HTMLParser):
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.body: NormalizedNode | None = None
        self.stack: list[NormalizedNode] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_by_name = {name.lower(): value or "" for name, value in attrs}
        node = normalize_node(tag, attrs_by_name.get("class", "").split(), [], "")
        if tag.lower() == "body":
            self.body = node
            self.stack = [node]
            return
        if not self.stack:
            return
        self.stack[-1]["children"].append(node)
        if tag.lower() not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].get("tag") == tag:
                del self.stack[index:]
                return


def parse_static_body_tree(abs_html_path: Path) -> NormalizedNode:
    parser = StaticBodyParser()
    parser.feed(abs_html_path.read_text(encoding="utf-8"))
    root = parser.body or normalize_node("body", [], [], "")
    assign_paths(root, "0")
    return root


def assign_paths(node: NormalizedNode, path: str) -> None:
    node["path"] = path
    children = node.get("children") if isinstance(node.get("children"), list) else []
    for index, child in enumerate(children):
        assign_paths(child, f"{path}/{index}")


def inject_css_if_needed(page: Any, css_path: Path) -> None:
    page.evaluate(
        """href => {
            const hasStylesheet = document.querySelector('link[rel~="stylesheet"]');
            if (hasStylesheet) {
                return;
            }
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = href;
            document.head.appendChild(link);
        }""",
        css_path.resolve().as_uri(),
    )


def normalize_frame_node(frame: dict[str, Any], path: str = "0") -> NormalizedNode:
    children = frame.get("children")
    child_nodes = children if isinstance(children, list) else []
    return normalize_node(
        "div",
        [],
        [normalize_frame_node(child, f"{path}/{index}") for index, child in enumerate(child_nodes) if isinstance(child, dict)],
        path,
    )


def normalize_frame_nodes(frame_nodes: list[dict[str, Any]]) -> NormalizedNode:
    if not frame_nodes:
        return normalize_node("body", [], [], "0")

    if any(isinstance(frame.get("children"), list) for frame in frame_nodes):
        roots = [frame for frame in frame_nodes if isinstance(frame, dict)]
    else:
        roots = build_frame_forest_from_parent_ids(frame_nodes)

    return normalize_node(
        "body",
        [],
        [normalize_frame_node(frame, f"0/{index}") for index, frame in enumerate(roots)],
        "0",
    )


def build_frame_forest_from_parent_ids(frame_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed: list[tuple[str, dict[str, Any]]] = []
    by_id: dict[str, dict[str, Any]] = {}

    for index, frame in enumerate(frame_nodes):
        if not isinstance(frame, dict):
            continue
        frame_id = str(frame.get("id") or f"frame:{index}")
        clone = {key: value for key, value in frame.items() if key != "children"}
        clone["children"] = []
        indexed.append((frame_id, clone))
        by_id[frame_id] = clone

    roots: list[dict[str, Any]] = []
    for frame_id, frame in indexed:
        parent_id = frame.get("parent_id")
        if parent_id is not None and str(parent_id) in by_id and str(parent_id) != frame_id:
            by_id[str(parent_id)]["children"].append(frame)
        else:
            roots.append(frame)
    return roots


def load_spec_tree(spec_path: Path) -> NormalizedNode:
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    structural_tree = payload.get("structural_tree")
    if isinstance(structural_tree, dict):
        return structural_tree
    frame_nodes = payload.get("frame_nodes")
    if not isinstance(frame_nodes, list):
        raise ValueError(f"Invalid spec JSON: expected frame_nodes array ({spec_path})")
    return normalize_frame_nodes([frame for frame in frame_nodes if isinstance(frame, dict)])


def diff_trees(expected: NormalizedNode, actual: NormalizedNode) -> list[str]:
    differences: list[str] = []

    def walk(left: NormalizedNode, right: NormalizedNode, path: str) -> None:
        if left.get("tag") != right.get("tag"):
            differences.append(f"{path}: tag expected {left.get('tag')!r}, actual {right.get('tag')!r}")
        if left.get("classes") != right.get("classes"):
            differences.append(f"{path}: classes expected {left.get('classes')!r}, actual {right.get('classes')!r}")

        left_children = left.get("children") if isinstance(left.get("children"), list) else []
        right_children = right.get("children") if isinstance(right.get("children"), list) else []
        if len(left_children) != len(right_children):
            differences.append(f"{path}: child-count expected {len(left_children)}, actual {len(right_children)}")

        for index, (left_child, right_child) in enumerate(zip(left_children, right_children)):
            walk(left_child, right_child, f"{path}/{index}")

    walk(expected, actual, "0")
    return differences


def run(args: argparse.Namespace) -> int:
    html_path = Path(args.html)
    css_path = Path(args.css) if args.css else None
    dom_tree = render_dom_tree(html_path, css_path)
    dom_hash = compute_hash(dom_tree)

    if args.dump_hash:
        print(dom_hash)
        return 0

    if not args.spec:
        print("ERROR: --spec is required unless --dump-hash is used", file=sys.stderr)
        return 2

    spec_tree = load_spec_tree(Path(args.spec))
    spec_hash = compute_hash(spec_tree)
    if spec_hash == dom_hash:
        print("STRUCTURAL MATCH")
        return 0

    print("STRUCTURE_DRIFT")
    print(f"expected_hash={spec_hash}")
    print(f"actual_hash={dom_hash}")
    for line in diff_trees(spec_tree, dom_tree):
        print(line)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare normalized Playwright DOM tree hash against Figma frame_nodes.")
    parser.add_argument("--spec", help="Path to Figma spec.json")
    parser.add_argument("--html", required=True, help="Path to HTML to render")
    parser.add_argument("--css", help="Optional CSS path, injected only when the HTML has no stylesheet link")
    parser.add_argument("--dump-hash", action="store_true", help="Print DOM hash and skip spec comparison")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
