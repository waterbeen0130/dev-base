# 피그마 → HTML/CSS 퍼블리싱 작업 가이드

> 실제 프로젝트(양평군체육센터)에서 발생한 이슈와 교정 사항을 정리한 가이드.
> 새 프로젝트 시작 시 이 파일을 반드시 읽고 숙지한 후 작업한다.

---

## 1. 작업 전 필수 확인

### 규칙 파일 읽기 (매 세션 시작 시)
- `D:/dev-base/rules/common.md` — 공통 CSS/HTML 규칙
- `D:/dev-base/rules/basic.md` — Basic 프로젝트 전용 (rem/px, 반응형)
- `D:/dev-base/rules/publishing-workflow-guide.md` — 이 파일 (실전 이슈 가이드)

### 피그마 정보 확인
- File Key, Token, 메인 프레임 Node ID
- 사이트맵 프레임에서 메뉴 구조 → 파일명 매핑 (한글 메뉴명 = 파일명)

---

## 2. 절대 하지 말 것 (CRITICAL)

### CSS 관련
- **섹션/컨테이너/이미지의 width, height에 고정 px 사용 금지**
  - width → `%` 비율 (부모 대비 환산. 예: 400/1440 = 27.78%)
  - height → `aspect-ratio` 사용 (예: 1440/700)
  - 허용 대상: padding, margin, gap, border-width, border-radius, font-size **만**
  - 예외: 아이콘, 버튼 등 반복/고정 크기 요소는 고정 px 허용

- **CSS Grid 사용 금지** — flexbox만

- **미디어쿼리 통합 블록 금지** — 각 페이지 PC 스타일 바로 아래에 해당 페이지 반응형 배치
  ```
  /* page — PC styles */
  .page_xxx{...}
  @media (max-width: 960px){.page_xxx{...}}
  @media (max-width: 768px){.page_xxx{...}}

  /* next page — PC styles */
  ```

- **flex 양쪽 영역: 양쪽 모두 % 지정** — `flex:1 + width:고정px` 조합 금지

- **`flex-direction:column`으로 행 묶기 금지** — 2열 배치는 `flex-wrap:wrap` + `width:calc(50% - gap/2)`

### HTML 관련
- **피그마 구조를 임의로 변경/병합 금지** — 피그마 데이터 그대로 추출
- **장식용 이미지에 `<img>` 태그 사용 금지** — CSS `background`로 처리
- **모든 요소에 개별 클래스 부여 금지** — 부모+태그 선택자 우선
- **범용 클래스명 사용 금지** — 반드시 페이지 프리픽스 (예: `instructor_card`, `program_banner`)
- **`<p>` 태그 남용 금지** — 95자 이하/줄바꿈 없는 텍스트는 `<span>` 사용
- **항목 나열형 텍스트는 `<ul><li>` 사용** — `<br><br>`로 분리하지 않음

### 작업 방식
- **피그마 데이터를 기억에서 복원 금지** — 반드시 MCP 호출해서 읽기
- **구조를 "편의상" 단순화 금지** — 피그마 셀이 분리되어 있으면 HTML에서도 분리
- **검증 없이 완료 선언 금지**

---

## 3. Figma MCP 한계 및 대응

### characterStyleOverrides (텍스트 내부 강조/색상)
- **Figma MCP(`get_figma_data`)는 `characterStyleOverrides`/`styleOverrideTable`을 반환하지 않음**
- 텍스트 내부 부분 굵기/색상이 의심될 때 Figma REST API 직접 호출:
  ```bash
  curl -s -H "X-Figma-Token: {TOKEN}" \
    "https://api.figma.com/v1/files/{FILE_KEY}/nodes?ids={NODE_ID}" \
    | python3 -c "
  import json,sys
  data=json.load(sys.stdin)
  node=data['nodes']['{NODE_ID}']['document']
  chars=node.get('characters','')
  overrides=node.get('characterStyleOverrides',[])
  table=node.get('styleOverrideTable',{})
  print(f'text: {chars}')
  print(f'overrides: {overrides}')
  for k,v in table.items():
      fw=v.get('fontWeight','없음')
      fills=v.get('fills',None)
      color='없음'
      if fills:
          c=fills[0].get('color',{})
          r,g,b=int(c.get('r',0)*255),int(c.get('g',0)*255),int(c.get('b',0)*255)
          color=f'#{r:02x}{g:02x}{b:02x}'
      print(f'  override {k}: weight={fw}, color={color}')
  "
  ```
- MCP에서 fontWeight:400으로 보여도 실제로는 부분 강조가 있을 수 있음 → REST API로 반드시 확인

---

## 4. 반응형 처리 규칙

- **768px 한 곳에 몰지 않는다** — 레이아웃 변경 시점에 맞춰 분산
  - 1200px: 5열 → 3열, 4열 → 2열 등 다열 레이아웃 축소
  - 960px: 가로 → 세로 전환, 테이블 세로 배치, 카드 1열
  - 768px: 모바일 폰트 고정px, gap/padding 절반

- **Basic 프로젝트 규칙**:
  - PC: font-size `rem`
  - 모바일(768px 이하): font-size 고정 `px`
  - 768px 이하: padding/margin은 PC 값의 **절반**

---

## 5. 서브페이지 공통 구조

모든 서브페이지는 아래 구조를 공유한다. 첫 페이지에서 확립 후 이후 페이지에서 복사.

```
header (gnb is_active 적용)
total_menu
sub_wrap
  sub_visual (배경 + 브레드크럼 + 타이틀)
  sub_cont (page_title + 콘텐츠)
  related_sites
  footer
```

- 공통 컴포넌트(header/footer/sub_visual/navi)는 기존 코드에서 그대로 복사
- 메뉴 `is_active` 상태만 해당 페이지에 맞게 변경
- CSS는 기존 common.css **하단에 추가** (기존 코드 수정 안 함)

---

## 6. 파일명 규칙

- 메인 페이지: `index.html`
- 서브 페이지: **한글 메뉴명** 그대로 (예: `센터소개.html`, `시설현황.html`)
- CSS 프리픽스: **영문 snake_case** (예: `intro_`, `facility_`, `instructor_`)
- `page_1.html`, `sub_01.html` 같은 의미 없는 파일명 금지

---

## 7. 재사용 가능한 공통 컴포넌트

이미 구현된 패턴을 새 프로젝트에서도 활용:

| 컴포넌트 | CSS 클래스 | 용도 |
|----------|-----------|------|
| 섹션 타이틀 | `.facility_stit` | 아이콘 + 섹션 제목 (Pretendard 600 30px) |
| 정보 테이블 | `.facility_table` | dt(27.78%) + dd(flex:1) 가로 테이블 |
| 번호 리스트 | `.usage_num` + `.usage_rule` | 파란 원형 번호 + 제목 + 설명 |
| 카드 테이블 | `.usage_cards` + `.usage_card` | head(#E6EFF7) + body 카드 배열 |
| 링크 버튼 | `.btn_link` + `.ic_more` | border #2E79BB + 화살표 아이콘 |
| 안내 박스 | `.program_info_box` | dashed border #91B8DB + radius 20px |
| 알림 리스트 | `.program_notice_list` | dot bullet + 항목 나열 |

---

## 8. 작업 순서 (권장)

1. 피그마 사이트맵 프레임 → 메뉴 구조 파악 → 파일명 매핑
2. 서브 비주얼(sub_tle) 프레임 → 공통 구조 확립
3. 첫 번째 서브페이지 구현 → PM 확인
4. 이후 페이지 순차 진행 (1페이지씩 확인)
5. 각 페이지: MCP 데이터 조회 → 이미지 다운로드 → HTML 작성 → CSS 추가 (PC + 반응형) → 확인
