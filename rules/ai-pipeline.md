# AI 직접 해석 퍼블리싱 파이프라인

## 개요

피그마 디자인 → 정규화 JSON → AI(Gemini)가 섹션별로 직접 HTML/CSS 생성하는 파이프라인.
규칙 기반 기계적 변환(json-to-html.py)은 폐기됨.

## 파이프라인 흐름

```
1. figma-extract.py   → 정규화 JSON (CSS 값 확정)
2. split-sections.py  → 섹션별 JSON 분할
3. build-prompts.py   → 섹션별 Gemini 프롬프트 생성
4. Gemini 병렬 실행    → 섹션별 HTML/CSS 생성
5. assemble.py        → 전체 index.html + common.css 조립
6. 브라우저 스크린샷    → 피그마 원본과 시각 비교
7. validate-semantic.py → 규칙 준수 검증
```

## 실행 방법

### 전체 자동 실행
```bash
python3 D:/dev-base/tools/run-pipeline.py \
  --file-key {피그마파일키} \
  --node-id {노드ID} \
  --output ./output/{프로젝트명} \
  --page {페이지명} \
  --profile basic
```

### 단계별 수동 실행

#### 1단계: 정규화 JSON 추출
```bash
FIGMA_TOKEN="토큰" python3 D:/dev-base/tools/figma-extract.py \
  --node-id {노드ID} --file-key {파일키} --profile basic \
  > normalized.json
```

#### 2단계: 섹션 분할
```bash
python3 D:/dev-base/tools/split-sections.py \
  --input normalized.json --output ./sections/
```

#### 3단계: 프롬프트 생성 + Gemini 실행
```bash
python3 D:/dev-base/tools/build-prompts.py \
  --sections ./sections/ \
  --image-map ./image-map.json \
  --page main --output ./prompts/

# 각 섹션 병렬 실행
gemini -p "$(cat prompts/00_header.md)" --sandbox=false &
gemini -p "$(cat prompts/01_mv.md)" --sandbox=false &
# ...
```

#### 4단계: 조립
```bash
python3 D:/dev-base/tools/assemble.py \
  --results ./gemini_results/ \
  --output ./output/
```

#### 5단계: 검증
```bash
python3 D:/dev-base/tools/validate-semantic.py \
  --html ./output/index.html --css ./output/common.css
```

## 도구 목록

| 도구 | 경로 | 역할 |
|------|------|------|
| figma-extract.py | tools/ | 피그마 API → 정규화 JSON. depth=15 |
| split-sections.py | tools/ | 정규화 JSON → 섹션별 분할 |
| build-prompts.py | tools/ | 섹션별 Gemini 프롬프트 자동 생성 |
| assemble.py | tools/ | Gemini 결과 → index.html + common.css 조립 |
| validate-semantic.py | tools/ | HTML/CSS 규칙 검증 (34규칙) |
| section-prompt.md | tools/templates/ | 프롬프트 템플릿 (common.md 규칙 인라인) |

## 핵심 원칙

1. **CSS 값은 정규화 JSON에서 100% 추출** — AI가 값을 추측하지 않음
2. **구조/태그/선택자는 AI가 판단** — common.md 규칙을 자연어로 이해
3. **텍스트는 JSON 원본 그대로** — 임의 생성/변경 절대 금지
4. **섹션별 처리** — 컨텍스트 크기 관리 + 병렬 실행
5. **브라우저 비교 필수** — 피그마 원본 이미지와 스크린샷 대조 후 전달

## 에이전트 배정

- 주 에이전트: **gemini-dev** (대용량 컨텍스트 + 퍼블리싱)
- PM(Claude)은 오케스트레이션만 — 코드 직접 작성 금지
- 브라우저 테스트 + 피그마 비교는 PM 책임

## 작업 지시 예시

새 프로젝트에서 이 파이프라인을 실행하려면:

```
피그마 파일키: {file_key}
노드 ID: {node_id}
프로젝트명: {name}
프로필: basic 또는 landing

위 파이프라인으로 HTML/CSS를 생성해줘.
```
