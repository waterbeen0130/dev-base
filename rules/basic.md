# Basic 프로젝트 규칙

> `common.md` 규칙 기본 적용, 아래는 Basic 프로젝트 전용 규칙

---

## Landing과 다른 점

### CSS
- font-size: **PC는 `rem`**, **모바일(768px 이하)은 고정 `px`**
- 기본 폰트 베이스: `html,body{font-size:clamp(14px, 1.2vw, 16px);}`
- padding/margin: 고정 `px` (기본), 100px 이상은 `clamp()` 허용
- 768px 이하: padding/margin은 PC 값의 **절반**

### JS
- **로컬 파일 사용** (CDN 아님)

### reset.css
- **별도 파일** (`@import url("reset.css")`)

---

## 파일 구조

```
project/
├── page/
│   ├── index.html
│   ├── {sub_list}.html
│   └── {sub_view}.html
├── css/
│   ├── reset.css
│   ├── slick.css
│   └── common.css
├── js/
│   ├── jquery-3.7.1.min.js
│   ├── gsap.min.js
│   ├── ScrollTrigger.min.js
│   ├── slick.js
│   └── ui_common.js
└── img/
```

### 기본 포함 파일
```html
<link rel="stylesheet" href="../css/common.css"/>
<script type="text/javascript" src="../js/jquery-3.7.1.min.js" charset="utf-8"></script>
<script type="text/javascript" src="../js/gsap.min.js"></script>
<script type="text/javascript" src="../js/ScrollTrigger.min.js"></script>
<script type="text/javascript" src="../js/slick.js" charset="utf-8"></script>
<script type="text/javascript" src="../js/ui_common.js" charset="utf-8"></script>
```

---

## 서브페이지 공통 구조

### 공통 컴포넌트 (모든 서브페이지 필수)
- `header` — GNB, 로고, 전체메뉴 버튼
- `.total_menu_wrap` — 전체메뉴 (슬라이드 패널)
- `.sub_visual` — 서브비주얼 (배경이미지 + 타이틀)
- `.breadcrumb` — 브레드크럼 (홈 > 1depth > 2depth)
- `.page_title` — 페이지 타이틀 (h3 + 밑줄 장식)
- `footer` — 패밀리사이트, 로고, SNS, 하단정보, 카피라이트

### 새 서브페이지 생성 규칙
1. 기존 프로젝트에 이미 변환된 서브페이지가 있으면 해당 페이지의 공통 컴포넌트를 **그대로 복사**
2. 메뉴 `active`/`select` 상태만 해당 페이지에 맞게 변경
3. 브레드크럼/lnb의 1depth/2depth 텍스트를 해당 페이지에 맞게 변경
4. `body` 태그에 페이지 프리픽스 클래스 `page_{name}`을 **반드시 부여** (파일명과 일치)
5. 콘텐츠 영역의 CSS는 기존 `common.css` 하단에 추가
6. **페이지 1개 완성 후 PM 체크 → 승인 후 다음 페이지 진행** (동시 작업 금지)

### 공통 컴포넌트가 없는 새 프로젝트
- `templates/sub_list.html` 또는 `templates/sub_view.html`을 기본 골격으로 사용
- 피그마의 header/footer 프레임을 기반으로 공통 컴포넌트를 먼저 작성

---

## 서브페이지 타입별 구조

### 리스트 페이지 (`templates/sub_list.html`)
```
.sub_wrap
  .sub_visual
  .navi
  .sub_cont
    .lnb (좌측/상단 로컬 네비게이션, 필요시)
    .page_title
    .{page}_section > .inner
      .tab_menu > .tab_list > a (탭 메뉴, 필요시)
      .list_top (건수 + 검색바, 필요시)
      .{page}_list > .list_row > .list_item (그리드 리스트)
      .list_bottom > .btn_group + .pagination (버튼 + 페이지네이션)
```

### 상세 페이지 (`templates/sub_view.html`)
```
.sub_wrap
  .sub_visual
  .navi
  .sub_cont
    .lnb (좌측/상단 로컬 네비게이션, 필요시)
    .page_title
    .{page}_view > .inner
      .{page}_info_area (이미지 슬라이더 + 정보 테이블)
      .{page}_detail (상세 내용 + 이미지)
      .btn_back (목록으로 버튼)
```

---

## 서브페이지 CSS 네이밍 패턴

### 공통 서브 컴포넌트
| 컴포넌트 | 클래스명 | 용도 |
|----------|----------|------|
| 탭 | `.tab_menu`, `.tab_list` | 카테고리 탭 |
| 검색 | `.search_bar`, `.search_input`, `.select_box` | 검색 영역 |
| 페이지네이션 | `.pagination`, `.btn_page`, `.num` | 페이지 이동 |
| 하단 버튼 | `.list_bottom`, `.btn_group`, `.btn_outline` | 관리 버튼 |
| 뒤로가기 | `.btn_back` | 목록으로 버튼 |

### 페이지별 컴포넌트
| 컴포넌트 | 패턴 | 예시 |
|----------|------|------|
| 섹션 래퍼 | `.{page}_section` | `.portfolio_section` |
| 리스트 | `.{page}_list`, `.list_item`, `.list_row` | `.portfolio_list` |
| 상세 래퍼 | `.{page}_view` | `.portfolio_view` |
| 정보 영역 | `.{page}_info_area` | `.portfolio_info_area` |
| 상세 내용 | `.{page}_detail` | `.portfolio_detail` |

---

## 서브페이지 CSS 기본 패턴

```css
/* tab menu */
.tab_menu{border-bottom:1px solid #e0e0e0;}
.tab_menu .tab_list{display:flex; gap:30px;}
.tab_menu .tab_list a{display:block; padding:10px 0; font-size:1.125rem; font-weight:500; color:#000; position:relative;}
.tab_menu .tab_list a.active::after{content:""; position:absolute; left:0; bottom:-1px; width:100%; height:4px; background-color:var(--point-color-1);}

/* search bar */
.list_top{display:flex; justify-content:space-between; align-items:center; padding:20px 0;}
.list_top .search_bar{display:flex; gap:5px;}
.list_top .select_box button{display:flex; align-items:center; justify-content:space-between; height:45px; padding:0 15px; background:#fff; border:1px solid #e0e0e0; font-size:1rem; font-weight:500; color:#212121; cursor:pointer;}
.list_top .search_input{display:flex; align-items:center; height:45px; border:1px solid #e0e0e0; padding:0 15px; background:#fff;}
.list_top .search_input input{flex:1; border:none; outline:none; font-size:0.9375rem; color:#212121;}

/* pagination */
.pagination{display:flex; align-items:center; justify-content:center;}
.pagination .num{display:flex; align-items:center; justify-content:center; width:30px; height:30px; font-size:0.875rem; font-weight:500; color:#757575;}
.pagination .num.active{color:#212121; font-weight:700; border-bottom:2px solid #212121;}
.pagination .btn_page{display:flex; align-items:center; justify-content:center; width:30px; height:30px; background:none; border:none; cursor:pointer;}

/* list bottom */
.list_bottom{display:flex; flex-direction:column; align-items:center; gap:30px;}
.list_bottom .btn_group{display:flex; gap:8px;}
.btn_outline{height:40px; padding:0 20px; background:#fff; border:1px solid #e0e0e0; font-size:0.9375rem; font-weight:500; color:#616161; cursor:pointer;}
.btn_outline.point{color:var(--point-color-1); border-color:var(--point-color-1);}

/* back button */
.btn_back{display:flex; justify-content:center;}
.btn_back a{display:flex; align-items:center; justify-content:center; width:336px; height:64px; border:1px solid var(--point-color-1); font-size:1.125rem; font-weight:500; color:var(--point-color-1); transition:all 0.3s ease-out;}
.btn_back a:hover{background:var(--point-color-1); color:#fff;}

/* view slider (slick) */
.view_img_area .slick-dots{display:flex !important; gap:10px; justify-content:center; margin-top:20px; padding:0; list-style:none;}
.view_img_area .slick-dots li{margin:0; padding:0;}
.view_img_area .slick-dots li button{display:block; width:10px; height:10px; border-radius:50%; background:#ddd; border:none; cursor:pointer; font-size:0; transition:all 0.3s ease-out;}
.view_img_area .slick-dots li.slick-active button{width:40px; height:15px; border-radius:8px; background:var(--point-color-1);}

/* info table (dl/dt/dd) */
.info_table{background:#fafafa; padding:25px; display:flex; flex-direction:column; gap:15px;}
.info_table dl{display:flex; align-items:center; gap:15px;}
.info_table dt{display:flex; align-items:center; gap:8px; min-width:100px; font-size:1.125rem; font-weight:600; color:#424242; flex-shrink:0;}
.info_table dt .ic_line{display:block; width:3px; height:16px; background:var(--point-color-1);}
.info_table dd{font-size:1.0625rem; font-weight:400; color:#424242; padding-left:15px; border-left:1px solid #bdbdbd;}
```

```css
/* responsive - 960px */
@media screen and (max-width: 960px){
.tab_menu .tab_list a{font-size:16px;}
.list_top{flex-direction:column; gap:15px; align-items:flex-start;}
.list_top .search_bar{width:100%;}
.list_top .select_box button{height:40px; font-size:14px;}
.list_top .search_input{flex:1; height:40px;}
.list_bottom .btn_group{flex-wrap:wrap;}
.btn_outline{height:36px; padding:0 15px; font-size:14px;}
.btn_back a{width:100%; max-width:336px; height:50px; font-size:16px;}
.info_table dt{font-size:16px; min-width:80px;}
.info_table dd{font-size:15px;}
}

/* responsive - 768px */
@media screen and (max-width: 768px){
.info_table dl{flex-direction:column; align-items:flex-start; gap:5px;}
.info_table dd{border-left:none; padding-left:11px;}
}
```
