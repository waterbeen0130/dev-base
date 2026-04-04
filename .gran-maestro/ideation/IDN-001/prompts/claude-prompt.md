# 유지보수성·스타일 가이드 체계 완성 규칙 제안

당신은 퍼블리싱 규칙 체계의 유지보수성과 확장성을 전문으로 합니다.

## 현재 규칙 체계 현황

- 파일: common.md (공통), codex.md (Codex), CLAUDE.md (Claude), landing.md (Landing)
- JSON: rule_engine.json (기계 규칙), validation_schema.json (검증 스키마)
- 문제: 규칙 중복 (21개 항목 2~4개 파일), override 메커니즘 없음
- 개선 중: project_type 분리 (basic/landing), applies_to 필드 추가

## 제안 요청 영역 (유지보수성/체계)

아래 항목들에 대해 **현재 없지만 규칙 체계를 완성할 추가 규칙**을 제안하세요:

1. **CSS 주석 컨벤션**: 섹션 구분 주석 패턴 (/* ===== section name ===== */ 등), 불필요 주석 금지
2. **파일 내 CSS 구조 순서**: :root → reset → 공통 → 섹션별 → 미디어쿼리 순 강제 여부
3. **클래스명 반복 패턴**: 동일 페이지 내 같은 역할의 섹션이 여러 개일 때 (`main_about`, `main_about_2`)
4. **반응형 이미지 클래스**: `.pc_only`, `.mb_only` 이미지 전환 패턴 표준화
5. **공통 UI 컴포넌트 패턴**: 공통 버튼, 공통 폼, 공통 모달 클래스명 컨벤션
6. **CSS 초기화(reset) 범위**: 어디까지 reset할지 명확한 기준 (box-sizing, margin/padding 0, 폰트 상속 등)
7. **미디어쿼리 중복 방지**: 같은 breakpoint 미디어쿼리를 한 파일 내 1개로 통합 규칙

각 항목에 대해:
- 제안 규칙 내용
- 적용 범위 (basic/landing/공통)
- 기대 효과

응답 형식: 번호 목록, 각 항목 3-4줄, 총 2000자 이내
