<!-- source-mapping: original=AGI-004/objective-qa-session sections=[조사:규칙↔검증 커버리지 매핑, CLAUDE.md 절대금지, rules/common.md] -->
# rule-encoding-gaps (미인코딩 규칙 보강)

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-001, DOD-002, DOD-003, DOD-004, DOD-005

## 개요

CLAUDE.md/rules에 명시된 강제 규칙 95개 중 74개(78%)만 `rules/rules.yaml`+`validation_schema.json`에 인코딩되어 있고, **21개(22%)는 어떤 검증 도구에도 인코딩되지 않았다**. 특히 실제 깨진 결과물의 1순위 위반인 "Figma 노드명 직역 클래스화"가 미인코딩 상태라, 규칙은 존재하나 검증이 잡지 못한다. 이 도메인은 기계 검증 가능(A/B급) 미인코딩 규칙을 인코딩하고, 커버리지 갭을 측정·축소한다.

## 설계 결정

### AD-001: Figma 노드명 직역 클래스 차단 규칙 신설 (`no_figma_nodeid_class`)
- **결정**: Figma 노드명/디자이너 식별자를 그대로 클래스로 박은 패턴을 CRITICAL 위반으로 검출하는 규칙을 신설한다.
- **근거**: 실제 결과물에서 `main_f0`~`main_f175`(프레임), `main_t0`~`main_t61`(텍스트), `main_v0`~`main_v312`(벡터) 294개가 그대로 클래스화됨. CLAUDE.md 절대금지 1순위인데 미검출이었다.
- **대안 검토**: (a) 페이지 prefix 화이트리스트 방식 — 사용자 지정 prefix가 프로젝트마다 달라 유지보수 부담. (b) 노드명 블랙리스트 패턴 방식 — 채택. 노드명은 `{접두}_{단일문자}{연속정수}`(`_f`/`_v`/`_t` + 숫자), `header_b`/`footer_bk`/`sec_{N}`/`box{N}`/`_v{N}` 등 디자이너 식별자 형태가 일관적이라 보수적 정규식으로 식별 가능.
- **영향 범위**: validate-semantic 클래스명 검사 경로, rules.yaml 신규 규칙, 경계 픽스처.

### AD-002: 의미론적 스코핑 규칙 인코딩 (B급, 휴리스틱)
- **결정**: 공통영역 자식 단독선언과 전역 클래스 부모 오염을 검출하는 custom 핸들러를 추가한다.
- **근거**: CLAUDE.md:81-114의 "공통영역 자식은 부모 스코핑 강제(`.header .logo`)" + "전역 클래스(`.header/.footer/.cont/.img_area`)는 부모 없이 단독선언"이 미인코딩. 기존 `generic_class_parent_scope`는 페이지 prefix 섹션만 대상이라 공통영역을 못 다룸.
- **대안 검토**: 완전 자동(AST) vs 휴리스틱. 클래스의 "전역 성질" 판정은 고정 클래스 목록(header/footer/logo/gnb/utils/sns/copyright/container/cont/img_area)으로 화이트리스트화하면 결정론적으로 가능 → 휴리스틱+화이트리스트 채택.

## 상세 명세

### 1. 인코딩 대상 규칙 (A/B급 — 이번 범위)

| 신규/보강 규칙 id | 검출 대상 | 등급 | 1차 심각도 | 출처 |
|---|---|---|---|---|
| `no_figma_nodeid_class` (신규) | `*_f{N}`/`*_v{N}`/`*_t{N}` 연속 인덱스, `header_b`/`footer_bk`/`sec_{N}`/`box{N}`/`_v{N}` 디자이너 식별자 클래스 | A | CRITICAL(픽스처 통과 후 승격) | CLAUDE.md:51 |
| `common_area_child_scope` (신규) | `.logo{}`/`.gnb{}`/`.utils{}`/`.copyright{}`/`.sns{}` 등 공통영역 자식 단독선언 | B | MAJOR | CLAUDE.md:81-95 |
| `global_class_standalone` (신규) | `body .header{}`/`html .cont{}`/`body .img_area{}` 등 전역 클래스에 부모 오염 | A | MAJOR | CLAUDE.md:97-114 |
| `character_segments_respected` (신규) | spec `has_mixed_styles:true`인데 HTML이 구간 분리 span 없음 | B | MAJOR | CLAUDE.md:394-420 |
| `no_deprecated_tools` (신규) | `generate.py`/`json-to-html.py`/`repair-from-violations.py`/`structural-diff.py`/`--converge` 등 폐기 도구 참조·호출 | A(grep) | MAJOR | CLAUDE.md:44-47 |
| `no_guess_prefix` (신규) | `site_`/`g_`/`common_` 등 추측 prefix 클래스 | A | MAJOR | CLAUDE.md:52 |

### 2. `no_figma_nodeid_class` 패턴 정의 (보수적)

- **차단(위반)**: 클래스명이 `^[a-z]+_[fvt][0-9]+$`(예: `main_f0`, `main_v53`, `main_t12`), 또는 `header_b`/`footer_bk`/`sec_[0-9]+`/`box[0-9]+`/`_v[0-9]+` 패턴.
- **통과(정상)**: 사용자 지정 페이지 prefix + 의미 역할명 — `main_intro`, `main_visual`, `greeting_title`, `products_card`. (역할명이 영단어이고 `_f/_v/_t + 숫자` 형태가 아님)
- **경계 사례**: `main_f0`(차단) vs `main_footer`?? → `footer`는 공통영역 단어이므로 `common_area_prefix` 규칙이 별도로 처리. `no_figma_nodeid_class`는 `_f0`처럼 단일문자+숫자 인덱스에만 반응하도록 한정.

### 3. 커버리지 갭 측정 (DOD-005)

- 입력: 95개 규칙 목록(조사 산출물) + rules.yaml 인코딩 현황.
- 산출: "규칙 id ↔ 인코딩 여부 ↔ 등급(A/B/C) ↔ 픽스처 존재 여부" 리포트.
- 목표: A/B급 미인코딩 항목 수를 측정 가능하게 감소시키고, 잔여(주로 C급: 거짓보고/시각판단)는 사유와 함께 리포트로 보존.

### 미인코딩 21개 갭 원본 목록 (조사 결과)

1. 공통영역 자식 부모 스코핑(.header .logo) — B — 본 도메인 `common_area_child_scope`
2. 전역 클래스 단독선언 — A/B — 본 도메인 `global_class_standalone`
3. 텍스트 부분 색상 character_segments — B — 본 도메인 `character_segments_respected`
4. spec byte-exact 텍스트 사용 — B — (기존 `text_byte_exact_required` 일부 커버, 잔여 확인 필요)
5. 자동 코드 생성 스크립트 금지 — A(grep) — 본 도메인 `no_deprecated_tools`
6. 자동 수리 루프(--converge) 금지 — A(grep) — 본 도메인 `no_deprecated_tools`
7. 폐기 도구 참조 금지(10개+) — A(grep) — 본 도메인 `no_deprecated_tools`
8. POLICY-1 적용 금지 — A — (verification-execution / trust-noise와 교차, 잔여 확인)
9. Figma 노드명 클래스 금지 — B — 본 도메인 `no_figma_nodeid_class` (핵심)
10. 추측 prefix 금지(site_/g_/common_) — A — 본 도메인 `no_guess_prefix`
11. PM 검증 통과 후 보고 — A(subprocess) — verification-execution-gate 도메인
12. 거짓 보고 금지 — C — Won't(완전자동화 제외), 게이트로 간접 방어
13. PNG 시각 참조 우선 — C — Out-of-scope
14. 7-Step 워크플로우 준수 — B(로그) — conversion-step-hardening 일부
15. OMX 기본 사용 — A(env) — conversion-step-hardening 일부
16. 요청외 개선 금지 — C — Out-of-scope
17. 과도/한글 주석 금지 — A(grep) — 후순위(잔여 리포트)
18. 불필요 에러처리 금지 — B — 후순위(잔여 리포트)
19. 외주 AI 자가보고 신뢰 금지 — B(로그) — verification-execution-gate 교차
20. 타이포 필드 없는 spec 시작 금지 — A(JSON) — (기존 `spec_typography_required` 커버, 잔여 확인)
21. MCP 폴백 spec 정규 사용 금지 — B(메타) — (기존 `spec_extraction_method_warning` 일부 커버)

## Q&A 보강 사항

- 사용자 결정: 검증 강화 4방향 전부 채택하되, "누락 규칙 인코딩"이 핵심. → 본 도메인이 최우선 Must.
- 사용자 결정: 제천 결과물은 참조도 하지 않음. → 노드명 패턴 픽스처는 제천 파일을 복사하지 않고 합성 예시로 새로 작성(regression-fixtures 도메인).
- 신규 규칙은 false positive 0 확인 전까지 CRITICAL 승격 금지(NFR 오류처리). 단계적 승격(MAJOR→CRITICAL).
