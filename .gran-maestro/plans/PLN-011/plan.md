# PLN-011 — 디에스솔루션 MAIN 페이지 end-to-end 파이프라인 드릴 런 + 검증

- 생성일: 2026-04-21
- Cynefin: Complicated
- 상태: active

## 1. 요청 (Refined)

어제까지 완성된 Figma → HTML/CSS 파이프라인(PLN-004/005/009/010 + REQ-040/041/042)을 실제 신규 Figma 소스에 적용하여 end-to-end 동작을 검증한다. 수렴 루프(`post-impl-verify --converge`), 구조 불변 원칙(text byte-exact / DOM 보존 / asset_manifest fidelity), 4종 게이트(figma-validate / validate-semantic / structural-diff / post-impl-verify) 가 실제 환경에서 작동하는지 확인하는 드릴 런이다.

## 2. 범위

**포함**
- 신규 프로젝트 폴더 초기화 (`tools/init-project.py --type basic --publishing`)
- Figma 데이터 추출: `figma-section-spec.py`로 MAIN 페이지 전체 섹션 spec 생성
- AI 구현: gemini-dev가 spec.md만 참조하여 HTML/CSS 작성
- 4종 게이트 통과까지 자동 수렴 (`--converge`, max_iter=2)
- 최종 결과 사용자 검수

**제외**
- 서브페이지(Sub) 추출 — MAIN만
- 파이프라인 도구 자체 수정 — 드릴 런이므로 발견 이슈는 기록만
- 모바일 반응형 세부 조정 (PC 1920 기준만)
- 실 배포

**대상**
- Figma URL: `https://www.figma.com/design/JLCP6dWG63kJVBlND7bVZl/디에스솔루션?node-id=130-10972`
- file-key: `JLCP6dWG63kJVBlND7bVZl`
- 페이지: `📌Main_Sub (260417)` 내 MAIN 페이지 (node 130:10972)

## 3. 결정 사항

- **출력 경로**: `D:/위링/2026-04-21 디에스솔루션/` (신규, `init-project.py --publishing`로 초기화)
- **검증 범위**: 풀 파이프라인 — spec 생성 → AI 구현 → 4종 게이트 → 수렴 루프
- **AI 에이전트**: gemini-dev (퍼블리싱 CLAUDE.md 규정)
- **토큰**: `FIGMA_TOKEN` 환경변수 (위링 개인 토큰, ~/.figma_token 존재)
- **브리프 템플릿**: `rules/templates/publishing/impl-request.md` (rules_version: 2, rule_ids 포함)
- **실패 시 정책**: 수렴 루프 max_iter=2 초과 시 사용자 개입, 파이프라인 도구 자체 버그 의심 시 별도 REQ 생성

## 4. 인수 기준 초안

이 plan의 구현이 완료됐다는 것은:

- [MUST] [TIER-A] `D:/위링/2026-04-21 디에스솔루션/` 에 `init-project.py --publishing` 기반 초기 구조가 생성되어 있다 (`.claude/settings.local.json`, `.gran-maestro/config.json`, `CLAUDE.md` 등)
- [MUST] [TIER-A] `extracted/` 디렉토리에 MAIN 페이지의 모든 섹션 `{section}_spec.md` + `{section}_spec.json` 파일이 존재한다
- [MUST] [TIER-A] `asset_manifest.json` 이 생성되고 모든 이미지 fills 가 매핑되어 있다
- [MUST] [TIER-A] `output/a_main/index.html` + `output/a_main/common.css` 가 생성되고 spec 의 text_nodes[].characters 가 byte-exact 로 HTML 에 반영되어 있다 (NBSP/라인 분리자/연속 공백 포함)
- [MUST] [TIER-A] `figma-validate.py` 가 모든 섹션에 대해 exit 0
- [MUST] [TIER-A] `validate-semantic.py --profile basic` 이 CRITICAL 0건으로 exit 0
- [MUST] [TIER-A] `post-impl-verify.py --converge` 가 exit 0 (CRITICAL 0건 + MAJOR 허용 범위 이하)
- [MUST] [TIER-A] `structural-diff.py --dump-hash` 가 spec DOM 계층과 일치
- [SHOULD] [TIER-B] 실행 로그(`running.log`)와 수렴 루프 반복 횟수가 REQ 폴더에 기록되어 있다
- [SHOULD] [TIER-B] 드릴 런에서 발견된 파이프라인 이슈 목록이 리포트 형식으로 요약되어 있다 (별도 PLN-012 후속 소스)

## 5. 범위 예산 (Appetite)

- 1차 실행 시간 상한: 3시간 (수렴 루프 포함)
- 외주 호출 상한: gemini-dev 최대 2회 (max_cli_retries=2)
- 파이프라인 도구 수정 금지 — 드릴 런 목적

## 6. 제외 범위 (No-go Scope)

- Sub 페이지 추출
- 모바일 반응형 세부 조정
- 실 배포 / 도메인 연결
- 파이프라인 도구(figma-section-spec / figma-validate / post-impl-verify) 수정

## 7. 제약사항

**기술적 제약**
- FIGMA_TOKEN 환경변수 필수 (이미 설정됨)
- Python 3 + 기존 dev-base 도구 체인
- 퍼블리싱 템플릿 v2 (`rules_version: 2`) 사용
- Figma MCP 직접 해석 금지 — spec.md 경유만

**비즈니스 제약**
- 드릴 런이므로 실제 고객 deliverable 아님
- 발견된 파이프라인 버그는 수정하지 않고 기록만

## 8. 우선순위 (MoSCoW)

- **Must**: 프로젝트 초기화, spec 생성, AI 구현, 4종 게이트 전체 통과
- **Should**: 수렴 루프 반복 로그, 발견 이슈 리포트
- **Could**: 스크린샷 비교(Playwright), 반복 섹션 componentId 재사용 확인
- **Won't**: Sub 페이지, 모바일 조정, 실 배포

## 9. 의존성

- 선행 필요: 없음 (PLN-010 완료 상태, REQ-040/041/042 커밋 완료)
- 연관: PLN-009/010 (이 plan은 그 결과물을 검증)

## 10. 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| Figma 대용량 노드 트리로 spec 생성 실패 | 중 | 중 | 섹션별 분할 추출, --depth 제한 |
| AI가 spec.md 대신 MCP 직접 해석 시도 | 중 | 상 | 브리프 템플릿 v2의 rule_ids + spec-only 원칙 강조 |
| 수렴 루프 max_iter 초과 | 중 | 중 | PM 수동 개입 지점 명확화, 이슈 리포트로 전환 |
| asset_manifest 누락 이미지 → AI 합성 이미지 삽입 | 낮 | 상 | `asset_manifest_consistency` CRITICAL 게이트 |
| structural-diff hash 불일치 (wrapper 임의 삭제) | 중 | 상 | 구조 불변 원칙 브리프 강조 (REQ-042 주입 완료) |

## 11. Loop 종료 조건

- 기존 검증 통과 (AC 통과 + max_iterations=2)

## 12. 테스트 전략

- 적용 안 함 (드릴 런, 기존 테스트 스위트 대상 아님)
- 최종 산출물 검증은 4종 게이트 + 사용자 시각 검수

## 13. 분리 실행

단일 REQ 로 충분 (gemini-dev 1회 dispatch + 수렴 루프). 세부 task 분해는 `/mst:request` 단계에서 결정.

## 14. Intent (JTBD)

- **When I**: 어제 완성된 Figma 파이프라인(PLN-009/010)이 실전에서 작동하는지 확인하고 싶을 때
- **I want to**: 신규 Figma 소스(디에스솔루션 MAIN)에 전체 파이프라인을 1회 end-to-end 실행해 보고
- **So I can**: 수렴 루프·구조 불변 원칙·4종 게이트가 실제로 기대대로 작동하는지 드릴 런으로 검증하고, 발견된 갭을 후속 PLN 소재로 삼을 수 있다
