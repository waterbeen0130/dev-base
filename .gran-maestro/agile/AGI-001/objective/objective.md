# Objective — Figma JSON 정규화 엔진 및 시멘틱 변환 파이프라인

## 진행 상태 요약

- AGI-ID: AGI-001
- 상태: active
- Objective 버전: 1
- 생성일: 2026-04-04
- 마지막 갱신: 2026-04-04

---

## JTBD 레이어

- **When I**: Figma MCP로 가져온 JSON 데이터를 AI에게 코드 추출 요청할 때
- **I want to**: JSON을 정규화된 중간 포맷으로 변환하고, 이를 기반으로 시멘틱 HTML/CSS를 생성하고 싶다
- **So I can**: 어떤 피그마 디자인이든 일관된 품질의 코드를 얻고, 후속 수작업 시간을 대폭 줄일 수 있다
- **성공 지표**: 서로 다른 피그마 디자인 3개 이상에서 추출한 결과물이 디자인과 시각적으로 거의 동일하여 사람의 세밀 비교 작업이 불필요한 수준
- **완료 정의**: 정규화 규칙 문서화 + 정규화 엔진 구축 + 시멘틱 변환 레이어 + 품질 검증 완료

---

## 프로젝트 완료 기준 (DoD)

- [ ] DOD-001: Figma JSON의 모든 시각적 속성(레이아웃, 색상, 타이포그래피, 간격, 보더, 이미지)이 정규화된 JSON 중간 포맷으로 손실 없이 변환된다, so that 어떤 AI 모델이 읽어도 동일한 해석이 가능하다.
<!-- dod:DOD-001 status:done priority:must -->
  - Direction: 증가
  - Measure: 속성 변환 커버리지
  - Object: Figma JSON 시각적 속성 전체
  - Context: MCP 응답 → 정규화 엔진 통과 시
  - Target: 100% 속성 매핑 (누락 0건)

- [ ] DOD-002: Figma 속성 → CSS/HTML 변환 규칙이 명확하게 문서화되어 "이 Figma 속성은 이 CSS 값으로 변환된다"를 누구나 조회할 수 있다, so that 변환 로직의 투명성이 확보되고 유지보수가 용이하다.
<!-- dod:DOD-002 status:done priority:must -->
  - Direction: 증가
  - Measure: 문서화된 규칙 수 / 전체 규칙 수
  - Object: 속성 변환 규칙
  - Context: 정규화 엔진의 모든 변환 경로
  - Target: 100% 규칙 문서화

- [ ] DOD-003: basic/landing 프로젝트 타입별 차이(rem vs px, 간격 규칙, 애니메이션 등)가 정규화 단계에서 프로필로 분리 처리된다, so that 프로젝트 타입에 따라 올바른 CSS 값이 자동 적용된다.
<!-- dod:DOD-003 status:done priority:must -->
  - Direction: 감소
  - Measure: 타입 분기로 인한 코드 중복
  - Object: 프로젝트 타입별 변환 규칙
  - Context: basic/landing 프로젝트 구분 시
  - Target: 프로필 설정 파일로 분기 로직 완전 분리

- [ ] DOD-004: 정규화된 중간 포맷을 AI가 읽고 시멘틱 HTML(ul/li, heading 계층, 적절한 태그 선택)/CSS로 변환하는 2차 파이프라인이 동작한다, so that 기계적 추출과 의미 해석이 분리되어 각 단계의 품질을 독립 관리할 수 있다.
<!-- dod:DOD-004 status:done priority:must -->
  - Direction: 증가
  - Measure: 시멘틱 변환 정확도
  - Object: 2차 AI 변환 파이프라인
  - Context: 정규화 JSON → 최종 HTML/CSS 생성 시
  - Target: 시멘틱 태그 선택이 디자인 의도와 일치

- [ ] DOD-005: 서로 다른 3개 이상의 피그마 디자인에서 추출한 결과물이 디자인과 시각적으로 거의 동일하여 사람의 세밀 비교 작업이 불필요한 수준이다, so that 추출 후 수작업 시간이 대폭 절감된다.
<!-- dod:DOD-005 status:done priority:must -->
  - Direction: 감소
  - Measure: 디자인 대비 시각적 차이 건수
  - Object: 최종 HTML/CSS 결과물
  - Context: 서로 다른 피그마 디자인 3개 이상 테스트 시
  - Target: 세밀 비교 작업 불필요 수준 (주요 시각 차이 0건)

- [ ] DOD-006: 기존 validate.js 검증 체계와 정규화 엔진이 연동되어 정규화 결과의 자동 품질 검증이 가능하다, so that 수동 검수 없이도 추출 품질을 보장할 수 있다.
<!-- dod:DOD-006 status:done priority:should -->
  - Direction: 증가
  - Measure: 자동 검증 커버리지
  - Object: 정규화 결과 검증
  - Context: 정규화 완료 후 validate.js 실행 시
  - Target: 기존 67개 검증 규칙과 정규화 엔진 연동 완료

- [ ] DOD-007: 정규화 과정에서 어떤 규칙이 적용됐는지 추적 가능한 로그가 출력된다, so that 문제 발생 시 원인을 빠르게 파악할 수 있다.
<!-- dod:DOD-007 status:done priority:could -->
  - Direction: 증가
  - Measure: 로그 추적 가능 노드 비율
  - Object: 정규화 처리 로그
  - Context: figma-extract.py 실행 시
  - Target: 각 노드별 적용된 규칙 ID 출력

---

## 설계 결정 (Architecture Decisions)

### AD-001: 중간 포맷은 JSON
- 결정: 정규화 출력을 JSON으로 확정
- 근거: 기존 매핑 파일이 JSON이며, AI가 파싱하기에 가장 자연스러운 포맷
- 대안: YAML(가독성 좋으나 파싱 복잡), 마크다운 테이블(기존 figma-extract.py 출력이지만 구조화 한계)

### AD-002: figma-extract.py 전면 재작성 허용
- 결정: 기존 코드 보존보다 더 나은 구조로의 개선에 비중을 둠. 복잡한 병합 로직 포함 전면 재작성 가능
- 근거: 사용자 명시 — "기존 병합 규칙이 복잡하다면 모두 수정해도 상관없어, 더 나은 방향으로 개선함에 더 비중을 크게 둬"
- 영향: 기존 figma-extract.py의 하위 호환성 유지 불필요

### AD-003: 2단계 파이프라인 아키텍처
- 결정: 1차 기계적 정규화(규칙 기반) → 2차 AI 시멘틱 변환
- 근거: AI 해석 편차의 원인이 raw JSON 해석에 있으므로, 값 확정(1차)과 의미 부여(2차)를 분리
- 영향: 1차 결과물만으로도 값의 정확성 검증 가능

### AD-004: MCP 파이프라인 유지
- 결정: Figma MCP + stdin 파이프 방식 유지
- 근거: MCP/REST API/수동복사 모두 동일 JSON 반환. MCP가 Claude 워크플로우에 가장 자연스러움
- 영향: API 변경 시 정규화 엔진의 입력 매핑만 수정하면 됨

---

## 제약사항 (Out-of-scope / 기술 / 비즈니스)

### Out-of-scope
- Figma MCP 자체 수정 (외부 의존)
- 디자인 시스템/컴포넌트 라이브러리 생성
- 백엔드 연동이나 빌드 시스템

### 기술적 제약
- 프로젝트 타입별 분기(basic: rem, landing: px)가 정규화 단계에 포함되어야 함
- Figma MCP 응답 구조에 의존 (현실적 리스크 매우 낮음)

### 비즈니스 제약
- 마감 기한 없음 — 품질이 만족될 때까지 진행

---

## 우선순위 (MoSCoW)

### Must
- 정규화 엔진 구축 (DOD-001)
- 변환 규칙 문서화 (DOD-002)
- 프로젝트 타입 프로필 분리 (DOD-003)
- 시멘틱 변환 파이프라인 (DOD-004)
- 디자인 동일 품질 달성 (DOD-005)

### Should
- validate.js 검증 연동 (DOD-006)

### Could
- 정규화 로그 추적 (DOD-007)

### Won't (this time)
- 디자인 시스템 생성
- 프로젝트 타입 자동 감지

---

## 프로젝트 NFR

- 성능: 단일 섹션 정규화 처리 시간 합리적 수준 (사용자 체감 대기 없음)
- 호환성: basic + landing 프로젝트 타입 모두 지원
- 오류 처리: 알 수 없는 Figma 속성은 경고 로그 출력 후 skip (실패 중단 방지)

---

## 리스크 레지스터

| ID | 리스크 | 가능성 | 영향 | 완화 방안 |
|----|--------|--------|------|-----------|
| R-001 | characterStyleOverrides 재작성 시 edge case 발생 | 중 | 중 | 다양한 텍스트 스타일 조합으로 테스트 케이스 확보 |
| R-002 | 프로젝트 타입별 분기점 증가로 복잡도 상승 | 중 | 낮 | 프로필 설정 파일로 분리하여 엔진 코드와 규칙 분리 |
| R-003 | 2차 AI 시멘틱 변환에서 여전히 편차 발생 | 중 | 중 | 정규화된 중간 포맷이 충분히 구조화되면 AI 판단 범위 최소화 |

---

## 참조 레퍼런스

- 기존 figma-extract.py: `/mnt/d/dev-base/tools/figma-extract.py` (34.2KB)
- 기존 validate.js: `/mnt/d/dev-base/tools/validate.js` (5.4KB)
- Figma 검증 체크: `/mnt/d/dev-base/tools/checks/figma-checks.js` (24KB)
- 규칙 엔진: `/mnt/d/dev-base/rules/rule_engine.json` (21.4KB)
- 검증 스키마: `/mnt/d/dev-base/rules/validation_schema.json` (7.2KB)
- 공통 규칙: `/mnt/d/dev-base/rules/common.md` (31.6KB)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1 | 2026-04-04 | 초기 objective 생성 |

---

## 상세 문서 (Details)

- [정규화 엔진](details/normalization-engine.md) — figma-extract.py 재설계, JSON 중간 포맷 스키마, 전체 속성 변환 규칙
- [시멘틱 변환](details/semantic-transform.md) — 2차 AI 파이프라인, 시멘틱 마크업 판단 기준, 태그 선택 규칙
- [검증 연동](details/validation-integration.md) — validate.js 연동, 정규화 결과 자동 검증, 로그 추적
