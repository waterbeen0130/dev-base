# Implementation Request — REQ-040 / Task 01

**Request**: REQ-040 (파이프라인 근본 개선 3축)
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-040-T01`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-040/tasks/01/spec.md`

---

## 구현 컨텍스트

오늘 목포플레이파크 검증에서 figma-validate 가 단일 `--spec` 만 받아서 7 섹션 HTML을 PM 이 수동으로 7번 돌려 집계 → 330+건 위반을 늦게 발견. 또한 text byte-exact (NBSP/특수 공백) 미체크, asset_manifest 생성은 되는데 검증 미통합.

3가지 동시 도입:

1. **`--spec-dir`**: 디렉토리 전체 spec.json 일괄 로드 → 합본 HTML 대비 검증
2. **text byte-exact**: spec.text_nodes[].characters 가 HTML에 그대로 존재 (NBSP/특수 공백 포함)
3. **asset_manifest 양방향 일치**: 통이미지(AI 합성) 감지 + Figma 이미지 누락 감지

## 구현 상세

### 1. `tools/figma-validate.py` 확장

#### (a) `--spec-dir DIR` 옵션

```python
parser.add_argument("--spec", help="Path to single spec.json")
parser.add_argument("--spec-dir", help="Directory containing *_spec.json files")
# 두 옵션 동시 사용 시 argparse error
if args.spec and args.spec_dir:
    parser.error("--spec and --spec-dir are mutually exclusive")
```

- `--spec-dir` 활성 시: `glob.glob(f"{dir}/*_spec.json")` 로 전부 수집
- 각 spec 에 대해 기존 검증 로직 반복 실행
- 출력 포맷: 섹션별 서브 헤더 + 위반 행 + 마지막에 섹션별 카운트 요약 표

```
=== [hero] ===
위반 카테고리  | 건수
폰트 5필드    | 14
padding/gap  | 25
...

=== 총계 ===
섹션          | CRITICAL | MAJOR | MINOR | 합계
hero          | 2        | 52    | 13    | 67
adventure     | 22       | 68    | 11    | 101
...
전체          | 33       | 247   | 58    | 338
```

#### (b) 텍스트 byte-exact 카테고리

```python
def validate_text_byte_exact(spec: dict, html: str) -> list[Violation]:
    """
    spec.text_nodes[i].characters 가 HTML 에 byte-exact 포함되는지 검증.
    NBSP (\xa0), LINE SEPARATOR (\u2028), ZWSP (\u200b) 등 특수 공백 포함 여부까지.
    """
    violations = []
    for tn in spec.get("text_nodes", []):
        chars = tn.get("characters", "")
        if not chars:
            continue
        if chars not in html:
            violations.append(Violation(
                category="텍스트 byte-exact",
                node_id=tn.get("id"),
                expected=repr(chars),  # NBSP 가시화
                actual="HTML 에 byte-exact 미발견",
                severity="error"
            ))
    return violations
```

- 기존 "줄바꿈 보존" 카테고리와 중첩되지 않도록 분리 — byte-exact 는 더 엄격한 검사

#### (c) asset_manifest 양방향 일치

```python
def validate_asset_manifest_consistency(spec: dict, html: str, spec_dir: Path | None) -> list[Violation]:
    """
    asset_manifest.json 과 HTML img src 양방향 매칭.
    """
    # 1. asset_manifest 경로 결정
    manifest_path = None
    if spec_dir:
        section_name = spec.get("section", {}).get("name", "").lower()
        candidates = list(spec_dir.glob(f"{section_name}_asset_manifest.json"))
        if candidates:
            manifest_path = candidates[0]
    if not manifest_path or not manifest_path.exists():
        return []  # manifest 없으면 skip (graceful)

    manifest = json.load(manifest_path.open())
    manifest_refs = set(asset["image_ref"] for asset in manifest.get("assets", []))

    # 2. HTML img src 수집 (파일명 basename 기준으로 정규화)
    import re
    html_srcs = set(re.findall(r'<img[^>]+src="([^"]+)"', html))
    html_basenames = set(Path(s).stem for s in html_srcs)  # 확장자 제외 basename

    # 3. 양방향 diff
    violations = []
    # Figma 에 있는데 HTML 에 없음
    for ref in manifest_refs:
        if not any(ref in b or b in ref for b in html_basenames):
            violations.append(Violation("asset_manifest 일치", ref, "HTML에 존재해야 함", "HTML에 미발견", severity="error"))
    # HTML 에 있는데 manifest 없음 (통이미지 의심)
    for b in html_basenames:
        if not any(b in ref or ref in b for ref in manifest_refs):
            violations.append(Violation("asset_manifest 일치", b, "asset_manifest 등록 필요 (Figma 원본)", "통이미지 의심 (manifest 미등록)", severity="error"))
    return violations
```

### 2. `tools/post-impl-verify.py`

- `--spec-dir` 인자 전달 (figma-validate.py 로 passthrough)
- 합본 검증 결과 분류 규칙 업데이트:
  - CRITICAL: 텍스트 byte-exact / asset_manifest / 텍스트 위변조 / fills color
  - MAJOR: padding/gap / clamp / lineHeight / column flex gap
  - IGNORE: 없음 (기존 유지)

### 3. rules SSOT 업데이트

`rules/rules.yaml` 에 2개 룰 추가:

```yaml
  - id: text_byte_exact_required
    description: "Figma spec의 text_nodes[].characters는 HTML에 byte-exact 존재해야 한다 (NBSP/특수공백 포함)."
    severity: error
    priority: 100
    applies_to: [figma]
    category: figma.text
    validation:
      type: custom
      custom_handler: validate_text_byte_exact
    examples:
      bad: "Figma '운영시간\\xa0  10:00' → HTML '운영시간 10:00' (NBSP 소실)"
      good: "byte-exact 복사"

  - id: asset_manifest_consistency
    description: "asset_manifest.json 과 HTML <img src> 는 양방향 일치해야 한다 (통이미지 금지)."
    severity: error
    priority: 100
    applies_to: [figma]
    category: figma.asset
    validation:
      type: custom
      custom_handler: validate_asset_manifest_consistency
    examples:
      bad: "HTML 에 asset_manifest 미등록 이미지 (AI 합성 의심)"
      good: "HTML 이미지 전부 asset_manifest 등록된 Figma 원본"
```

그 후 `python3 -m rules.models` 로 validation_schema.json 재생성. check-rules-drift 에서 `65/65 rules in sync` 확인.

### 4. 신규 테스트 3종

#### `tests/unit/test_figma_validate_spec_dir.py`

```python
def test_spec_dir_runs_all_section_specs(tmp_path):
    # 2개 spec fixture + 합본 HTML/CSS 생성 후 --spec-dir 실행
    # assert: 양쪽 섹션 위반이 1회 실행 출력에 모두 포함
```

#### `tests/unit/test_text_byte_exact.py`

```python
def test_nbsp_missing_is_detected():
    spec = {"text_nodes": [{"id": "n1", "characters": "운영시간\xa0 10:00"}]}
    html = "<div>운영시간 10:00</div>"  # NBSP 일반 공백으로 변조
    violations = validate_text_byte_exact(spec, html)
    assert len(violations) == 1
    assert violations[0].category == "텍스트 byte-exact"
```

#### `tests/unit/test_asset_manifest_fidelity.py`

```python
def test_missing_image_detected(tmp_path):
    # asset_manifest 에 5개, HTML 에 4개 → 1건 위반
def test_phantom_image_detected(tmp_path):
    # HTML 에 manifest 없는 이미지 1개 → 1건 위반
```

### 5. 검증 명령

```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-040-T01

# Pydantic 재생성
python3 -m rules.models

# drift check
python3 tools/check-rules-drift.py --all
# expected: 65/65 rules in sync

# 신규 테스트
pytest tests/unit/test_figma_validate_spec_dir.py tests/unit/test_text_byte_exact.py tests/unit/test_asset_manifest_fidelity.py -v

# 전체 회귀
pytest tests/ -v 2>&1 | tail -20
# expected: 140 + 3 신규 = 143 passed, 0 failed

# 실제 목포 합본 검증 (sanity)
python3 tools/figma-validate.py \
  --spec-dir "/mnt/d/위링/2026-04-15 목포플레이파크/extracted/" \
  --html "/mnt/d/위링/2026-04-15 목포플레이파크/output/a_main/index.html" \
  --css "/mnt/d/위링/2026-04-15 목포플레이파크/output/a_main/common.css" 2>&1 | tail -15
# expected: 섹션별 총계 표 출력
```

### 6. git 커밋 금지 — PM 직접 커밋.

## 규칙

- 기존 `--spec FILE` 경로 호환 유지 (하위 호환)
- `--spec` 와 `--spec-dir` 동시 사용은 argparse error
- Pydantic SSOT 통해서만 rule 추가 (validation_schema.json 수동 편집 금지)
- 기존 140 passed 회귀 없음
- 코드 주석은 영어만

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-040-T01`

## [MANDATORY] 응답에 반드시 포함할 것

1. `tools/figma-validate.py` 변경 diff 요약 (--spec-dir, 2개 신규 카테고리)
2. `rules/rules.yaml` 변경 diff (2개 rule 추가)
3. 검증 명령 5번 전체 출력
