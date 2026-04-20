# Schema Designer 관점 의견 — IDN-002

## 1. 공식화 가능성 판단
**가능합니다.** 현재 `figma-section-spec.py`는 타입과 반올림(`safe_round_3`) 등을 이미 어느 정도 통제하고 �요청하신 Schema Designer 관점의 분석 의견을 요구사항에 맞추어 작성하고 `/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-schema(gemini).md` 경로에 저장 완료했습니다.

Pydantic을 단일 진실 공급원(SSOT)으로 삼아 JSON Schema를 추출하는 방식이 실용적이고 구조적 안정성을 담보할 수 있을 것으로 판단하여 제안서에 반영했습니다. 추가적으로 더 필요한 분석이나 수정 사항이 있다면 말씀해 주세요.
계에서 Dictionary 대신 Pydantic 인스턴스를 생성 후 JSON으로 덤프하여 정규화 및 필수 키 제약을 강제합니다.
4. **검증기 적용:** `figma-validate.py` 등 소비처에서 최우선으로 스키마 검증(Type/Nullability 체크)을 수행해 로직 복잡도(예: `isinstance` 분기)를 낮춥니다.

## 2. 제안 스키마 초안 (v2 대비 누락 필드 포함)
Fidelity 갭을 보완한 Pydantic/JSON Schema 스타일의 명세 초안입니다.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["schema_version", "section", "text_nodes", "frame_nodes", "vector_nodes"],
  "properties": {
    "schema_version": { "type": "string", "enum": ["2.0.0"] },
    "frame_nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "bbox", "layoutMode", "fills", "strokes"],
        "properties": {
          "id": { "type": "string" },
          "componentId": { "type": ["string", "null"] },
          "layoutMode": { "type": ["string", "null"], "enum": ["HORIZONTAL", "VERTICAL", null] },
          "layoutSizingHorizontal": { "type": ["string", "null"], "enum": ["FIXED", "HUG", "FILL", null] },
          "constraints": {
            "type": ["object", "null"],
            "properties": { "horizontal": {"type": "string"}, "vertical": {"type": "string"} }
          },
          "fills": {
            "type": ["array", "null"],
            "items": {
              "type": "object",
              "properties": {
                "type": { "type": "string", "enum": ["SOLID", "IMAGE", "GRADIENT_LINEAR"] },
                "color": { "type": "string", "pattern": "^#[0-9a-f]{6}$" },
                "gradientStops": { "type": "array" }
              }
            }
          },
          "effects": {
            "type": ["array", "null"],
            "description": "Drop shadow, blur 등"
          },
          "strokes": {
            "type": ["array", "null"],
            "items": { "type": "object", "properties": {"color": {"type": "string"}} }
          },
          "strokeWeight": { "type": ["number", "null"] },
          "cornerRadius": { "type": ["number", "null"] },
          "rectangleCornerRadii": { "type": ["array", "null"], "items": {"type": "number"} }
        }
      }
    }
  }
}
```

## 3. 스키마 버저닝 전략
숫자형 `1`에서 **Semantic Versioning(문자열, 예: `"2.0.0"`)**으로 전환합니다.
- **Major (2.x.x → 3.x.x):** Required 필드 추가/삭제 등 호환성이 깨지는 변경. 검증기(`figma-validate.py`)는 Major 버전 단위로 파싱 로직(Pydantic 모델 클래스)을 분기(`SpecV1`, `SpecV2` 등)하여 하위 호환성을 유지해야 합니다.
- **Minor/Patch:** Optional 필드 추가 등 하위 호환이 보장되는 변경. 구버전 파서에서도 무시(`extra='ignore'`)되거나 정상 처리 가능하게 운영합니다.

## 4. 단일 진실 공급원 (SSOT) 구조
**Pydantic 모델 코드를 단일 진실 공급원**으로 삼는 것이 가장 이상적입니다.
- **(a, b) Python 파이프라인:** `figma-section-spec.py`, `figma-validate.py`는 공유 패키지의 Pydantic 클래스를 직접 import하여 생성/검증 로직에 결합합니다.
- **(c, d) 에이전트 브리프 및 규칙 문서:** Pydantic의 `Field(description="...")` 속성을 풍부하게 작성한 후, CI 파이프라인 스크립트(`build-rules.py` 연계)에서 `model_json_schema()`를 추출해 Markdown 테이블과 JSON Schema 파일(`validation_schema.json`)로 자동 렌더링(Generate)합니다.

## 5. 결정성(Determinism) 보장 방안
Figma API 변경이나 실행 환경과 무관한 완전한 일치를 위해 다음 규칙을 파이프라인에 강제해야 합니다.
- **키 순서 강제:** JSON 직렬화 시 스키마에 정의된 필드 순서를 강제하고, 딕셔너리 키는 알파벳 순으로 정렬합니다 (`sort_keys=True`).
- **명시적 Null:** 값이 없더라도 키를 생략하지 않고 항상 `null`을 명시해 구조를 고정합니다 (예: `exclude_none=False`).
- **배열 정렬:** `text_nodes`, `frame_nodes` 배열 출력 시 항상 절대 좌표(1순위: `y`, 2순위: `x`) 또는 Node ID를 기준으로 오름차순 정렬합니다.
- **부동소수점 및 색상 정규화:** 모든 좌표/크기 수치는 스키마의 사전 Validator 수준에서 소수점 3자리(`round(val, 3)`)로 강제 고정하며, 색상은 `#rrggbb` 형태의 6자리 소문자로 치환합니다.

---

## 공식화 가능성: 가능
근거: Python 기반이므로 Pydantic을 활용해 구조, Nullability, 정규화 제약(반올림/소문자)을 모델 자체에 내재화할 수 있으며, 해당 모델 기반으로 JSON Schema 문서를 자동 파생하여 완벽한 SSOT를 달성할 수 있습니다.EXIT_CODE:0
