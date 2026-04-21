<!-- source-mapping: original=Q&A 대화 sections=[DOD-001, AD-001, R3] -->
# 폐기 도구 완전 삭제

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-001

## 개요

기존 워크플로우에서만 사용되던 11개 도구 + 그 도구를 호출하는 wrapper 함수 + dev-base 어디에서도 참조 흔적을 완전 제거. 새 워크플로우 (PNG → AI 선정 → spec.json 정밀 → pm-verify) 에 사용되지 않는 모든 코드는 git history 만 남기고 작업 트리에서 삭제한다.

## 설계 결정

### AD-001: 완전 삭제 (백업 X)
- **결정**: `tools/.deprecated/` 의 11개 파일을 `git rm` 으로 작업 트리 + 인덱스에서 제거
- **근거**: 사용자 명시 — "백업도 필요없고 아예 삭제". `tools/.deprecated/` 자체가 일시 보관 용도였고, 회수 필요 시 git history (commit `de126b8` 이전) 에서 복구 가능
- **대안 검토**:
  - `.deprecated/` 보관 (회수 가능) — 기각: 향후 다른 AI 가 잘못 참조할 위험
  - `--orphan deprecated` 브랜치 보관 — 기각: 과도한 인프라
- **영향 범위**: tools/, dev-base 전체 grep 대상

## 상세 명세

### 삭제 대상 11개 파일

```
tools/.deprecated/repair-from-violations.py
tools/.deprecated/structural-diff.py
tools/.deprecated/compare-css.py
tools/.deprecated/json-to-html.py
tools/.deprecated/check-rules-drift.py
tools/.deprecated/migrate-spec-v1-to-v2.py
tools/.deprecated/assemble.py
tools/.deprecated/split-sections.py
tools/.deprecated/run-pipeline.py
tools/.deprecated/build-prompts.py
tools/.deprecated/brief-checksum.py
```

### 추가 정리 대상 (참조 흔적)

`post-impl-verify.py` 에서 호출하는 `check-rules-drift` / `repair-from-violations` 호출 코드:
- `--converge` 자동 재시도 루프 비활성 또는 제거
- `--no-repair` 기본값을 `true` 로 변경 (자동 수리 비활성)
- DRIFT 관련 import / 함수 정리

`figma-validate.py` 의 false-positive 카테고리 (POLICY-1, layoutSizing, opacity 등) 는 본 DoD 범위 아님 (DOD-006 / pm-verify 후처리에서 처리)

### grep 검증 대상 키워드

```
repair-from-violations
structural-diff
compare-css
json-to-html
check-rules-drift
migrate-spec
run-pipeline
build-prompts
brief-checksum
assemble.py
split-sections
```

### 검증 절차

1. `git rm tools/.deprecated/*.py`
2. `rm -rf tools/.deprecated/` (빈 디렉토리 정리)
3. `post-impl-verify.py` 의 자동 재시도 / repair 호출 부분 정리
4. dev-base 전체 grep:
   ```bash
   grep -rn "repair-from-violations\|structural-diff\|compare-css\|json-to-html\|check-rules-drift\|migrate-spec\|run-pipeline\|build-prompts\|brief-checksum\|assemble\.py\|split-sections" \
     /mnt/d/dev-base \
     --exclude-dir=node_modules --exclude-dir=.git
   ```
5. 매칭 0건이면 PASS
6. git commit 메시지에 "복구 위치" 명시 (해시)

## Q&A 보강 사항

- **Q3 답변**: "완전 새로 바뀌는 워크플로우에 사용되지 않는 파일은 백업도 필요없고 아예 삭제해줘"
  - 결정: `tools/.deprecated/` 도 같이 삭제 (이전 보관용 디렉토리도 정리)
- **Q4 답변**: "없어" — 제약사항 없음
  - 결정: figma-section-spec.py 도 변경 가능 (단, 본 DoD 범위는 아님)
