from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


class MockResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        json_payload: dict | None = None,
        content: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._json_payload = json_payload
        self.content = content
        self.headers = headers or {}

    def json(self) -> dict:
        if self._json_payload is None:
            raise ValueError("no json")
        return self._json_payload

    def iter_content(self, chunk_size: int = 8192):
        del chunk_size
        yield self.content


def _load_section_module():
    module_name = "figma_section_spec_req044_download"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_validate_module():
    module_name = "figma_validate_req044_download"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_VALIDATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _payload() -> dict:
    return {
        "frame_nodes": [{"id": "2:3", "fills_v2": [{"type": "IMAGE", "imageRef": "img_hash"}]}],
        "vector_nodes": [{"id": "1:2", "fillGeometryPathData": ["M0 0L1 1Z"], "strokeGeometryPathData": []}],
    }


def test_svg_download(tmp_path: Path, monkeypatch) -> None:
    # Arrange
    module = _load_section_module()
    svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg'><path d='M0 0'/></svg>"
    calls: list[str] = []

    def fake_get(url: str, **kwargs):
        calls.append(url)
        if url.startswith("https://api.figma.com"):
            return MockResponse(json_payload={"images": {"1:2": "https://assets.example/vector.svg"}})
        return MockResponse(content=svg_bytes)

    monkeypatch.setattr(module.requests, "get", fake_get)
    assets = [{"ref": "1:2", "kind": "vector", "hash": "metadata", "spec_node_id": "1:2"}]

    # Act
    downloads = module.download_assets(assets, "FILE", "TOKEN", tmp_path, "hero")

    # Assert
    asset_path = tmp_path / "hero" / "vectors" / "1_2.svg"
    assert asset_path.read_bytes().startswith(b"<svg")
    assert downloads[("vector", "1:2")]["local_path"] == "hero/vectors/1_2.svg"
    assert downloads[("vector", "1:2")]["format"] == "svg"
    assert downloads[("vector", "1:2")]["hash"] == hashlib.sha256(svg_bytes).hexdigest()
    assert len(calls) == 2


def test_png_download(tmp_path: Path, monkeypatch) -> None:
    # Arrange
    module = _load_section_module()
    png_bytes = b"\x89PNG\r\n\x1a\npayload"

    def fake_get(url: str, **kwargs):
        if url.startswith("https://api.figma.com"):
            return MockResponse(json_payload={"images": {"2:3": "https://assets.example/image.png"}})
        return MockResponse(content=png_bytes)

    monkeypatch.setattr(module.requests, "get", fake_get)
    assets = [{"ref": "img_hash", "kind": "image", "hash": "img_hash", "spec_node_id": "2:3"}]

    # Act
    downloads = module.download_assets(assets, "FILE", "TOKEN", tmp_path, "hero")

    # Assert
    asset_path = tmp_path / "hero" / "images" / "img_hash.png"
    assert asset_path.read_bytes()[:4] == b"\x89PNG"
    assert downloads[("image", "img_hash")]["local_path"] == "hero/images/img_hash.png"
    assert downloads[("image", "img_hash")]["format"] == "png"


def test_manifest_schema(tmp_path: Path, monkeypatch) -> None:
    # Arrange
    module = _load_section_module()
    svg_bytes = b"<svg><path d='M0 0'/></svg>"
    png_bytes = b"\x89PNG\r\n\x1a\npayload"

    def fake_get(url: str, **kwargs):
        params = kwargs.get("params", {})
        if url.startswith("https://api.figma.com") and params.get("format") == "svg":
            return MockResponse(json_payload={"images": {"1:2": "https://assets.example/vector.svg"}})
        if url.startswith("https://api.figma.com") and params.get("format") == "png":
            return MockResponse(json_payload={"images": {"2:3": "https://assets.example/image.png"}})
        if url.endswith("vector.svg"):
            return MockResponse(content=svg_bytes)
        return MockResponse(content=png_bytes)

    monkeypatch.setattr(module.requests, "get", fake_get)
    base_manifest = module.build_asset_manifest(_payload())

    # Act
    downloads = module.download_assets(base_manifest["assets"], "FILE", "TOKEN", tmp_path, "hero")
    manifest = module.build_asset_manifest(_payload(), downloads)

    # Assert
    for asset in manifest["assets"]:
        assert "local_path" in asset
        assert asset["format"] in {"svg", "png"}
        assert len(asset["hash"]) == 64
        assert asset["hash"] != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_backward_compat() -> None:
    # Arrange
    module = _load_section_module()

    # Act
    manifest = module.build_asset_manifest(_payload())

    # Assert
    image_asset = next(asset for asset in manifest["assets"] if asset["kind"] == "image")
    vector_asset = next(asset for asset in manifest["assets"] if asset["kind"] == "vector")
    assert "local_path" not in image_asset
    assert "format" not in image_asset
    assert image_asset["hash"] == "img_hash"
    assert "local_path" not in vector_asset
    assert "format" not in vector_asset
    assert vector_asset["hash"] == hashlib.sha256(b"M0 0L1 1Z").hexdigest()


def test_download_assets_error_handling(tmp_path: Path, monkeypatch, capsys) -> None:
    # Arrange
    module = _load_section_module()

    def fake_get(url: str, **kwargs):
        del url, kwargs
        return MockResponse(status_code=500, json_payload={"err": "nope"})

    monkeypatch.setattr(module.requests, "get", fake_get)
    base_manifest = module.build_asset_manifest(_payload())

    # Act
    downloads = module.download_assets(base_manifest["assets"], "FILE", "TOKEN", tmp_path, "hero")
    manifest = module.build_asset_manifest(_payload(), downloads)

    # Assert
    assert downloads == {}
    assert not (tmp_path / "hero").exists()
    assert all("local_path" not in asset for asset in manifest["assets"])
    assert "warning: Figma images API request failed" in capsys.readouterr().err


def test_validator_accepts_local_path_manifest_consistency(tmp_path: Path) -> None:
    # Arrange
    module = _load_validate_module()
    spec = {"section": {"name": "hero"}}
    manifest = {
        "assets": [
            {
                "ref": "1:2",
                "kind": "vector",
                "hash": "a" * 64,
                "spec_node_id": "1:2",
                "local_path": "hero/vectors/1_2.svg",
                "format": "svg",
            }
        ]
    }
    (tmp_path / "hero_asset_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    html = '<img src="./hero/vectors/1_2.svg">'

    # Act
    violations = module.validate_asset_manifest_consistency(spec, html, tmp_path)

    # Assert
    assert violations == []
