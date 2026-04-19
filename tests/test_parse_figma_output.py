import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "post-impl-verify.py"

spec = importlib.util.spec_from_file_location("post_impl_verify", SCRIPT_PATH)
post_impl_verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post_impl_verify)
KNOWN_CATEGORIES = set(post_impl_verify.V2_CATEGORIES)


def _build_output(lines: list[str]) -> str:
    body = "\n".join(lines)
    return f"카테고리 | 노드 | 기대값 | 실제값\n{body}\n\n누락된 spec 행\n없음\n"


def test_parse_figma_output_singleline_row():
    output = _build_output(
        ["텍스트 위변조 | 842:88 (VS) | VS | HTML 텍스트 미발견"]
    )

    result = post_impl_verify.parse_figma_output(output, 1, KNOWN_CATEGORIES)

    assert result["runner_error"] is False
    assert result["critical"] == 1
    assert result["major"] == 0
    assert len(result["violations"]) == 1
    violation = result["violations"][0]
    assert violation["category"] == "텍스트 위변조"
    assert violation["node"] == "842:88 (VS)"
    assert violation["expected"] == "VS"
    assert violation["actual"] == "HTML 텍스트 미발견"


def test_parse_figma_output_multiline_expected_text_preserved():
    output = _build_output(
        [
            "텍스트 위변조 | 842:137 (abc) | 누구나 모제림을 흉내 낼 순 있지만, 1997년부터 축적된 오리지널의 시스템은 따라할 수 없습니다.",
            "모제림은 수술 경험 없는 신입 원장을 철저히 배제하고, 수술 시작부터 끝까지 마스터 집도의가 직접 책임집니다. | HTML 텍스트 미발견",
        ]
    )

    result = post_impl_verify.parse_figma_output(output, 1, KNOWN_CATEGORIES)

    assert len(result["violations"]) == 1
    violation = result["violations"][0]
    assert violation["expected"] == (
        "누구나 모제림을 흉내 낼 순 있지만, 1997년부터 축적된 오리지널의 시스템은 따라할 수 없습니다.\n"
        "모제림은 수술 경험 없는 신입 원장을 철저히 배제하고, 수술 시작부터 끝까지 마스터 집도의가 직접 책임집니다."
    )
    assert violation["actual"] == "HTML 텍스트 미발견"


def test_parse_figma_output_multiple_rows_with_one_multiline():
    output = _build_output(
        [
            "폰트 5필드 완결성 | 842:90 (headline) | font-family, font-size, font-weight, line-height, letter-spacing | missing: font-size @ .headline",
            "텍스트 위변조 | 842:137 (abc) | 첫 줄 텍스트",
            "둘째 줄 텍스트 | HTML 텍스트 미발견",
            'interaction URL 일치 | 888:10 (cta) | <a href="https://example.com" target="_blank"> | 불일치',
        ]
    )

    result = post_impl_verify.parse_figma_output(output, 1, KNOWN_CATEGORIES)

    assert len(result["violations"]) == 3
    assert [item["category"] for item in result["violations"]] == [
        "폰트 5필드 완결성",
        "텍스트 위변조",
        "interaction URL 일치",
    ]
    assert result["violations"][1]["expected"] == "첫 줄 텍스트\n둘째 줄 텍스트"
    assert result["violations"][1]["actual"] == "HTML 텍스트 미발견"


def test_parse_figma_output_multiline_node_and_expected_are_not_merged_with_previous_row():
    output = _build_output(
        [
            "텍스트 위변조 | 842:204 (a hair transplant plan) | a hair transplant plan | HTML 텍스트 미발견",
            "텍스트 위변조 | 842:205 (모발이식 첫 줄",
            "모발이식 둘째 줄) | 기대값 첫 줄",
            "기대값 둘째 줄 | HTML 텍스트 미발견",
        ]
    )

    result = post_impl_verify.parse_figma_output(output, 1, KNOWN_CATEGORIES)

    assert len(result["violations"]) == 2
    first, second = result["violations"]
    assert first["node"] == "842:204 (a hair transplant plan)"
    assert first["actual"] == "HTML 텍스트 미발견"
    assert second["category"] == "텍스트 위변조"
    assert second["node"] == "842:205 (모발이식 첫 줄\n모발이식 둘째 줄)"
    assert second["expected"] == "기대값 첫 줄\n기대값 둘째 줄"
    assert second["actual"] == "HTML 텍스트 미발견"
