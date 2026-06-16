<!-- source-mapping: original=Q&A 대화 sections=[DOD-007] -->
# 새 워크플로우 실행 매뉴얼

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-007

## 개요

새 프로젝트에서 다른 사람이 혼자 새 워크플로우를 수행할 수 있도록 단계별 명령어 + 의사결정 분기 + 체크리스트 제공.

## 상세 명세

### 사전 조건

- `FIGMA_TOKEN` 환경 변수 설정 (40+ 자, `figd_` 시작)
- `pip install Pillow` (이미지 크롭 사용 시)
- Figma URL 에서 file-key + 섹션별 node-id 확인

### Step 1: 프로젝트 초기화

```bash
python3 D:/dev-base/tools/init-project.py "D:/위링/{날짜} {프로젝트명}" --type landing --publishing
cd "D:/위링/{날짜} {프로젝트명}"
```

체크: `CLAUDE.md`, `css/`, `js/`, `img/`, `.gran-maestro/` 생성 확인

### Step 2: Figma 자산 추출

```bash
FIGMA_TOKEN="figd_..." python3 D:/dev-base/tools/figma-section-spec.py \
  --file-key {KEY} \
  --node-id {ROOT_NODE_ID} \
  --output extracted/
```

체크: `extracted/{section}_spec.json` + `{section}_spec.md` + `{section}_asset_manifest.json` 생성

### Step 3: PNG 다운로드

```bash
FIGMA_TOKEN="figd_..." python3 D:/dev-base/tools/figma-png-download.py \
  --file-key {KEY} \
  --node-ids "{MAIN_NODE},{S1_NODE},{S2_NODE},..." \
  --output .gran-maestro/figma-png/ \
  --include-fills \
  --scale 1
```

체크: `.gran-maestro/figma-png/{section}.png` + `fill_{ref12}.png`

### Step 4: 자산 복사

```bash
python3 D:/dev-base/tools/asset-copy.py \
  --extracted extracted/ \
  --img img/
```

체크: `img/` 에 자산 복사 완료, missing 카운트 확인

### Step 5: 외주 AI 선정

```bash
python3 D:/dev-base/tools/select-ai.py \
  --extracted extracted/ \
  --figma-png .gran-maestro/figma-png/ \
  --img img/ \
  --project-type landing \
  --json
```

출력: 선정된 AI + 사유 + 신뢰도

PM 의사결정:
- `confidence: high` → 그대로 진행
- `confidence: medium` → 사용자에게 사유 보여주고 override 여부 확인

### Step 6: 외주 구현

선정된 AI 에게 아래 입력으로 dispatch:

- spec.json 파일들 (정확한 텍스트/색상/폰트/패딩)
- PNG 파일들 (시각 참조)
- CLAUDE.md (룰 강제)

```bash
# gemini 선정 시
gemini -p "$(cat .gran-maestro/briefs/{name}.md)" --approval-mode yolo --sandbox=false

# codex 선정 시
codex exec --full-auto -C . "$(cat .gran-maestro/briefs/{name}.md)"

# claude 선정 시
# Skill(skill: "mst:claude", args: "--prompt-file .gran-maestro/briefs/{name}.md")
```

브리프 템플릿 (반드시 포함):
- spec.json 파일 경로 + 모든 텍스트는 byte-exact 사용 강제
- PNG 파일 경로 + 시각 참조 명시
- CLAUDE.md 의 룰 (페이지 prefix, 공통 영역 prefix 없음, 시멘틱 마크업, hex/em/px 등) 인라인 포함
- 검증 명령어 + 통과 조건 명시
- "거짓 보고 금지, 자체 검증 결과 raw 출력 그대로 보고" 명시

### Step 7: PM 검증

```bash
python3 D:/dev-base/tools/pm-verify.py \
  --spec-dir extracted/ \
  --html index.html \
  --css css/common.css \
  --img img/ \
  --profile landing
```

판정:
- exit 0 → 다음 단계
- exit 1 → 위반 사항 외주 AI 에게 피드백 → 수정 → 재검증

### Step 8: Playwright 시각 비교

```bash
# HTTP 서버 시동
python3 -m http.server 8765 &

# 사용자가 브라우저로 http://127.0.0.1:8765/ 확인
# 또는 PM 이 Playwright MCP 로 1920px 렌더 → PNG 저장 → 사용자에게 제시
```

사용자 자연어 피드백 → Step 6 또는 Step 7 로 복귀 → 수정

### Step 9: Commit

```bash
git add -A
git commit -m "{프로젝트명} {섹션} — Figma 추출 + 새 워크플로우 적용"
```

### 체크리스트 (commit 직전)

- [ ] pm-verify exit 0
- [ ] broken link 0
- [ ] CLAUDE.md 의 클래스 컨벤션 모두 준수 (grep 검증)
- [ ] 사용자 시각 OK 확인
- [ ] 도구 단위 테스트가 아닌 end-to-end 1 페이지로 검증

### 의사결정 분기

| 상황 | 처리 |
|------|------|
| Figma file-key 못 찾음 | 사용자에게 Figma URL 직접 요청 |
| spec.json 의 image fill 이 다운로드 안 됨 | `figma-png-download --include-fills` 단독 재실행 |
| pm-verify 의 figma-validate 신뢰 카테고리 위반 | 외주 AI 에게 spec 값 피드백 (텍스트/폰트/색상) |
| pm-verify 의 컨벤션 위반 | 외주 AI 에게 룰 키워드 + 위반 위치 피드백 |
| broken link 발견 | asset-copy 재실행 또는 자산 누락 (figma-png-download --include-fills) |
| LLM 이 잘못된 외주 AI 추천 | 정량 점수 우선, 사유 보고 후 PM override |
| 외주 AI 가 거짓 보고 (실제 위반인데 통과 주장) | pm-verify 직접 실행으로 검증, 거짓 확인 시 동일 AI 재dispatch + 강한 피드백 |

### Anti-pattern (절대 하지 말 것)

- generate.py / json-to-html.py 같은 자동 코드 생성 스크립트 작성
- post-impl-verify --converge 자동 재시도 루프 사용
- repair-from-violations 같은 자동 수리
- 외주 AI 자가 보고 신뢰 후 사용자 전달
- "이미 안다" 판단으로 룰 파일 안 읽기
- Figma 노드명을 클래스명으로 박기

## Q&A 보강 사항

- **Q1 답변**: 디에스솔루션 후속은 사용자 요청 시에만
  - 결정: 매뉴얼에 디에스솔루션 사례 X, 일반화된 절차만 기재
- **Q5 답변**: 모든 프로젝트 호환 X, 실패 시 PM 콜백
  - 결정: 매뉴얼은 새 워크플로우 신규 프로젝트 기준만 기재. 기존 프로젝트 마이그레이션 가이드 X
