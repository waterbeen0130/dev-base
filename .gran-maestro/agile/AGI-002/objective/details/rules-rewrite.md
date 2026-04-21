<!-- source-mapping: original=Q&A 대화 sections=[DOD-003, R4] -->
# 룰/가이드 재작성 — 기존 워크플로우 제거 + 새 워크플로우 대체

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-003

## 개요

`CLAUDE.md`, `rules/*.md`, `templates/` 등에서 기존 워크플로우 설명을 모두 제거하고 새 워크플로우 설명으로 대체. 다음 AI 가 dev-base 를 처음 봐도 새 워크플로우만 알 수 있어야 한다.

## 설계 결정

### AD: 키워드 grep 으로 잔존 검출 강제
- **결정**: DoD measure 를 grep 매칭 0건으로 정의하여 누락 방지
- **근거**: R4 — 기존 워크플로우 키워드를 모두 잡지 못해 일부 가이드에 잔존할 위험
- **영향 범위**: dev-base 전체 (단, .git, node_modules, .gran-maestro/agile 제외)

## 상세 명세

### 제거 대상 키워드 (grep 0건 강제)

```
# 폐기 도구 참조
repair-from-violations
structural-diff
compare-css
json-to-html
check-rules-drift
migrate-spec
run-pipeline
build-prompts
brief-checksum

# 기존 워크플로우 패턴
generate.py
--converge
--max-iterations.*post-impl-verify
auto-repair
--no-repair
POLICY-1 강제
gemini-dev 자동 재시도
codex-dev 자동 재시도
```

### 검토 + 재작성 대상 파일

```
/mnt/d/dev-base/CLAUDE.md
/mnt/d/dev-base/rules/CLAUDE.md
/mnt/d/dev-base/rules/common.md
/mnt/d/dev-base/rules/landing.md
/mnt/d/dev-base/rules/basic.md
/mnt/d/dev-base/rules/ai-pipeline.md
/mnt/d/dev-base/rules/publishing-workflow-guide.md
/mnt/d/dev-base/rules/css-enhancement.md
/mnt/d/dev-base/rules/enhancement-flow.md
/mnt/d/dev-base/rules/codex.md
/mnt/d/dev-base/rules/gemini.md
/mnt/d/dev-base/rules/semantic-transform-rules.md
/mnt/d/dev-base/rules/deprecated.md
/mnt/d/dev-base/templates/semantic-prompt.md
```

### 새 워크플로우 설명으로 대체할 핵심 섹션

CLAUDE.md / rules/CLAUDE.md 에 아래 구조 신설:

```markdown
## Figma 퍼블리싱 워크플로우 (CRITICAL)

### Step 1: Figma 자산 추출
python3 tools/figma-section-spec.py --file-key K --node-id N --output extracted/

### Step 2: PNG 다운로드 (시각 참조 + AI 외주 선정 입력)
python3 tools/figma-png-download.py --file-key K --node-ids N1,N2,... --output figma-png/ --include-fills

### Step 3: 자산 복사
python3 tools/asset-copy.py --extracted extracted/ --img img/

### Step 4: PNG 분석 → 외주 AI 선정 (PM 자동)
PM 이 PNG 시각 + 정량 지표(자산 수, 섹션 수, 이미지 fill 유무) 로 gemini/codex/claude 중 하나 선정 + 사유 사용자 통지

### Step 5: 외주 구현
선정된 AI 에게 spec.json (정확한 값) + PNG (시각 참조) 전달. AI 가 HTML/CSS 작성

### Step 6: PM 검증
python3 tools/pm-verify.py --spec-dir extracted/ --html index.html --css css/common.css --img img/ --profile landing

### Step 7: Playwright 시각 비교
1920px 렌더 + Figma PNG 사용자 비교 → 자연어 피드백 → 수정 → 6 반복
```

### 그리고 명시적으로 금지하는 패턴

```markdown
## 금지 패턴

- generate.py / json-to-html.py 같은 자동 코드 생성 스크립트 작성 금지
- post-impl-verify.py 의 자동 재시도 루프 (--converge) 사용 금지
- repair-from-violations.py 같은 자동 수리 도구 사용 금지
- POLICY-1 (VERTICAL frame margin-bottom 강제) — 모던 CSS gap 과 충돌, 적용하지 말 것
- 도구 단위 테스트 통과 = 파이프라인 통과로 간주 금지 (end-to-end 1 페이지 + pm-verify 통과 후만 보고)
```

### 검증 절차

1. 위 14개 파일 + dev-base 전체 grep:
   ```bash
   grep -rn "repair-from-violations\|structural-diff\|compare-css\|json-to-html\|check-rules-drift\|migrate-spec\|run-pipeline\|build-prompts\|brief-checksum\|generate\.py\|--converge\|auto-repair\|POLICY-1 강제" \
     /mnt/d/dev-base \
     --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.gran-maestro
   ```
2. 매칭 0건 → PASS
3. CLAUDE.md / rules/CLAUDE.md 에 위 "Step 1~7" 섹션 + "금지 패턴" 섹션 존재 확인

## Q&A 보강 사항

- **Q3 답변**: 새 워크플로우에 사용 안 되는 파일은 완전 삭제
  - 결정: 삭제뿐 아니라 **언급된 모든 가이드에서도 참조 제거**까지 포함 (DOD-003)
- **Q6 답변**: 디에스솔루션 관련 모두 배제, 현재 변경 로직 최적화에만 몰두
  - 결정: 새 워크플로우 가이드 작성 시 디에스솔루션 사례 인용 X
