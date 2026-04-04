# CSS/레이아웃 구현 품질 향상을 위한 추가 규칙 제안

당신은 HTML/CSS 구현 품질을 높이는 규칙을 설계하는 전문가입니다.

## 현재 퍼블리싱 규칙 체계 요약

**HTML**: div+class 기반, figure/main/article 금지, img 래퍼 필수, aria 최소화, alt 간결
**CSS**: 한 줄 셀렉터, 중복 선언 금지, 미디어쿼리 들여쓰기 없음, flexbox only, hex 색상, rem(PC)/px(모바일) font-size, line-height 비율, letter-spacing em, 100px 이상 clamp, snake_case+페이지 prefix
**프로젝트**: Basic(rem, 로컬 JS, reset.css 분리) vs Landing(px all, CDN JS, CSS 최상단 reset)

## 제안 요청 영역 (CSS/레이아웃)

아래 항목들에 대해 **현재 규칙에 없지만 추가하면 코드 품질을 높일 규칙**을 제안하세요:

1. **z-index 관리**: 레이어 체계 정의 방법 (헤더, 모달, 드롭다운, 팝업 등)
2. **overflow 처리 패턴**: 가로 스크롤 방지, text overflow 처리, 스크롤 영역 정의
3. **CSS 변수 체계 확장**: 현재 `--point-color-1`, `--width`, `--padding`만 있는데 색상/타이포/간격 변수 체계화
4. **상태 클래스 네이밍**: active, hover, disabled, error 상태 표현 (`is-*`, `has-*`, `section_on`)
5. **반복 패턴 규칙**: 카드 리스트, 그리드 대체 패턴 (flex + nth-child 활용)
6. **텍스트 오버플로**: 말줄임(...) 처리 패턴 (single-line, multi-line ellipsis)
7. **min-height vs height**: 컨테이너 높이 처리 방식

각 항목에 대해:
- 제안 규칙 내용
- 기존 규칙과의 관계 (보완/새로운/수정)
- rule_engine.json 추가 시 JSON 형식 초안

응답 형식: 번호 목록, 각 항목 3-4줄, 총 2000자 이내
