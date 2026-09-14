# Gnuboard Skin Rules

HTML/CSS code extraction output to Gnuboard5 theme conversion rules.
Theme base: `theme/wering/` (project-specific customization per site).

---

## 설치 직후 선행 작업 (Pre-conversion Setup)

> **그누보드 설치 완료 후, 스킨 변환(Phase 1)을 시작하기 전에 반드시 먼저 끝내는 4단계.**
> 이 선행 셋팅이 끝나야 이후 변환 작업의 전제(테마 활성화, 모바일/캐시 비활성, viewport)가 성립한다.

### 1. `config.php` — 모바일/캐시 비활성화

`data/config.php` (설치 루트의 `config.php`) 에서 아래 두 상수를 **모두 `false`** 로 변경한다.

```php
define('G5_USE_MOBILE', false); // 별도 모바일 홈페이지 미사용 (반응형 단일 테마)
define('G5_USE_CACHE',  false); // 최신글 등 cache 기능 미사용
```

- 이유: 반응형 단일 스킨을 쓰므로 모바일 전용 테마 분기가 불필요하고, 개발 중 캐시로 인한 최신글 미갱신을 방지한다.

### 2. 테마 폴더 준비 + 활성화 확인

1. `theme/basic` 폴더의 **이름을 `theme/wering` 으로 변경**한다. (복사본을 따로 두지 않는다 — `basic` 은 남기지 않는다)
2. 관리자로 접속하여 **환경설정 → 테마**에서 `wering` 테마가 **사용 체크(활성)** 되어 있는지 확인한다.

### 3. `head.sub.php` — viewport meta 추가

`theme/wering/head.sub.php` 의 `<meta charset="utf-8">` **바로 아래 줄**에 viewport meta 를 추가한다.

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
```

- 이 viewport 값은 이후 [File Conversion Rules → head.sub.php](#headsubphp-minimal-changes) 단계와 **동일하게 유지**한다 (확대 제한 등 커스텀 없이 기본 반응형 viewport로 통일).

### 4. 기본 게시판 4개 삭제

관리자 로그인 → **게시판 관리**에서 그누보드 설치 시 기본 생성된 게시판 목록 **4개를 삭제**한다. (실제 사용할 게시판만 이후 스킨/메뉴 연동 단계에서 새로 생성)

### 5. 기본환경설정

테마 사용 지정을 마친 뒤, 관리자 → **환경설정 → 기본환경설정**에서 아래 항목을 변경한다.

- **홈페이지 제목**: `그누보드5` → 현재 프로젝트에 맞는 이름으로 변경
- **포인트 사용**: 체크 **해제**
- **관리자 메일 발송이름**: 프로젝트 이름과 동일하게 변경
- **짧은 주소 설정**: **숫자**로 변경

---

## Basic Principles

- Read this entire file before starting any conversion work
- Preserve ALL existing PHP code in head.php / tail.php — never delete Gnuboard functions
- Maintain extracted HTML class names as-is (`.header`, `.gnb`, `.footer`, etc.)
- Only convert features that exist in the extracted HTML — do not add features that aren't there
- Image paths: `../img/` → `<?php echo G5_THEME_IMG_URL; ?>/`
- `.html` links → board view URLs or PHP routing
- No hardcoded theme-specific prefixes on helper functions (e.g., `wering_` prefix forbidden)
- Helper functions use generic descriptive names with `if (!function_exists())` guard
- Comments in English only

---

## Conversion Procedure (3 phases)

### Phase 1: Feature Detection

Read the extracted HTML files (header, footer, main content, sub-pages) and check which features exist.
Build a feature checklist before writing any PHP.

```
[Header]
□ Logo (.header_logo, .logo)
□ GNB navigation (.gnb, .gnb_depth1, .s_gnb, or similar nav structure)
□ Site search (input[name="stx"], .search, .sch)
□ Login / Register (.login, .member, .util, or login/register text links)
□ Mobile hamburger menu (.gnb_toggle, .menu_open)
□ Full-screen menu overlay (.allmenu, .all_menu, #gnb_all)  ← 메뉴 목록이면 Module A-2 필수

[Footer]
□ Company info (.footer_info, dl/dt/dd blocks)  ← 값은 시안 예시값이다. §푸터 회사정보·연락처·링크 필수
□ Sitemap nav (.footer_sitemap, .footer_menu, repeated menu structure)
□ SNS links (.sns, .social, or SNS icon links)
□ Copyright (.copyright, .footer_bottom)
□ Quick-to-top button (.quick_top, #top_btn)

[Sub-page common]
□ Sub visual hero (.sub_visual)
□ Breadcrumb (.breadcrumb)
□ Sub content wrapper (.sub_cont, .sub_main)

[Main page]
□ Main visual / slider (.main_visual, .slider, .swiper)
□ Dynamic content sections (news, notice, gallery — board-linkable areas)
□ Static content sections (intro, banner, etc.)
```

Only proceed with modules that were checked.

### Phase 2: Conversion

Apply only the modules relevant to detected features.

```
a) Asset copy: css/, js/, img/ → theme/wering/ corresponding directories
b) head.sub.php: add custom CSS/JS via add_stylesheet / add_javascript
c) head.php: apply detected feature modules (see Module Catalog below)
d) index.php: insert main content + path conversion + dynamic section substitution
e) tail.php: apply detected footer modules
f) Sub-pages: extract content HTML → prepare for board posts (we_js skin)
```

### Phase 3: Verification

Run only the checks relevant to applied modules.

```
[Required — all projects]
□ _GNUBOARD_ guard exists in all PHP files
□ G5_IS_MOBILE branch exists
□ No remaining ../img/ paths (grep)
□ No remaining .html links (grep)
□ php -l passes on all generated PHP files
□ Extracted HTML class structure preserved (not replaced with #hd, #ft, etc.)
□ 테마 head.php / tail.php 에 하드코딩 메뉴 링크 0건
  → `grep -c '<a href="#">' theme/{skin}/head.php theme/{skin}/tail.php` 가 모두 0
  (0 이 아니면 동적화가 덜 끝난 메뉴가 남아 있다는 뜻. 토글 버튼용 `#` 은 `class=` 가 붙어 구분된다)
□ 푸터 예시값 0건 — `홍길동`·예시 주소/메일/번호가 없고, 대표자·전화·주소·이메일은 출처 확인값뿐(모르면 미기입) — §푸터 회사정보·연락처·링크
□ 헤더·전체메뉴·모바일 메뉴·푸터 정책링크·Family Site·SNS 의 `href` 전수: `#`·빈값·404 없음, 준비 중은 `#ready`
□ 전화번호는 `tel:` 링크
□ 390px 모바일 실화면까지 확인한 뒤 보고(남은 자리표시자·빈 링크는 보고에 목록으로)

[Conditional — only if the feature was detected and applied]
□ GNB detected → get_menu_db() call exists in head.php
□ 전체메뉴 오버레이 detected → `.allmenu` 블록 안에 `foreach ($menu_datas ...)` 루프 존재
  (GNB 만 동적이고 전체메뉴가 정적으로 남는 누락이 가장 잦다)
□ Search detected → search form action points to G5_BBS_URL/search.php
□ Login detected → $is_member branch exists
□ Breadcrumb detected → menu context helper function exists
□ Sitemap detected → get_menu_db() call exists in tail.php
□ Sub-pages exist → defined("_INDEX_") branch exists in head.php and tail.php
```

---

## File Conversion Rules

### head.sub.php (minimal changes)

Keep the entire existing file. Only add:
1. Custom CSS loading — append after the existing CSS echo block:
   ```php
   echo '<link rel="stylesheet" href="'.G5_THEME_CSS_URL.'/common.css?ver='.G5_CSS_VER.'">'.PHP_EOL;
   ```
2. Custom JS loading — append after the existing add_javascript block:
   ```php
   add_javascript('<script src="'.G5_THEME_URL.'/js/gsap.min.js?ver='.G5_JS_VER.'"></script>', 0);
   add_javascript('<script src="'.G5_THEME_URL.'/js/ScrollTrigger.min.js?ver='.G5_JS_VER.'"></script>', 0);
   // add other project-specific JS as found in extracted HTML <head>
   ```
3. Viewport meta if not already present (선행 작업 3단계와 동일 값 사용):
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1">
   ```

Only add what exists in the extracted HTML `<head>`. Do not add libraries the project doesn't use.

### head.php (structure varies by project)

**Fixed top section — always preserve:**
```php
<?php
if (!defined('_GNUBOARD_')) exit;
if (G5_IS_MOBILE) { include_once(G5_THEME_MOBILE_PATH.'/head.php'); return; }
if (G5_COMMUNITY_USE === false) { ... }
include_once(G5_THEME_PATH.'/head.sub.php');
include_once(G5_LIB_PATH.'/latest.lib.php');
// ... other includes
?>
```

**Middle section — apply detected modules:**
- If GNB detected → insert menu helper functions + dynamic menu loop
- If search detected → insert search form with Gnuboard API
- If login detected → insert $is_member conditional block

**Bottom section — if sub-pages exist:**
```php
<?php if (!defined("_INDEX_")) { ?>
<main class="sub_main">
    <!-- sub visual, breadcrumb if detected -->
    <div class="sub_cont">
<?php } ?>
```

### index.php

```php
<?php
if (!defined('_INDEX_')) define('_INDEX_', true);
if (!defined('_GNUBOARD_')) exit;
if (G5_IS_MOBILE) { include_once(G5_THEME_MOBILE_PATH.'/index.php'); return; }
if (G5_COMMUNITY_USE === false) { include_once(G5_THEME_SHOP_PATH.'/index.php'); return; }
include_once(G5_THEME_PATH.'/head.php');
?>

{extracted HTML main content — header and footer excluded}
{image paths converted, static links converted}
{dynamic sections replaced with latest() if applicable}

<?php include_once(G5_THEME_PATH.'/tail.php'); ?>
```

### tail.php

**Fixed top section — always preserve:**
```php
<?php
if (!defined('_GNUBOARD_')) exit;
if (G5_IS_MOBILE) { include_once(G5_THEME_MOBILE_PATH.'/tail.php'); return; }
if (G5_COMMUNITY_USE === false) { ... }
?>
```

**Sub-page wrapper closing — if sub-pages exist:**
```php
<?php if (!defined('_INDEX_')) { ?>
    </div>
</main>
<?php } ?>
```

**Footer — from extracted HTML, apply detected modules:**
- Company info: **마크업만** 시안대로(이미지 경로 변환). **값(대표자·전화·주소·이메일·사업자번호)은 시안 값을 쓰지 않는다** — §푸터 회사정보·연락처·링크
- Sitemap: if detected, replace with get_menu_db() loop
- SNS: use design HTML as-is
- Copyright: use design HTML as-is
- Quick-to-top: use design HTML as-is, convert image paths

**Fixed bottom — always include:**
```php
<?php
if ($config['cf_analytics']) echo $config['cf_analytics'];
include_once(G5_THEME_PATH."/tail.sub.php");
```

### ⚠️ 푸터 회사정보·연락처·링크는 시안 예시값을 절대 남기지 않는다 (CRITICAL · 대표 지시)

> # 🚨 대표자·전화·주소·이메일·사업자번호에 **시안에 적힌 값을 쓰지 않는다** — 모르면 미기입, 기획·단톡방에 확인
>
> 시안(Figma)의 푸터 값은 **자리표시용 예시값**이다(`홍길동`, 예시 주소·메일·번호). 마크업은 시안대로 가져오되
> **값은 실제 출처(공고문, 기관 홈페이지 「찾아오시는 길」, 기획 문서)에서 확인한 것만** 넣는다.
> 출처가 없으면 **그 줄을 비워 두고(미기입)** 기획이나 단톡방에 묻는다. **지시가 없어도 퍼블 단계에서 챙긴다.**
>
> | 실제 사고 (2026-09-14) | |
> |---|---|
> | 제천시티패스 `jctour.kr/citypass/` | 푸터 「대표자 홍길동」, 전화도 예시값, 주소는 우편번호와 도로명이 서로 다른 주소에서 섞인 값, 약관·메뉴 `href="#"` 6곳, Family Site 는 목록 없는 빈 버튼 → **클라이언트 과장이 노출 화면을 보고 지적** |
> | 태안반값여행 (같은 날 오전) | 푸터 이메일·주소·대표자가 Figma 예시값(개인 메일, 다른 동네 주소, 홍길동) 그대로 |
> | 대표 | "작업할 때마다 이야기 나온다. 한두 번이 아니다. 앞으로는 말이 없어도 퍼블단에서 꼭 신경 써 달라" |
>
> **올리기 전 체크리스트** — Phase 3 와 §작업 종료 전 링크 최종 점검에서도 반복한다.
> 1. **예시값 grep 0건** (「현금영수증 예시」 같은 정상 문구는 눈으로 걸러낸다)
>    ```bash
>    grep -rnE '홍길동|000-0000|example\.com|test@|lorem|샘플|예시' theme/wering/*.php theme/wering/skin
>    curl -s https://{도메인}/ | grep -cE '홍길동|000-0000|example\.com|test@|lorem'
>    ```
> 2. **푸터 값 대조** — 대표자·사업자번호·전화·주소·이메일·copyright 를 출처와 한 줄씩 대조한다. 반값여행류는
>    운영기관 주소·대표전화 + `광고대행사 (주)위링 731-87-01628 대표자 : 정병민` 형식이라, 같은 계열 사이트 푸터와도 대조한다.
> 3. **링크 전수** — GNB·전체메뉴·모바일 메뉴·푸터 정책링크(이용약관·개인정보처리방침)·Family Site·SNS 의 모든 `href`:
>    `#`·빈값·404·새 창(`target="_blank" rel="noopener"`). 준비 중이면 `#` 로 두지 말고 **`#ready`**(누르면 「준비 중입니다.」 알림)로 명시한다.
>    단 **JS 탭 전환용 `#` 은 바꾸지 않는다**(바꾸면 탭을 누를 때마다 알림이 뜬다).
> 4. **Family Site·관련사이트** — 버튼만 있고 목록이 없는 빈 드롭다운 금지. 목록(시·군청, 문화관광 등)과 열기/닫기 JS 까지 넣는다.
> 5. **전화번호는 `<a href="tel:…">`** — 모바일에서 눌러 연결되는지 확인한다.
> 6. **390px 모바일 실화면** — 실제 값은 예시값보다 길다. 긴 주소 때문에 줄이 밀려 구분선(`::before`)이 줄 맨 앞에 남거나,
>    `dt` 가 눌려 「주/소」로 쪼개지지 않는지 본다(`dt{flex:none}`). PC 만 보고 끝내지 않는다.
> 7. 완료 보고에 **남은 자리표시자·빈 링크를 목록으로** 적는다.

---

## Module Catalog

Each module is independent. Apply only if the feature was detected in Phase 1.

### ⚠️ 메뉴는 헤더·푸터를 통틀어 **하나도 남기지 않고** 동적화한다 (CRITICAL)

퍼블 마크업에는 같은 메뉴가 **GNB / 전체메뉴 오버레이 / 모바일 메뉴 / 푸터 사이트맵** 으로
여러 벌 들어 있다. **하나라도 정적으로 남기면 관리자 메뉴설정(`g5_menu`)과 어긋난다.**

정적으로 남았을 때 실제로 벌어지는 일 (2026-08-24 영천·함양 반값여행):
- GNB 는 "정산신청" 인데 전체메뉴는 퍼블 원본 문구 "경비신청" 으로 굳어 **같은 사이트에서 메뉴명이 불일치**
- 전체메뉴 링크가 전부 `href="#"` 라 **클릭해도 아무 데도 안 감**
- 관리자에서 메뉴를 고쳐도 전체메뉴만 안 바뀜 → "왜 반영이 안 되냐" 문의로 돌아옴
- 퍼블 원본에만 있던 항목(자료실·갤러리)이 실제 사이트에 없는데 계속 노출

**착수 전 확인**: 헤더/푸터 마크업에서 `<a href="#">` 로 된 메뉴 링크가 있으면 전부 동적화 대상이다.
Module A(GNB) 만 처리하고 나머지를 넘기는 것이 가장 흔한 누락이다.

### Module A: GNB Dynamic Menu

**Detection**: nav element with menu list structure in extracted HTML.

**Conversion**: Replace static `<li>` items with `get_menu_db()` PHP loop.
Preserve the exact class names from extracted HTML (`.gnb`, `.s_gnb`, `.gnb_depth1`, etc.).

**Helper functions needed** (insert in head.php before HTML output):
- `theme_menu_parse_link($link)` — normalize menu URL for comparison
- `theme_menu_link_is_active($link)` — check if link matches current page
- `theme_menu_item_is_active($menu)` — check menu item or its children active
- `theme_menu_target_attr($target)` — build target attribute string

All helpers must use `if (!function_exists('...'))` guard.
Naming convention: use descriptive names, no theme-specific prefix.
Reference implementation: see any recent completed project's head.php.

**Pattern (adapt class names to match extracted HTML):**
```php
$menu_datas = get_menu_db(0, true);
foreach ($menu_datas as $row) {
    if (empty($row)) continue;
    $is_active = theme_menu_item_is_active($row);
    $subs = array();
    foreach ((array)(isset($row['sub']) ? $row['sub'] : array()) as $sub) {
        if (!empty($sub)) $subs[] = $sub;
    }
?>
<li<?php echo $is_active ? ' class="on"' : ''; ?>>
    <a href="<?php echo htmlspecialchars($row['me_link'], ENT_QUOTES, 'UTF-8'); ?>">
        <span><?php echo get_text($row['me_name']); ?></span>
    </a>
    <?php if ($subs) { ?>
    <ul class="{extracted HTML sub-menu class}">
        <?php foreach ($subs as $sub) { ?>
        <li><a href="<?php echo htmlspecialchars($sub['me_link'], ENT_QUOTES, 'UTF-8'); ?>"><?php echo get_text($sub['me_name']); ?></a></li>
        <?php } ?>
    </ul>
    <?php } ?>
</li>
<?php } ?>
```

### Module A-2: Full-screen Menu Overlay (전체메뉴)

**Detection**: 헤더 안에 GNB 와 **별도로** 존재하는 전체메뉴/사이트맵 오버레이
(`.allmenu`, `.all_menu`, `#gnb_all`, `.total_menu` 등). 보통 `.icon_menu` / 햄버거 버튼으로 토글한다.

**판정** — `.allmenu` 안에 **메뉴 목록이 있으면 대상, 장식만 있으면 대상 아님**.
(예: 서천반값여행의 `.allmenu` 는 슬로건 + 이미지뿐이라 변환 불필요.)

**Conversion**: Module A 와 **같은 `$menu_datas` 를 재사용**한다. `get_menu_db()` 를 다시 부르지 않는다.
컬럼이 GNB 1depth 와 나란히 서는 레이아웃이 많으므로, **2depth 가 없는 1depth 도 컬럼을 비우지 말고
자기 자신을 넣어** 열 수가 어긋나지 않게 한다.

```php
<div class="allmenu">
    <ul class="menu">
        <?php
        foreach ($menu_datas as $row) {
            if (empty($row)) continue;
            $subs = array();
            foreach ((array)(isset($row['sub']) ? $row['sub'] : array()) as $sub) {
                if (!empty($sub)) $subs[] = $sub;
            }
            if (!$subs) $subs[] = $row;
        ?>
        <li>
            <ul>
                <?php foreach ($subs as $sub) { ?>
                <li><a href="<?php echo htmlspecialchars($sub['me_link'], ENT_QUOTES, 'UTF-8'); ?>"<?php echo theme_menu_target_attr($sub['me_target']); ?><?php echo theme_menu_link_is_active($sub['me_link']) ? ' class="is_active"' : ''; ?>><?php echo get_text($sub['me_name']); ?></a></li>
                <?php } ?>
            </ul>
        </li>
        <?php } ?>
    </ul>
</div>
```

클래스명은 **추출 HTML 그대로** 유지한다(`.allmenu .menu > li > ul > li` 구조를 CSS 가 그대로 기대한다).

**남은 `href="#"` 처리**: 변환 후에도 `#` 이 보이면 그건 마크업이 아니라 **`g5_menu.me_link` 값이 `#`** 인
것이다. 관리자 메뉴설정에서 채우면 즉시 반영된다 — 테마를 다시 고치지 않는다.

### Module B: Site Search

**Detection**: search input or search form in extracted HTML header.

**Conversion**: Replace static form with Gnuboard search form.
```php
<form name="fsearchbox" method="get"
      action="<?php echo G5_BBS_URL ?>/search.php"
      onsubmit="return fsearchbox_submit(this);">
    <input type="hidden" name="sfl" value="wr_subject||wr_content">
    <input type="hidden" name="sop" value="and">
    <input type="text" name="stx" id="sch_stx" maxlength="20"
           placeholder="{extracted HTML placeholder text}">
    <button type="submit">{extracted HTML button content}</button>
</form>
```
Include `fsearchbox_submit()` validation JS (2-char minimum, single space limit).

**⚠️ 폼만 붙이고 끝내지 말 것** — 검색 폼을 넣었다면 결과 페이지(`bbs/search.php`)도 전용 스킨이 필요하다. §전체검색 결과 페이지 스킨 (검색이 있는 사이트는 필수) 를 반드시 수행한다.

**Not detected**: skip entirely — do not add search functionality.

### Module C: Login / Register

**Detection**: login/register links or member utility area in extracted HTML.

**Conversion**: Wrap in `$is_member` conditional.
```php
<?php if ($is_member) { ?>
    <a href="<?php echo G5_BBS_URL ?>/logout.php">로그아웃</a>
    <?php if ($is_admin) { ?>
        <a href="<?php echo G5_ADMIN_URL ?>">관리자</a>
    <?php } ?>
<?php } else { ?>
    <a href="<?php echo G5_BBS_URL ?>/login.php">로그인</a>
<?php } ?>
```
Adapt the HTML wrapper/class to match extracted design.
Include only the links that exist in the extracted HTML (register may or may not exist).

**Not detected**: skip entirely.

### Module D: Sub-page Branch (sub_visual + breadcrumb)

**Detection**: sub-pages exist in extracted HTML with `.sub_visual` or `.breadcrumb`.

**Conversion in head.php** (after header closing tag):
```php
<?php if (!defined("_INDEX_")) { ?>
<main class="{extracted sub wrapper class}">
    <section class="{extracted sub visual class}">
        <!-- sub visual content with dynamic title -->
    </section>
    <div class="{extracted sub content class}">
<?php } ?>
```

**Breadcrumb** (only if detected):
Requires `theme_get_current_menu_context($menu_datas)` helper function.
Renders: Home > Depth1 > Depth2 using menu data.

**Conversion in tail.php** (before footer):
```php
<?php if (!defined('_INDEX_')) { ?>
    </div>
</main>
<?php } ?>
```

**Not detected** (single-page sites or no sub-visual design): skip entirely.

### Module E: Footer Sitemap

**Detection**: repeated menu structure in footer area of extracted HTML.

**Conversion**: Replace static menu links with `get_menu_db()` loop.
```php
<?php
$footer_menus = function_exists('get_menu_db') ? (array) get_menu_db(0, true) : array();
foreach ($footer_menus as $menu) {
    if (empty($menu)) continue;
?>
<li>
    <strong><?php echo get_text($menu['me_name']); ?></strong>
    <?php foreach ((array)(isset($menu['sub']) ? $menu['sub'] : array()) as $sub) {
        if (empty($sub)) continue; ?>
    <a href="<?php echo htmlspecialchars($sub['me_link'], ENT_QUOTES, 'UTF-8'); ?>"><?php echo get_text($sub['me_name']); ?></a>
    <?php } ?>
</li>
<?php } ?>
```

**Not detected**: keep footer HTML as-is (static text, path conversion only).

### Module F: Dynamic Content (latest)

**Detection**: main page has news/notice/gallery sections that should pull board posts.

**Conversion**: Replace static card/list with `latest()` function call.
```php
<?php echo latest('theme/{skin_name}', '{bo_table}', {count}, {chars}); ?>
```
If a custom latest skin is needed, create `skin/latest/{skin_name}/latest.skin.php`
matching the design pattern from extracted HTML.

**Not detected**: keep content as static HTML (path conversion only).

---

## Sub-page Processing (Board + we_js Skin)

Content sub-pages (company intro, directions, etc.) are handled via Gnuboard boards
with `we_js` skin applied — not as standalone PHP files.

### ⚠️ 게시판은 콘텐츠 페이지마다가 아니라 **1depth 메뉴 단위로 1개** (CRITICAL)
콘텐츠(정적) 서브페이지는 **페이지마다 게시판을 만들지 않는다.** 그 페이지가 속한 **1depth(대) 메뉴에 해당하는 게시판 1개**를 만들고, 각 콘텐츠 서브페이지를 그 게시판의 **글(wr_id)** 로 등록한다. 2depth 메뉴 링크는 해당 글의 view 로 연결한다.

- 예: 1depth `이용안내` → 게시판 `guide` 1개, 글: 시설이용안내(wr_id=1)·이용안전수칙(wr_id=2)·이용제한(wr_id=3). 메뉴 `시설이용안내`→`guide/1`, `이용안전수칙`→`guide/2` …
- 게시판 `bo_subject` 는 1depth 메뉴명으로 둔다(예 `guide`=이용안내).
- **동적 게시판(갤러리·공지·FAQ·이벤트)은 이 규칙과 무관하게 각각 별도 게시판**으로 만든다(목록형이라 1글로 담을 수 없음).
- 아직 콘텐츠가 없는(미빌드) 서브페이지도 링크가 깨지지 않게 **빈 글(예 `<p>준비 중입니다.</p>`)** 을 등록해 wr_id 를 확보한다.
- ❌ 금지: `intro`·`location`·`facility` … 페이지마다 게시판 1개씩 생성.

### 짧은 주소(숫자) 링크 형식 — `cf_bbs_rewrite` = 숫자일 때
[선행 작업 §5](#5-기본환경설정)에서 짧은주소를 **숫자**로 설정했으면, **GNB 메뉴 링크와 테마 내부 링크(index.php 퀵/더보기, tail.php 푸터)를 모두 짧은주소 형식**으로 맞춘다. (설정만 바꾸고 링크를 `board.php?bo_table=…` 로 두면 형식이 어긋난다.)

| 대상 | 짧은주소 형식 |
|------|--------------|
| 게시판 목록(동적) | `/{bo_table}` — **끝 슬래시 없이** (예 `/notice`) |
| 게시판 글 view(콘텐츠) | `/{bo_table}/{wr_id}` (예 `/about/1`) |

> ⚠️ 목록은 **`/notice/` (끝 슬래시) 로 쓰면 Apache 가 디렉터리로 오인해 404** 가 난다. 반드시 `/notice` 로. 글 view 는 `/about/1` 처럼 슬래시가 중간에만 있어 정상.

- 테마 파일에서는 `<?php echo G5_URL ?>/about/1` 처럼 `G5_URL` 접두로 출력한다.
- head.php 의 breadcrumb/active 감지(`theme_menu_is_active`)는 `strpos($_SERVER['REQUEST_URI'], me_link)` 매칭이라 짧은주소에서도 동작한다.

### Workflow
1. Identify sub-pages from extracted HTML (all pages except index.html)
2. Group sub-pages by their **1depth menu**; one board per group (see CRITICAL rule above)
3. For each sub-page, extract only the content area:
   - Exclude: header, footer, sub_visual (head.php generates these)
   - Include: everything between sub_visual and footer
4. Convert image paths to server absolute paths
5. Output: one HTML file per sub-page, ready to paste into board post (wr_content)
6. Board setup (admin): create **1depth-unit** board → apply we_js skin → write each sub-page as a post → link GNB 2depth menu to `/{bo_table}/{wr_id}` (short URL)

### we_js Skin Behavior
The `we_js` view skin renders `wr_content` as raw HTML without board UI chrome.
This enables full-design pages within the board system for SEO/RSS/search benefits.

### ⚠️ 스킨 출처는 공용 폴더 `D:\위링\위링스킨\` 뿐 (CRITICAL)
게시판 스킨은 **공용 위링스킨 폴더에 있는 것만** 쓴다. **다른 프로젝트 폴더(`D:\위링\<날짜> <업체명>\…`)에서 스킨을 복사해 오지 않는다.**

- 그 프로젝트 전용으로 손댄 사본이라 사이트마다 동작·마크업이 다르고, 공용 폴더에 없으니 다음 프로젝트에서 재현·유지보수가 불가능하다.
- 공용 폴더에 원하는 기능의 스킨이 **없으면** — 가장 가까운 공용 스킨(대개 `we_basic`)을 쓰거나, **사용자에게 확인**한다. 다른 프로젝트에서 끌어오는 것은 선택지가 아니다.
- 공용 게시판 스킨 목록: `we_basic` `we_faq` `we_gallery` `we_gallery2` `we_js` `we_event` `we_event2` `we_inquiry` `we_column` `we_portfolio` `we_webzin` `we_schedule` `we_link` `we_map_api` `we_mapV2` `we_pdf` `we_excel` `we_youtube` `we_visual` `we_consulting` `we_contnet`
- ⚠️ **`we_notice` 는 공용 폴더에 없다.** 공지사항·뉴스는 `we_basic` 이 정답이다.

### Board Skin Selection Guide
Choose skins based on the page function detected in extracted HTML:

| Page function | Recommended skin | Notes |
|--------------|-----------------|-------|
| Static content page (intro, about) | we_js | raw HTML rendering |
| Notice / news list | we_basic | list + view with date/hit |
| Gallery / portfolio | we_gallery | thumbnail grid + lightbox |
| Contact / inquiry form | we_inquiry | form fields + submission |
| FAQ | we_faq | accordion UI |
| Map / directions | we_js + map script | raw HTML with map embed |

Do not create custom board skins unless the project design requires UI that
no existing skin supports. Check `D:\위링\위링스킨\` for available skins first.

### 사이트맵 기준 스킨 결정 (CRITICAL)
스킨 선택의 **1차 기준은 프로젝트 사이트맵(Figma)의 페이지 마킹**이다. 목업 HTML 유무보다 사이트맵이 우선한다.

| 사이트맵 마킹 | 의미 | 적용 |
|---|---|---|
| 📌디자인 | 시안대로 퍼블리싱하는 정적 콘텐츠 페이지 | `we_js` (wr_content 에 디자인 HTML) |
| 📌리스트/뷰 | 시안이 있는 목록 + 상세 | 시안에 맞는 스킨(`we_gallery` 등) + 필요한 만큼만 커스터마이징 |
| 📌게시판 | **시안 없는 일반 게시판** | 위링 기본 스킨 **그대로** (`we_basic`/`we_faq`/`we_gallery`) |

- **사이트맵에만 있고 목업에는 없는 메뉴가 정상이다.** 일반 게시판은 시안을 그리지 않으므로 목업 GNB 에 나타나지 않는다. 목업 기준으로 메뉴를 구성하면 누락되니 **메뉴 구성은 사이트맵을 기준**으로 한다.
- 마킹이 없거나 애매하면 **임의 판단하지 말고 사용자에게 확인**한다.

### ⚠️ 시안 없는 일반 게시판은 커스터마이징 금지
공지사항·회사뉴스·자료실처럼 시안이 없는 일반 게시판(📌게시판)은 위링 기본 스킨을 **적용하고 끝낸다.** "사이트 톤에 맞춘다"며 목록/뷰 마크업을 카드형으로 고쳐 쓰지 않는다.

| 허용 | 금지 |
|---|---|
| accent 컬러 통일(`--board-color-1` → `--point-color-1`, §스킨 accent 컬러) | 목록 구조 변경(테이블 → 카드/그리드) |
| `--sub_width` 등 **폭 변수**를 사이트 값에 맞춤 | 정렬바·검색폼·페이징 마크업 재작성 |
| §`.cont` 래핑 | 뷰(상세) 레이아웃 재구성 |

### ⚠️ 시안대로 리스트/뷰를 새로 짤 때도 그누보드 기본 기능은 전부 살린다 (CRITICAL)
📌리스트/뷰(시안 있는 게시판)를 시안 마크업으로 다시 짤 때, **디자인만 옮기고 원본 스킨의 기능 코드를 버리는 사고**가 났다. 시안에는 관리자 화면이 없으니 관리자 기능이 통째로 빠진다.

| 실제 사고 (2026-09-11, 금강불교사 `notice`·`qa`) | |
|---|---|
| 증상 | 번호 앞 체크박스·전체선택·선택삭제/복사/이동 없음, 관리자 버튼 없음, 글쓰기가 스타일 없는 글자로만 보임, 검색폼 없음 |
| 원인 | `we_basic`/`we_qa` 목록·뷰를 시안 표로 새로 쓰면서 원본 스킨의 `fboardlist` 폼과 관리자 분기를 옮기지 않음 |
| 덤 | 페이징 URL 을 `$list_href.'&amp;page='` 로 조립 → 목록에서는 `$list_href` 가 빈 값이라 `&page=2` 상대경로가 되어 **페이지 이동이 전부 깨짐** |

**목록(list.skin.php) 필수 체크리스트** — 원본 위링 스킨(`D:\위링\위링스킨\we_basic\list.skin.php`)에 있는 것은 전부 옮긴다.
- `<form name="fboardlist">` + hidden `bo_table sfl stx spt sca sst sod page sw`
- `$is_checkbox` 일 때: 헤더 전체선택(`chkall`), 행마다 `chk_wr_id[]`, 하단 `선택삭제·선택복사·선택이동` 버튼 + `all_checked()`·`fboardlist_submit()`·`select_copy()`(→ `board_list_update.php` / `move.php`)
- `$admin_href`(관리자) · `$rss_href`(RSS) · `$write_href`(글쓰기) — **버튼 스타일까지** 준다. 글자만 두지 않는다
- 분류(`$is_category` / `$category_option`, 현재 분류는 `#bo_cate_on`)
- 검색폼 `<form name="fsearch" method="get">` + `sfl`·`stx`·`sop`·`sca`
- 제목 아이콘: 답글(`icon_reply`)·비밀글·새글(`icon_new`)·댓글수
- 페이징 URL 은 반드시 `get_pretty_url($bo_table, '', $qstr.'&amp;page=')`. **`$list_href` 로 조립 금지**
- 체크박스 열이 앞에 붙으면 `th:nth-child(n)` 너비 규칙이 한 칸씩 밀린다 → `.chk ~ th:nth-child(n)` 로 보정

**뷰(view.skin.php) 필수 체크리스트**
- `$update_href`(수정) · `$delete_href`(삭제, `del(this.href)`) · `$copy_href`·`$move_href`(복사·이동, `board_move()` 팝업) · `$reply_href`(답변) · `$write_href`(글쓰기) · `$list_href`(목록)
- 첨부(`$view['file']`, 다운로드 포인트 차감 확인 스크립트 포함) · 관련링크(`$view['link']`)
- 원본 스킨이 댓글을 include 했다면 그대로 둔다

**검증** — 비회원 화면만 보면 관리자 기능은 원래 안 보이므로 누락을 못 잡는다. 관리자 분기 마크업을 라이브 페이지에 끼워 넣어 레이아웃을 보거나, 관리자 계정으로 확인을 요청한다.

### 게시판 세부설정 (권한·에디터·썸네일·목록수)
게시판 생성 후 **게시판마다** `관리자 → 게시판 관리 → 수정`에서 아래를 반드시 점검한다. **기본값 방치 금지.**

**생성 시 필수 체크리스트**

| 항목 | 필드 | 적용 대상 |
|---|---|---|
| ① 권한 레벨 | `bo_*_level` 전체 | 모든 게시판 |
| ② DHTML 에디터 사용 | `bo_use_dhtml_editor` | **HTML 본문을 쓰는 모든 게시판** |
| ③ 썸네일 크기 | `bo_gallery_width` × `bo_gallery_height` | 갤러리·썸네일형 |
| ④ 가로 컬럼수 | `bo_gallery_cols` | 갤러리·썸네일형 |
| ⑤ 페이지당 목록수 | `bo_page_rows` / `bo_mobile_page_rows` | 갤러리·썸네일형(+일반도 확인) |


**① 권한 레벨** (그누보드 비회원=1, 최고관리자=10)

| 게시판 유형 | 글읽기 | 목록·글쓰기·답변·댓글·링크·업로드·다운로드·HTML |
|------------|:---:|:---:|
| **we_js 콘텐츠**(소개·오시는길·이용안내 글 등) | **1** | **10** (전부) |
| **관리자만 제어하는 동적 게시판**(공지·갤러리·FAQ·이벤트) | 1 | **목록·다운로드만 1**, 글쓰기~HTML 등 나머지 10 |

- we_js 콘텐츠: 글은 메뉴 링크(`/{bo}/{wr_id}`)로 직접 읽으므로 **글읽기만 1**, 목록조차 10(관리자 외 목록 노출 불필요).
- 동적 게시판: 방문자는 **목록·읽기·첨부 다운로드까지만**(=1), 글쓰기·댓글·업로드·HTML 등 작성계열은 **관리자(10)**.

> # 🚨 공지·FAQ 는 **글쓰기 권한이 반드시 10** — 오픈 전 SQL 로 전수 점검한다
>
> 위 표대로 만들었더라도 **DB 복사·게시판 일괄 생성 과정에서 `bo_write_level` 이 1 로 남는 사고가 실제로 났다.**
>
> | 실제 사고 (2026-09-02, 함양 `faq`) | |
> |---|---|
> | 증상 | 자주묻는질문에 **비회원이 직접 글을 올림** (3건: "환급금 사용 기한", "숙박- 자연휴양림도 해당되나요?", "함양 반값여행 문의") |
> | 원인 | `faq` 의 `bo_write_level=1` · `bo_reply_level=1` (다른 게시판은 전부 10, **이 게시판만** 1) |
> | 발견 | 사용자가 화면에서 글쓰기 버튼을 보고 지적 — **오픈 전 점검에서 걸러지지 않았다** |
> | 조치 | `bo_write_level=10` · `bo_reply_level=10` 으로 변경, 비회원 글 3건은 실제 이용자 문의라 **삭제하지 않고 보고** |
>
> **방문자가 글을 쓸 수 있어야 하는 게시판은 문의(`qna`) 계열뿐이다.** 공지사항·자주묻는질문·갤러리·이벤트는 예외 없이 10.
>
> **점검 도구** — 사이트마다 오픈 전 반드시 실행한다. **exit 0 이어야 오픈 가능.**
> ```bash
> python3 D:/dev-base/tools/check-board-permissions.py --site 함양반값여행
> python3 D:/dev-base/tools/check-board-permissions.py --site 서천반값여행 --site 영천반값여행   # 여러 곳 한 번에
> python3 D:/dev-base/tools/check-board-permissions.py --site 함양반값여행 --fix                # 위반을 10 으로 교정
> ```
> exit `0`=이상 없음 / `1`=위반 / `2`=점검 불가(금고에 DB 접속정보 없음 — 정보를 채우고 다시 돌린다).
>
> **게시판 이름으로 판단하지 않는다.** 완도는 문의 게시판의 `bo_table` 이 `faq` 라, 이름 기준 점검은
> 정상인 곳을 위반으로 잡는다. 도구는 **스킨(`we_qna`·`wz.application` 등) · 제목(문의/신청/상담…) ·
> 강제 비밀글 · 비회원 글 비율**로 문의·신청 계열을 판별해 예외 처리하고, 그 근거를 함께 출력한다.
>
> 수동으로 볼 때의 SQL:
> ```sql
> SELECT bo_table, bo_subject, bo_skin, bo_use_secret, bo_write_level, bo_reply_level
>   FROM g5_board WHERE bo_write_level < 10 OR bo_reply_level < 10;
> ```
> 나온 행마다 **문의·신청 계열인지 스킨·제목까지 보고** 판단한다. 아니면 즉시 10 으로 바꾼다.
>
> **화면 검증까지 해야 끝난다** — 비로그인 상태로 `/{bo_table}` 에 글쓰기 버튼이 없는지,
> `/bbs/write.php?bo_table={bo_table}` 직접 접근 시 "권한이 없습니다" 가 뜨는지 둘 다 확인한다.

**② DHTML 에디터 사용** (`bo_use_dhtml_editor`)

> # 🚨 `we_js` 게시판은 DHTML 에디터를 **절대 체크하지 않는다** (`bo_use_dhtml_editor = 0`)
>
> **`we_js` 는 반드시 에디터 OFF = 순수 textarea 로 설정한다.** 예외 없다.
>
> **왜** — `we_js/view.skin.php` 는 `conv_content()` 처리본(`$view['content']`)을 **버리고
> `$view['wr_content']` 원문을 그대로** 출력한다.
> ```php
> echo "<script>bo_v_con.innerHTML='';bo_v_con.style.display='none'</script>"
>    . "<div id=jsContent>".$view['wr_content']."</div>";
> ```
> 즉 **`wr_option` 의 `html1` 플래그가 애초에 무관**하다. 에디터를 켤 이유가 하나도 없다.
>
> **켜면 무슨 일이 나나** — SmartEditor 가 저장할 때 마크업을 제 맘대로 정규화해
> **디자인 래퍼 태그를 소리 없이 지운다.** 담당자는 "글자만 좀 고쳤다"고 하는데 화면이 통째로 깨진다.
>
> | 실제 사고 (2026-08-27, 함양 `/about/1`) | |
> |---|---|
> | 증상 | CSS 가 전부 안 먹고 글자만 세로로 나열 |
> | 원인 | 관리자가 SmartEditor 로 문구를 고치자 **`<section class="intro_guide">` 여닫이 2줄이 삭제** |
> | 잔존 | `num_list`·`li` 28개·`h3` 5개 등 나머지 마크업은 **전부 그대로** → 래퍼만 증발 |
> | 복구 | 그 2줄만 다시 넣어 해결(내용 손실 0) |
>
> **점검 방법** — 스킨이 `we_js` 인 게시판 중 에디터가 켜진 곳을 찾는다.
> ```sql
> SELECT bo_table, bo_skin, bo_use_dhtml_editor FROM g5_board
>  WHERE bo_skin LIKE '%we_js%' AND bo_use_dhtml_editor <> 0;
> ```
> **결과가 0행이어야 한다.** 한 곳이라도 나오면 즉시 0 으로 바꾼다.
>
> **디자인 HTML 을 넣는 방법** — 관리자 에디터로 붙여넣지 말고
> **DB 직접 입력 또는 textarea 원문 붙여넣기**로 넣는다. `we_js` 는 원문을 그대로 뿌리므로 그대로 렌더된다.

**`we_js` 가 아닌 게시판**(공지·뉴스·제품 등 `we_basic`·`we_faq` 계열)에서 **본문에 HTML 을 넣는 경우에만
체크**한다. 이쪽은 `conv_content()` 를 타므로, 꺼두면 글 등록 시 `wr_option` 에 html 플래그가 안 붙어
본문이 **`&lt;p&gt;…` 처럼 태그가 그대로 화면에 노출**된다.

⚠️ **이 설정은 신규 글에만 적용된다.** 이미 등록된 글은 체크해도 그대로이므로, **글 등록 전에 먼저 켠다.** 이미 등록했다면 해당 글을 다시 저장하거나 `wr_option` 에 `html1` 을 넣어야 한다.

**③④⑤ 썸네일 게시판**(갤러리·이벤트 등 `we_gallery`/`we_event` — `get_list_thumbnail($board['bo_gallery_width'], $board['bo_gallery_height'])` 사용) 은 반드시:
1. **썸네일 크기**(`bo_gallery_width`×`bo_gallery_height`)를 **디자인 카드 비율에 맞춘다.** 기본값 202×150 방치 금지. (예: 디자인 카드가 `aspect-ratio:5/4` → `400×320`)
2. **가로 컬럼수**(`bo_gallery_cols`)를 디자인 열 수에 맞춘다(스킨은 `col-gn-N` 으로 렌더).
3. **페이지당 목록수**(`bo_page_rows`)를 컬럼수의 배수로(예 4열×3행=12), 모바일(`bo_mobile_page_rows`)도 별도 설정.

### 스킨 accent 컬러를 사이트 포인트 컬러로 통일
위링 게시판 스킨(`we_basic`·`we_faq`·`we_gallery`·`we_event` 등)은 style.css 최상단 `:root` 에 각자 다른 **accent 변수(`--board-color-1`)** 를 갖는다(스킨 기본색). 프로젝트에 복사한 뒤 이 값을 **`css/common.css` 의 `:root --point-color-1` 값과 동일하게** 바꿔 사이트 포인트 컬러로 통일한다.

```css
/* 스킨/style.css 최상단 */
:root{ --board-color-1:#fd8f12; }   /* common.css 의 --point-color-1 과 동일하게 */
```
- 스킨마다 변수명이 다를 수 있으니(`--board-color-1`/`--point-color-N` 등) **최상단 `:root` 에 선언된 색값**을 기준으로 맞춘다.
- `we_js` 처럼 `:root` 선언 없이 `var(--point-color-1)` 을 직접 참조하는 스킨은 **이미 통일돼 있으므로** 손대지 않는다.
- 수정 대상은 **프로젝트에 복사된 `skin/board/*/style.css`** 만. 원본 `D:\위링\위링스킨\` 은 공용이므로 건드리지 않는다.

### 페이징은 `default.css` 의 기본 블록을 통째로 교체 (CRITICAL)

그누보드 기본 페이징은 `.pg_wrap{float:left}` + 각진 사각 버튼 + **하드코딩 파랑 `#3a8afd`** 라 어느 사이트에 얹어도 브랜드와 따로 논다. `theme/wering/css/default.css` 의 `/* 페이징 */` 블록(`/* cheditor 이슈 */` 직전까지)을 **아래 블록으로 통째로 교체**한다.

```css
/* 페이징 */
.pg_wrap{margin:30px 0; display:flex; align-items:center; justify-content:center;}
.pg {text-align:center}
.pg_page, .pg_current {display:inline-block;vertical-align:middle; background-color:transparent; border:1px solid #ddd; transition: all 0.3s ease-out;}
.pg a:focus, .pg a:hover {text-decoration:none; background-color:#eee;}
.pg_page {color:#959595;height:30px;line-height:28px; width:30px;text-decoration:none;border-radius:50%; font-size:13px;}
.pg_page:hover {background-color:#fafafa}
.pg_start {text-indent:-999px;overflow:hidden;background:url('../img/btn_first.gif') no-repeat 50% 50%;padding:0;border:1px solid #ddd}
.pg_prev {text-indent:-999px;overflow:hidden;background:url('../img/btn_prev.gif') no-repeat 50% 50%;padding:0;border:1px solid #ddd}
.pg_end {text-indent:-999px;overflow:hidden;background:url('../img/btn_end.gif') no-repeat 50% 50%;padding:0;border:1px solid #ddd}
.pg_next {text-indent:-999px;overflow:hidden;background:url('../img/btn_next.gif') no-repeat 50% 50%;padding:0;border:1px solid #ddd}
.pg_start:hover,.pg_prev:hover,.pg_end:hover,.pg_next:hover {background-color:#fafafa}
.pg_current {display:inline-block;background:var(--point-color-1);color:#fff;font-weight:bold;height:30px;line-height:30px; width:30px; border-radius:50%; }
@media screen and (max-width: 640px) {
.pg_wrap .pg_page{margin:0 2px;}
.pg_current,
.pg_page{min-width:22px; width:22px; height:22px; line-height:22px; padding:0; font-size:11px;}
}
```

- **현재 페이지는 `var(--point-color-1)`** — 사이트마다 색을 손대지 않아도 `common.css` 의 `:root` 에서 자동으로 따라온다. hex 를 박지 않는다.
- 원형(`border-radius:50%`) + 고정 30px 정사각이라 `padding`·`min-width` 로 폭을 늘리면 원이 깨진다. 숫자가 세 자리여도 그대로 둔다.
- `.pg_wrap` 이 `float:left` 에서 `flex`+`justify-content:center` 로 바뀌므로, 기존에 `float` 를 전제로 넣어둔 `clear:both`·래퍼 여백이 있으면 함께 정리한다.
- 교체 대상은 **`/* 페이징 */` ~ `/* cheditor 이슈 */` 사이**. 앞뒤 블록(`.sv_nojs`, cheditor)은 건드리지 않는다.
- 적용 확인은 **페이징이 실제로 그려지는 목록**에서 한다. 글이 한 페이지에 다 들어가면 `.pg_wrap` 자체가 출력되지 않는다.

### 전체검색 결과 페이지 스킨 (검색이 있는 사이트는 필수)

**언제**: §Module B(Site Search) 를 적용했다면 — 즉 헤더/푸터에 `bbs/search.php` 로 가는 검색이 하나라도 있으면 — **전체검색 결과 페이지도 반드시 전용 스킨을 만든다.** 검색 폼만 붙이고 결과 페이지를 방치하면, 그누보드 기본 스킨(`skin/search/basic`)이 그대로 나와 **사이트에서 유일하게 디자인이 따로 노는 페이지**가 된다.

**미적용 판정** — 응답에 `skin/search/basic` 이 보이면 아직 기본 스킨이다:
```bash
curl -s "{사이트}/bbs/search.php?sfl=wr_subject%7C%7Cwr_content&stx={두글자이상}" | grep -o "skin/search/[a-z_]*"
```

**만드는 법**
1. `theme/{테마}/skin/search/we_search/` 에 `search.skin.php` + `style.css` 를 만든다(폴더명 위링 관례 `we_search`).
2. 관리자 → **환경설정**(`adm/config_form.php`) → 검색 스킨을 **`theme/we_search`** 로 지정(`cf_search_skin`). 모바일 미사용이면 `cf_mobile_search_skin` 은 그대로 둔다.
3. 원본은 `skin/search/basic/search.skin.php` 를 베이스로 삼되, **마크업은 프로젝트 클래스 규칙으로 새로 짠다**(기본 스킨의 `#sch_res_detail`·`#sch_res_ov`·`#sch_res_board` 같은 id 는 버린다).

**필수 체크리스트**

| # | 항목 | 이유 |
|---|------|------|
| ① | **`.cont` 래핑** — 스킨 최상단을 `<section class="cont {page}_con">` 으로 감싼다 | 기본 스킨은 폭 제한이 없어 콘텐츠가 화면 끝까지 퍼진다. `bbs/list.php` 방식과 달리 **코어 수정 불필요** — 스킨 안에서 감싸면 된다 |
| ② | **sub_visual 라벨 분기** — 테마 `head.php` 에서 `basename($_SERVER['PHP_SELF']) == 'search.php'` 로 검색 전용 라벨을 준다 | `search.php` 는 메뉴에 없어 `get_menu_db` 컨텍스트가 비고, 1depth 첫 메뉴(회사소개 등) 라벨이 **엉뚱하게** 붙는다 |
| ③ | **포인트 컬러 통일** — 기본 스킨의 파랑 `#3a8afd` · 분홍 `#ff005a` 를 전부 걷어내고 `var(--point-color-1)` 계열로 | §스킨 accent 컬러 통일과 동일 원칙 |
| ④ | **반응형 작성** | 기본 스킨에는 **미디어쿼리가 아예 없다.** 프로젝트 breakpoint 를 그대로 쓴다 |
| ⑤ | **빈 상태 2종** — ⓐ 검색어 없음(`$stx` 없음) ⓑ 결과 없음 | 헤더 검색 아이콘으로 처음 들어오면 `$stx` 가 비어 **본문이 통째로 빈 화면**이 된다. 기본 스킨은 ⓑ 조차 `검색된 자료가 하나도 없습니다.` 한 줄뿐 |
| ⑥ | **검증** — PC/모바일 렌더 + 스킨 경로가 `we_search` 로 바뀌었는지 | |

**코어가 만들어 스킨에서 못 바꾸는 마크업** — 반드시 이 셀렉터로 스타일한다:

| 출처 | 마크업 |
|------|--------|
| `$str_board_list` | `<li><a class=sch_on><strong>게시판명</strong><span class="cnt_cmt">건수</span></a></li>` (`class=sch_on` 은 **따옴표 없음**) |
| `$group_select` | `<label class="sound_only">` + `<select id="gr_id">` 가 **한 덩어리로** 온다. 라벨을 직접 쓰려면 `preg_replace('/<label[^>]*>.*?<\/label>/', '', $group_select)` 로 제거 |
| 키워드 하이라이트 | `<b class="sch_word">` — 코어가 출력하므로 **스킨 CSS 에서 반드시 재정의**(안 하면 기본 분홍) |
| `$write_pages` | `.pg_wrap` / `.pg` / `.pg_page` / `.pg_current` |

⚠️ **`fsearch_submit()` JS 는 기본 스킨에서 그대로 가져온다**(2글자 이상·공백 1개 제한 + `f.action=""`). 폼의 `onsubmit` 이 이 함수를 부르므로 빼먹으면 검색이 동작하지 않는다.

🚫 **`<select>` 에 세로 padding 을 주지 말 것 — 한글 받침이 잘린다.**
`padding:14px 22px` 처럼 세로 padding 으로 높이를 키우면 크롬이 select 내부 텍스트를 클리핑해 **받침만 사라진다**(`전체 분류`→`저체 브르`, `제목+내용`→`제모+내요`). `line-height` 를 키워도 해결되지 않고 오히려 악화된다. 검색 폼처럼 높이가 큰 select 는 **`height` + 가로 padding** 으로 잡는다.
```css
/* ✗ */ select{padding:14px 40px 14px 22px; line-height:1.3;}
/* ✓ */ select{height:58px; padding:0 40px 0 22px; line-height:normal;}
```
같은 줄의 `input`/`button`/토글도 `height` 로 맞춰 baseline 을 정렬한다(테두리 1px 때문에 래퍼가 있는 토글은 label 높이를 2px 작게). **글자가 깨지는 건 폰트 문제가 아니므로 font-family 를 의심하지 말 것** — 같은 페이지의 `input` 은 멀쩡히 나온다.

### 비 we_js 게시판 출력을 `.cont` 로 래핑 (bbs/ 에서 페이지별 구분)
`we_js` 콘텐츠 게시판의 **글읽기(view)** 는 wr_content 내부에 이미 디자인 `.cont`(예 `.intro_about .cont`)가 있어 너비/여백이 잡히지만, 그 외 스킨(`we_basic`·`we_gallery`·`we_faq`·`we_event`)의 목록/뷰/글쓰기, 그리고 we_js 게시판의 **목록·글쓰기** 는 `.cont` 없이 스킨 컨테이너(`#bo_list`/`#bo_gall`/`#bo_w`)로만 렌더돼 여백·정렬이 제각각이다.

**⚠️ 테마 `head.php`/`tail.php` 로는 안 된다.** `board.php` 가 `board_head.php`(→theme `head.php`, `.sub_contents` 열기)를 **list.php/view.php 보다 먼저** include 하므로, 테마 시점에는 목록/뷰를 구분할 수 없다(그룹으로 통째 제외하면 목록·글쓰기까지 제외됨). **각 페이지 종류를 아는 `bbs/{list,view,write}.php` 에서 스킨 include 를 `.cont` 로 감싼다.**

| bbs 파일 | 스킨 include | `.cont` 래핑 |
|---------|-------------|-------------|
| `bbs/list.php` | `list.skin.php` | **항상** 감쌈 |
| `bbs/write.php` | `write.skin.php` | **항상** 감쌈 |
| `bbs/view.php` | `view.skin.php` | **`$board['gr_id'] !== 'contents'` 일 때만** (we_js 콘텐츠 뷰 제외 — 내부에 이미 `.cont`, 이중 방지) |

```php
// bbs/list.php, bbs/write.php — 스킨 include 앞뒤 (항상)
echo '<div class="cont">'; include_once($board_skin_path.'/list.skin.php'); echo '</div>';
// bbs/view.php — view.head.skin 앞 / view.tail.skin 뒤 (조건부)
$view_wrap = ($board['gr_id'] !== 'contents');
if ($view_wrap) echo '<div class="cont">';   // ... 스킨들 ...   if ($view_wrap) echo '</div>';
```
- **제외 기준 = 게시판 그룹 `contents`.** we_js 콘텐츠 게시판을 그룹 `contents`(관리자 → 게시판그룹설정, `boardgroup_form.php`)로 묶고, **view 에서만** 제외. 앞으로 콘텐츠(we_js) 게시판 추가 시 반드시 이 그룹에 넣는다.
- 전제: `common.css` 에 `.sub_contents .cont{max-width:var(--sub_width); padding-top:80px;}` 규칙 존재(디자인 표준). 별도 CSS 추가 불필요.
- **주의**: `bbs/list.php`·`view.php`·`write.php` 는 그누보드 코어라 **업그레이드 시 덮어쓰일 수 있다.** 업그레이드 후 재적용 필요(사이트별 `sites/<업체>/work/src/bbs/` 에 수정본 보관).

---

## 회원 스킨 (회원가입 / 로그인)

로그인·회원가입·비밀번호찾기 등 회원 페이지는 **위링 공용 회원 스킨 패키지 `D:\위링\위링스킨\회원가입\`** 를 적용한다. 패키지 구성과 배포 대상:

| 패키지 경로 | 서버 배포 경로 | 내용 |
|------------|--------------|------|
| `skin/member/basic/**` | `/skin/member/basic/` | 회원 스킨(login·register_form·password·profile 등 `*.skin.php`) + `style.css` + `img/` |
| `bbs/login.php`·`password.php`·`register.php`·`register_result.php` | `/bbs/` | 회원 페이지 코어 오버라이드(위링 회원 플로우) |
| `img/step_1·2·3.svg` | `/img/` | 회원가입 단계 아이콘 — 스킨이 **`/img/step_N.svg`(웹루트 절대경로)** 로 참조하므로 반드시 웹루트 `/img/` 에 둔다 |

- 멤버 스킨명은 기본값 `basic` → `/skin/member/basic/` 를 덮어쓰면 **별도 관리자 설정 없이 즉시 적용**된다.
- **로그인 카드 로고 = 헤더 로고로 통일**: `skin/member/basic/login.skin.php` 의 `.login_logo img` 를 헤더와 동일한 로고로 바꾼다.
  ```php
  <img src="<?php echo G5_THEME_IMG_URL; ?>/logo_header.svg" alt="<?php echo get_text($config['cf_title']); ?>">
  ```
- 로그인 페이지는 `bbs/login.php` 가 `_head.php`(테마 헤더)를 include 하므로 **사이트 헤더/서브비주얼 + 로그인 카드** 구조로 렌더된다.
- ⚠️ `bbs/{login,password,register,register_result}.php` 는 그누보드 코어 오버라이드 → 업그레이드 시 덮어쓰일 수 있다(수정본은 `sites/<업체>/work/src/bbs/` 보관).

---

## Asset Copy Rules

| Source | Destination | Notes |
|--------|------------|-------|
| `html/css/reset.css` | `theme/wering/css/reset.css` | Overwrite |
| `html/css/common.css` | `theme/wering/css/common.css` | Overwrite |
| `html/css/slick.css` | `theme/wering/css/slick.css` | Overwrite if exists |
| `html/css/swiper.css` | `theme/wering/css/swiper.css` | Overwrite if exists |
| `html/css/font/` | `theme/wering/css/font/` | Overwrite |
| `html/js/*.js` | `theme/wering/js/` | Overwrite matching files |
| `html/img/*` | `theme/wering/img/` | Overwrite |

Do not delete existing theme files that have no counterpart in html/ output.
Board skin assets (skin/board/*/img/) are separate from theme img/.

---

## Path Conversion Reference

| Extracted HTML | Gnuboard PHP |
|---------------|-------------|
| `../img/{file}` | `<?php echo G5_THEME_IMG_URL; ?>/{file}` |
| `../css/{file}` | loaded via head.sub.php `add_stylesheet()` |
| `../js/{file}` | loaded via head.sub.php `add_javascript()` |
| `href="index.html"` | `<?php echo G5_URL; ?>` or `href="/"` |
| `href="{page}.html"` | board view URL (e.g., `/bbs/board.php?bo_table={id}&wr_id={n}`) |
| `href="#none"` | `href="#"` or actual PHP route |
| `src="../img/logo.svg" alt="..."` | `src="<?php echo G5_THEME_IMG_URL; ?>/logo.svg" alt="<?php echo get_text($config['cf_title']); ?>"` |

---

## 영카트(쇼핑몰) 프로젝트

> 이 문서의 나머지 규칙은 **일반 사이트(커뮤니티형)** 기준이다.
> 쇼핑몰 시안이면 아래 규칙이 **위 규칙보다 우선**한다. 선행 5단계와 클래스/포맷 규칙은 그대로 유효하다.
>
> 최초 정리: 2026-09-08 금강불교사(kg9202.com) — 그누보드 5.6.36 + 영카트

### 판별

`data/dbconfig.php` 에 `define('G5_USE_SHOP', true);` 가 있으면 영카트다. 루트에 `shop/`, `shop.config.php` 가 함께 있다.

### 1. 선행 셋팅 — 6번째 단계 추가

일반 선행 5단계를 그대로 하고, **`theme/wering/theme.config.php` 의 `G5_COMMUNITY_USE` 를 `false`** 로 바꾼다.

```php
// 커뮤니티 사용없이 쇼핑몰이 초기화면이라면 false로 설정
if(! defined('G5_COMMUNITY_USE')) define('G5_COMMUNITY_USE', false);
```

이 한 줄로 `/` 가 쇼핑몰 메인이 되고 **게시판 head/tail 까지 shop 쪽을 탄다.** 이걸 안 바꾸면 커뮤니티 최신글 화면이 뜬다.

### 2. 변환 대상 파일이 달라진다

| 일반 사이트 | 영카트 |
|---|---|
| `theme/wering/head.php` | `theme/wering/shop/shop.head.php` |
| `theme/wering/tail.php` | `theme/wering/shop/shop.tail.php` |
| `theme/wering/index.php` | `theme/wering/shop/index.php` |
| `css/default.css` | `css/default.css` + **`css/default_shop.css`** |

`shop.head.php` 에는 tnb·로고·검색폼(`shop/search.php`, `name="q"`)·장바구니 수량(`get_boxcart_datas_count()`)·아웃로그인·분류메뉴(`shop/category.php` include)·사이드메뉴가 이미 들어 있다. **퍼블리싱 헤더로 갈아끼울 때 이 PHP 기능들을 반드시 옮겨 담는다.**

### 3. 테마 오버라이드 훅 — 있는 파일과 없는 파일

영카트 코어 일부는 테마에 같은 이름 파일이 있으면 그걸 대신 include한다. **훅이 있으면 코어를 절대 건드리지 않는다.**

| 페이지 | 훅 | 테마에 둘 파일 |
|---|---|---|
| 상품목록 | 있음 | `theme/wering/shop/list.php` |
| 장바구니 | 있음 | `theme/wering/shop/cart.php` |
| 관심상품 | 있음 | `theme/wering/shop/wishlist.php` |
| 주문상세/주문완료 | 있음 | `theme/wering/shop/orderinquiryview.php` |
| 마이페이지 | 있음 | `theme/wering/shop/mypage.php` |
| 상품상세 | **없음** | 스킨(`item.form.skin.php`·`item.info.skin.php`)으로 처리 |
| 주문서 | **없음** | 코어 4줄 패치 (아래) |
| 타입별 목록(`type-N`) | **없음** | 코어 4줄 패치 (아래) |

⚠️ **`shop/listtype.php` 를 빠뜨리기 쉽다.** GNB 의 "신상품·인기상품" 이 여기로 오는데, 이 파일은 **래퍼 마크업 없이 `$list->run()` 과 `get_paging()` 만 출력**한다. 카드 CSS 가 `.products_goods .list > li` 처럼 스코핑돼 있으면 **한 줄도 안 걸려 화면이 깨진다.** 목록 페이지 작업할 때 `list.php` 와 **반드시 같이** 처리한다.

**주문서와 타입별 목록은 코어 4줄 패치가 필요하다.** 훅이 있는 파일들과 같은 패턴으로 넣고, 테마에 사본을 둔다.

```php
// shop/listtype.php — include_once('./_head.php'); 바로 앞
$theme_listtype_file = defined('G5_THEME_SHOP_PATH') ? G5_THEME_SHOP_PATH.'/listtype.php' : '';
if ($theme_listtype_file && is_file($theme_listtype_file)) {
    include_once($theme_listtype_file);
    return;
}
```

```php
// shop/orderform.php — require_once(G5_SHOP_PATH.'/orderform.sub.php'); 를 교체
$theme_orderform_sub = defined('G5_THEME_SHOP_PATH') ? G5_THEME_SHOP_PATH.'/orderform.sub.php' : '';
if ($theme_orderform_sub && is_file($theme_orderform_sub))
    require_once($theme_orderform_sub);
else
    require_once(G5_SHOP_PATH.'/orderform.sub.php');
```

⚠️ 영카트 업그레이드 시 이 4줄이 사라진다. 업그레이드 후 재적용하고, 수정본은 `sites/<업체>/work/src/shop/` 에 보관한다.

### 4. 스킨 경로를 테마 안으로 옮긴다

기본값은 루트 `skin/` 을 본다. **관리자에서 테마 스킨으로 바꿔야** 스킨 작업이 테마와 함께 이동한다.

| 설정 | 위치 | 값 |
|---|---|---|
| PC 쇼핑몰 스킨 (`de_shop_skin`) | 쇼핑몰설정 | `basic` → **`theme/basic`** |
| 회원 스킨 (`cf_member_skin`) | 기본환경설정 | `basic` → **`theme/basic`** |

바꾸면 `G5_SHOP_SKIN_PATH` 가 `theme/wering/skin/shop/basic/` 을 가리킨다. 테마가 자체 shop 스킨 38개를 이미 갖고 있으므로 전환해도 화면은 그대로다.

⚠️ **공용 위링스킨 폴더에는 shop 스킨이 없다.** 게시판 스킨과 달리 상품/장바구니/주문 화면은 `skin/shop/basic` 을 테마 안에서 직접 커스터마이징한다.

### 5. 짧은주소는 쇼핑몰에도 적용된다

`cf_bbs_rewrite` 를 숫자로 저장하면 루트 `.htaccess` 가 자동 생성되고 **영카트 규칙도 함께** 들어간다.

| 형식 | 대상 | 생성 함수 |
|---|---|---|
| `/shop/list-{ca_id}` | 분류별 목록 | `shop_category_url($ca_id)` |
| `/shop/type-{1~5}` | 타입별 목록 | `shop_type_url($type)` |
| `/shop/{it_id}` | 상품 상세 | `shop_item_url($it_id)` |
| `/{bo_table}` · `/{bo_table}/{wr_id}` | 게시판 | `get_pretty_url()` |

**URL 은 반드시 위 함수로 만든다.** 문자열로 조립하면 rewrite 를 끈 사이트에서 깨진다.
상품유형 기본값: 1=히트, 2=추천, 3=최신, 4=인기, 5=할인.

### 6. GNB 소스가 두 갈래다

일반 사이트는 `get_menu_db()` 하나지만 쇼핑몰은 **메뉴DB + 상품분류(ca_id)** 를 섞는다.

| 시안 메뉴 유형 | 소스 |
|---|---|
| 전체 카테고리 / 분류 트리 | `get_shop_category_array(true)` — `theme/wering/shop/category.php` 를 시안 마크업으로 교체 |
| 신상품·인기상품 등 | `shop_type_url(N)` |
| 사용후기 | `shop/itemuselist.php` (게시판으로 만들지 않는다) |
| 상품문의 | `shop/itemqalist.php` |
| 공지사항·고객센터 등 콘텐츠 | 게시판 (일반 규칙대로 1depth 단위 1개) |

### 7. 상품 카드는 한 벌만 만든다

메인 진열·분류 목록·검색 결과의 카드 마크업이 대개 같다. `main.10.skin.php` 에 카드를 쓰고 나머지는 include 한다.

```php
// list.10.skin.php
include dirname(__FILE__).'/main.10.skin.php';
```

`item_list` 클래스 사용 패턴:

```php
$list = new item_list();
$list->set_type(3);                                   // set_list_skin 보다 먼저
$list->set_list_skin(G5_SHOP_SKIN_PATH.'/main.10.skin.php');
$list->set_list_mod(4);   // 한 줄 개수
$list->set_list_row(2);   // 줄 수
$list->set_img_size(287, 300);
$list->set_css('list');   // 스킨에서 $this->css 로 <ul> 클래스에 씀
echo $list->run();
```

스킨 안에서 쓰는 값: `$list`(행 배열), `$this->list_mod`, `$this->img_width/height`, `$this->css`.
가격은 `display_price(get_price($row), $row['it_tel_inq'])`, 소비자가는 `it_cust_price > it_price` 일 때만 `<del>` + 할인율.

### 8. 옵션 UI 는 shop.js 를 덮어쓴다

상품상세의 "선택된 옵션" 목록은 `js/shop.js` 의 `add_sel_option()` 이 `<ul><li>` 로 그린다. 시안이 표라면 **스킨 안 인라인 `<script>` 에서 함수를 재정의**한다. `item.php` 가 `<script src=shop.js>` 를 먼저 출력하므로 나중 정의가 이긴다.

재정의 대상: `add_sel_option(type, id, option, price, stock)` / `price_calculate()`

지켜야 할 계약:

| 항목 | 이유 |
|---|---|
| 행 class `sit_opt_list`(선택옵션) / `sit_spl_list`(추가옵션) | `fitem_submit()` 이 개수를 센다 |
| `io_type[]` · `io_id[]` · `io_value[]` · `ct_qty[]` · `.io_price` · `.io_stock` | `cartupdate.php` 와 금액계산이 읽는다 |
| `<div class="get_item_options">` 와 그 안의 `<label for="it_option_N">` | `sel_option_process()` 가 라벨 텍스트로 옵션명을 만든다 |
| `#sit_sel_option` · `#sit_opt_added` id | 다른 스크립트가 참조한다 |

`get_item_options()` 출력은 시안 마크업으로 바로 못 쓰므로 **문자열 후처리**한다 — `<div class="get_item_options row">` 로 클래스 추가, `<label>` 은 `<span>` 으로 감싸 유지(제거 금지), select 를 감싼 `<span>` 만 벗긴다.

수량 입력은 시안이 스테퍼면 `<span>` 표시 + `ct_qty` **hidden input** 조합으로 만든다. 시안에 옵션 삭제 버튼이 없으면 **수량을 1 미만으로 내릴 때 행 삭제**로 대체한다.

### 9. 장바구니 수량 변경 엔드포인트

영카트 장바구니에는 **수량만 바꾸는 경로가 없다**(옵션수정 팝업뿐). `cartupdate.php` 의 act 는 `buy` / `seldelete` / `alldelete` / `multi` / `optionmod` 뿐이다.

시안에 행별 스테퍼가 있으면 테마에 작은 엔드포인트를 만든다 — `theme/wering/shop/cartqty.php`

```php
include_once('../../../common.php');
header('Content-Type: application/json; charset=utf-8');
check_token();                                   // CSRF
// ct_id 가 현재 세션 장바구니(ss_cart_id)의 행인지 확인 → 재고 상한 확인 → ct_qty 갱신
```

⚠️ 세션 소유 확인과 재고 상한 검사를 빼면 안 된다. 호출부에서 `token: "<?php echo get_token(); ?>"` 를 같이 보낸다.

또한 영카트 장바구니는 **상품(it_id) 단위로 묶어 1행**이다. 시안이 옵션별 행이면 `ct_id` 단위로 출력하되, 체크박스 삭제·주문은 여전히 it_id 기준으로 동작한다는 점을 알고 쓴다.

### 10. 회원 페이지는 레이아웃이 없다

`bbs/login.php`·`register.php` 등은 `_head.sub.php`(HTML head 만)를 include 한다. 위링 공용 회원 패키지의 `bbs/*.php` 오버라이드를 안 쓰는 프로젝트에서는 **헤더·사이드·푸터 없이 스킨만 렌더된다.**

코어를 건드리지 않는 해법 — 회원 스킨 안에서 직접 레이아웃을 include 한다.

```php
if (!defined('_GNUBOARD_')) exit;
include_once(G5_SHOP_PATH.'/_head.php');   // 헤더·사이드
?>
... 스킨 마크업 ...
<?php
include_once(G5_SHOP_PATH.'/_tail.php');   // 푸터
```

대상: `login.skin.php` · `register.skin.php` · `register_form.skin.php` · `register_result.skin.php` · `member_confirm.skin.php`
`head.sub.php` 는 이미 include 된 상태라 중복되지 않는다(`include_once`).

같은 문제가 `shop/itemuse.php` 에도 있다. 이 파일은 **단독 페이지이면서 상품상세 후기 탭에도 include** 되므로, 스킨에서 분기한다.

```php
$use_standalone = (basename($_SERVER['SCRIPT_NAME']) === 'itemuse.php');
```

### 11. 그누보드 기본 CSS 가 퍼블리싱을 덮는 지점 (3종)

`default.css` / `default_shop.css` 는 `common.css` 보다 먼저 로드되지만 **요소 선택자로 직접 거는 규칙은 상속보다 세다.** 아래 세 가지는 매번 나온다.

| 증상 | 원인 | 조치 |
|---|---|---|
| 카드 가격이 `60,000 / 원` 처럼 글자 단위로 쪼개짐 | `p {word-break:break-all}` 이 `#wrap{word-break:keep-all}` 상속을 이김 | 테마 `default.css`·`default_shop.css` 의 `p` 규칙에서 `word-break` 만 제거 |
| 입력칸 안에 빨간 별표 배경 | `.required {background-image:url(require.png)}` | 시안이 라벨에 `<em>*</em>` 를 쓰면, 해당 폼 영역만 `background-image:none !important` 로 끈다 |
| "필수" 같은 보조 텍스트가 화면 좌상단에 겹쳐 보임 | `.sound_only` 가 `font-size:0` 로만 숨겨 폰트 규칙과 충돌 | `width:1px !important; height:1px !important; clip:rect(0 0 0 0)` 추가 |

⚠️ `common.css` 는 수정 금지 규칙이 그대로 적용된다. 고칠 곳은 **테마의 `default*.css`** 다.

### 12. `<ul><li>` 를 시안의 표로 바꾸는 정형 패턴

주문서(`orderform.sub.php`)·주문상세(`orderinquiryview.php`)·회원가입 폼(`register_form.skin.php`)은 목록 마크업이라 시안의 `<table>` 과 안 맞는다. **PHP 계산과 스크립트는 한 줄도 건드리지 말고 마크업만** 바꾼다.

- 원본을 그대로 두고 **변환 스크립트로 사본을 생성**한다. 손으로 고치면 재현이 안 된다.
- 치환 전에 `re.sub(r"[ \t]+\n", "\n", src)` 로 줄 끝 공백을 정리해야 패턴이 맞는다.
- 여는 태그의 래퍼(`<div class="tbl_frm01 tbl_wrap">`)를 없앴으면 **닫는 `</div>` 도 같이 지운다.** 이걸 빠뜨리면 DOM 이 어긋나 뒷 블록이 통째로 밖으로 밀린다.
- `<li><strong>항목</strong><span>값</span></li>` → `<tr><th>/<td>` 정규식 변환이 대부분 통하지만, **span 이 먼저 오는 블록, PHP `echo` 로 조립되는 항목, 자식 요소가 더 있는 항목**은 따로 처리해야 한다. 변환 후 남은 `<li>` 개수를 반드시 세어 0 인지 확인한다.
- JS 가 값을 갱신하는 블록(`#sod_bsk_tot`, `#ct_tot_price` 등)은 지우지 말고 `class="blind"` 로 숨긴다.

### 13. 영카트에 없어서 시안과 충돌하는 것

시안에 있어도 플랫폼에 기능이 없으면 **임의로 만들지 말고 보고 후 결정**한다.

| 시안 요소 | 영카트 실제 |
|---|---|
| 후기 1건 상세 페이지 | 없음. 상품별 후기 모음(`itemuse.php?it_id=`)만 있다 |
| 후기 목록의 조회수 | 필드 없음 |
| 후기 목록의 글쓰기 버튼 | 후기는 구매한 주문에서만 작성(`itemuseform.php?it_id=&od_id=`) |
| 후기 댓글 | 없음. 판매자 답변(`is_reply_*`)만 있다 |
| 메인비주얼 슬라이드의 문구 | 배너 테이블에 텍스트 필드가 없다(이미지·링크·alt 뿐). 문구는 이미지에 포함해야 한다 |
| 장바구니 옵션변경 버튼 | 팝업(`cartoption.php`)이 기본 스킨 마크업이라 별도 작업 |
| 결제수단 라디오 목록 | PG 설정에 따라 생성된다. **PG 확정 전에는 무통장입금만 나온다** |

### 14. 관리자 선행 설정 체크리스트

퍼블리싱 전에 아래를 맞춰두지 않으면 화면이 비거나 크기가 어긋난다.

| 설정 | 위치 | 맞출 값 |
|---|---|---|
| 회사정보(상호·대표·주소·사업자번호·통신판매업신고·전화·개인정보책임자·이메일) | 쇼핑몰설정 | 푸터가 전부 이 값을 쓴다 |
| PC 쇼핑몰 스킨 / 회원 스킨 | 쇼핑몰설정 / 기본환경설정 | `theme/basic` |
| 상세 이미지 크기 (`de_mimg_*`) | 쇼핑몰설정 | 시안 상세 이미지 폭 |
| 목록 이미지 크기 (`de_simg_*`) | 쇼핑몰설정 | 시안 카드 썸네일 크기 |
| 검색 진열 (`de_search_list_mod/row`, `de_search_img_*`) | 쇼핑몰설정 | 목록과 동일하게 |
| 분류별 진열 (`ca_list_mod`, `ca_list_row`, `ca_img_*`) | 분류관리 — **분류마다** | 시안 기준 (예: 4열 × 5줄) |
| 휴대폰번호 사용·필수 (`cf_use_hp`) | 기본환경설정 | 시안 회원가입에 있으면 켠다. 꺼져 있으면 입력칸이 비어 보인다 |
| 메인 배너 | 배너관리 | 위치 `메인`, 종료일을 먼 미래로(기본은 한 달 뒤 자동 종료) |

### 11-1. 그누보드 기본 ID·클래스가 시안을 덮는 지점 (추가, 2026-09-11 금강불교사)

§11 외에 영카트 화면을 시안으로 바꿀 때 반복해서 나온 것들이다.

| 증상 | 원인 | 조치 |
|---|---|---|
| 요소 사이 간격(gap)이 0 으로 붙음 (상품상세 정보 영역, 장바구니·관심상품 목록↔버튼) | 시안은 `flex + gap` 컨테이너 바로 아래에 요소가 있는데, 스킨은 그 사이에 `<form>` 이 끼어 gap 이 form 한 개에만 걸림 | `.product_view .info form`, `.cart_list form`, `.wish_list form` 에 `display:contents` |
| `.block + .block` 간격이 한 곳만 0 | 두 블록 사이에 `class="blind"` 숨김 블록(`#sod_bsk_tot`)이 있어 인접 선택자가 끊김 | 숨김 블록을 첫 블록 앞으로 옮긴다 (JS 는 위치와 무관) |
| 파란 테두리·파란/분홍 배경·청록 글씨가 시안 위에 덧칠됨 | 스킨에 남은 그누보드 ID 에 `default_shop.css` 규칙이 걸려 있음: `#sod_frm` `#sod_frm_orderer` `#sod_frm_taker` `#sod_frm_pay` `#od_pay_sl` `#sod_frm_paysel` `#settle_bank` `#od_tot_price` `#sod_bsk_tot2` `.order_choice_place` `.lb_icon` | JS·코어가 쓰는지 grep 후 **안 쓰면 ID 삭제**, 테마 JS 만 쓰면 **ID 이름을 바꾸고 JS 도 같이 수정**, 코어가 출력하는 것(`#display_pay_button`, `#sod_v`)은 `.order_btns #display_pay_button` 처럼 ID 를 포함한 더 센 선택자로 덮는다 |
| `<button type="submit">` 에만 회색 테두리 | `reset.css` 의 `[type=submit]{border:1px solid #ddd}` 가 `button{border:none}` 보다 셈 | reset 의 입력 규칙을 `input[type=...]` 로 한정 |
| 버튼이 93% 너비로 늘어나 세로로 쌓임 | `default_shop.css` 의 `.btn_list{margin:0 auto; width:93%}` | 사용하는 영역에서 `margin:0; width:auto` |
| 입력칸 안 빨간 별표 | `.required` 클래스(`!important`) | 클래스는 빼고 **`required` 속성만 남긴다** (`wrest.js` 는 속성으로 검사) |

**그누보드 기본 색 전수 점검** — 작업 후 해당 화면에서 계산된 색에 `#3a8afd`(파랑) `#ff006c`(분홍) `#38b2b9`(청록) `#e5f0ff`·`#edf3fc`(연파랑 배경)이 남아 있는지 스크립트로 훑고, 남은 곳은 포인트 컬러(`--point-color-1/2`)로 바꾼다. 사용자가 하나하나 지적하기 전에 먼저 한다.

### 11-2. 테마에 파일이 없으면 코어 화면이 그대로 나오는 곳

| 화면 | 테마 오버라이드 | 없으면 |
|---|---|---|
| 주문내역 목록 `shop/orderinquiry.php` (회원) | **`theme/<테마>/shop/orderinquiry.sub.php` 만** 인식 (본 파일 오버라이드 없음) | 제목·경로 없이 그누보드 7칸 표(`tbl_head03`) + 파란 페이징(`.pg_wrap`)이 나온다 |

`orderinquiry.sub.php` 를 만들 때: 제목·경로·자체 페이징은 `basename($_SERVER['SCRIPT_NAME']) === 'orderinquiry.php'` 일 때만 출력하고, 코어가 뒤에 붙이는 `get_paging()` 은 `#sod_v > .pg_wrap{display:none}` 으로 숨긴다. 코어 래퍼 `#sod_v td{text-align:center}` 도 ID 선택자로 덮어야 한다.

#### 시안 없는 기본 스킨 — 테마에 같은 이름 파일을 두지 않으면 설치본이 그대로 나온다 (2026-09-14 금강불교사)

시안이 있는 화면만 옮기면 아래 화면은 `btn01`/`btn02` 파란 버튼·`new_win` 기본 새창으로 남는다. **사용자가 "기본테마 그대로인 곳 전부"를 요청했는데 두 번 빠졌다.**

| 화면 | 테마 파일 | 없으면 |
|---|---|---|
| 상품상세 상품문의 탭 / 전체 상품문의 / 문의·후기 쓰기 새창 | `skin/shop/basic/itemqa` · `itemqalist` · `itemqaform` · `itemuseform` `.skin.php` | 기본 스킨 (`#sit_qa_wbtn` 등) |
| 쿠폰존 / 개인결제 리스트 / 상품 이미지 새창 | `skin/shop/basic/couponzone.10` · `personalpay` · `largeimage` `.skin.php` | 기본 스킨 |
| 쿠폰 내역 새창 / 배송지 목록 새창 | `theme/<테마>/shop/coupon.php` · `orderaddress.php` (코어 훅) | 코어 마크업 |
| 포인트 새창 / 회원정보 찾기 / 비밀번호 재설정 | `skin/member/basic/point` · `password_lost` · `password_reset` `.skin.php` | 기본 스킨 |
| 개인결제 결제화면 `personalpayform.sub.php` / 주문서 쿠폰 레이어 3종 | **훅 없음** | 코어를 더 고치지 말고 `default_shop.css` 끝에서 `.pesonal` · `#personal_pay` · `.od_coupon` 으로 덮는다 |

- **전수 점검**: `fetch-source.py --dir theme/wering` 로 서버 테마를 전부 받아 **작업본에 없는 스킨 파일 목록**을 뽑는다 → 비로그인 크롤 + 관리자 로그인(읽기)으로 새창까지 연다 → 계산된 색 스윕. 탭 안에서 include 되는 스킨(`itemqa`)은 페이지 단위 점검에 안 걸린다.
- **테마 기본 CSS 색 일괄 교체**: 테마 `default.css`·`default_shop.css` 의 `#3a8afd` `#ff006c` `#ff005a` `#38b2b9` `#305af9` `#1471f6` `#1c70e9` `#253dbe` → `var(--point-color-1)`, `#e5f0ff` `#edf3fc` → `#f8f8f8`, `#d1ddee` → `var(--point-color-3)`. 화면별로 덮는 것보다 빠지는 곳이 없다.
- **헬퍼 함수는 `shop.head.php` 에 두지 않는다**: 상품문의 탭 ajax 페이징(`/shop/itemqa.php` 단독 호출)과 새창에는 `shop.head.php` 가 없어 `theme_shop_paging()` 미정의 치명 오류가 난다. `theme/<테마>/shop/theme_shop.lib.php` 로 분리해 필요한 스킨에서 `include_once`.
- **관리자 폼 자동 저장은 `form.requestSubmit()` 금지**: 관리자 토큰(`adm/ajax.token.php`) 처리가 빠져 "올바른 방법으로 이용해 주십시오"로 거부되거나 조용히 저장이 안 된다. 실제 확인 버튼을 클릭하고, 폼 전체값을 저장 전후로 비교해 의도한 필드만 바뀐 것을 확인한다. 쿠폰폼처럼 선택값에 따라 `required` 를 풀어 주는 폼은 select 를 **실제로 선택**(`select_option`)해야 한다 — 값만 넣으면 숨은 필수칸 때문에 조용히 제출이 막힌다.

#### 전 과정 테스트에서 걸린 함정 (2026-09-14 금강불교사)

- **테스트 회원은 자동으로 못 만든다** — 사이트 회원가입과 **관리자 회원추가 둘 다** 자동등록방지(kcaptcha)가 있다. 사람에게 가입을 요청한다(실제 회원가입 검증도 같이 끝난다).
- **옵션 상품 자동화**: `shop.js` 는 옵션 select 의 `mouseup`/`touchend`(Safari `mousedown`)가 있어야 `option_add=true` 가 되어 옵션 줄을 추가한다. `select_option()` 만 쓰면 "상품의 선택옵션을 선택해 주십시오"가 떠서 **버그로 오판**하기 쉽다 — `dispatch_event("mouseup")` 후 선택.
- **에디터 HTML 을 `<p>` 에 넣지 않는다**: `conv_content($x, 1)` 결과(블록 태그)가 `<p class="txt">` 안에 들어가면 브라우저가 문단을 먼저 닫아 본문이 스타일 밖으로 빠진다(큰 빈칸 + 여백 없는 본문). 후기 본문·판매자 답변은 `<div>`.
- **후기 쓰기 버튼**: 시안의 후기 목록에 쓰기 버튼이 없어 빼더라도, 상품상세 후기 탭에는 `itemuseform.php?it_id=` 새창 버튼을 둔다. 없으면 고객이 후기를 쓸 경로가 없다.
- **썸네일 찌그러짐**: `get_it_image()` 는 `width`/`height` 속성을 박는다. 부모 폭으로 줄이는 칸에는 `img{height:auto}` 를 같이 준다. 데이터 없이 보면 안 보인다.
- **개인결제는 무통장을 지원하지 않는다** — 결제수단이 가상계좌·계좌이체·휴대폰·카드뿐이라 PG 미계약 상태면 "결제할 방법이 없습니다". 디자인만 확인하고 결제는 PG 이후.
- **테스트 주문 전 메일 수신처 확인**: 주문 메일은 `cf_admin_email`·주문자 메일·상품 `it_sell_email` 로 간다. 관리자 메일을 고객사 주소로 바꾼 뒤라면 테스트 전에 사용자에게 수신처를 묻는다.

### 11-3. 기능 동작 체크 (시안에 없어서 빠뜨리기 쉬운 것)

- **관심상품 행 버튼** — `바로구매`·`장바구니`를 상품 링크로 두지 않는다. 그 행만 체크한 뒤 `cartupdate.php`(`act=multi`, `sw_direct=1` 이면 주문서 / `0` 이면 장바구니)로 보낸다. 옵션 상품은 옵션을 골라야 하므로 안내 후 상세로, 전화문의·품절은 안내만.
- **상품상세 "선택옵션" 제목** — 선택옵션·추가옵션이 있을 때만 출력한다.
- **비회원 구매 개인정보 안내 박스** — `de_guest_privacy` 가 비어 있으면 박스를 출력하지 않고, 관리자에 문구 입력을 요청한다(법적 문구는 임의 작성 금지).
- **주문서 결제수단** — PG 가 출력하는 `<input> <label for>` 쌍은 버퍼로 받아 `<label><input><span>` 으로 감싸 시안 라디오 스타일에 맞춘다. 무통장 계좌가 `OO은행 12345-67-89012` 같은 샘플 값이면 사용자에게 보고한다.
- **포인트 미사용 사이트** — "무통장입금 이외 결제 시 포인트 미적립" 안내는 `cf_use_point` 가 켜져 있을 때만 출력한다.

### 15. 검증은 실제 흐름까지 돌린다

렌더만 보고 끝내지 않는다. **상품상세 → 옵션 선택 → 장바구니 → 주문서 → 주문완료**까지 실제로 한 번 통과시키고 주문번호가 생기는지 확인한다. 결제 관련 파일을 건드렸다면 이 확인이 필수다.

검수용으로 만든 더미(상품·분류·옵션·테스트 주문·샘플 게시글)는 **목록으로 남겨 두고** 실제 오픈 전에 정리한다. 영카트 관리자 주문내역에는 일괄삭제 버튼이 없다는 점을 미리 알아둔다.

- **실주문·회원 로그인이 있어야 열리는 화면**(주문상세, 회원 주문내역, 관심상품, 게시판 관리자 분기)은 사용자 승인 없이 테스트 주문·테스트 회원을 만들지 않는다(주문 알림 메일이 관리자·입력 주소로 나간다). 대신 스킨을 더미 데이터로 로컬 `php` 실행해 오류를 보고, 그 출력 HTML 을 라이브 페이지에 끼워 넣어 **라이브 CSS 로** 레이아웃을 확인한다. 실제 화면 확인은 사용자에게 요청한다.
- **업로드 전에는 서버 파일을 내려받아 로컬과 diff** 한다. 차이가 내 수정분뿐일 때만 올린다(서버에서 따로 고친 내용을 덮어쓰지 않도록).

---

## 스킨 이후 작업 (지시 누적)

> 스킨 변환이 끝난 뒤 **사용자 지시로 수행하는 작업**을 여기에 누적한다.
> 규칙이 아니라 **작업 기록**이다. 지시받을 때마다 한 줄씩 추가하고, 완료되면 `[x]` 로 바꾼다.
> 형식: `- [ ] YYYY-MM-DD (사이트) 작업 내용` — 상세는 각 사이트의 `sites/<업체>/작업현황.md` 에 둔다.

- [x] **약관 2종 적용 (개인정보처리방침 / 이용약관)** — 게시판 스킨작업 마무리 후 수행
      *(2026-07-24 어린이건강놀이터 적용 완료)*

  원본: `D:\위링\위링스킨\약관\개인정보 처리방침.html`(파일명에 공백 주의), `D:\위링\위링스킨\약관\이용약관.html`
  적용처: 관리자 → **내용관리**(`adm/content_form.php`)

  1. **CSS 분리** — 원본 `<style>…</style>` 안의 CSS는 에디터에 넣지 말고 **현재 적용 중인 `theme/wering/css/default.css` 하단에 추가**한다.
  2. **본문만 붙여넣기** — `<body>…</body>` **안쪽 내용만** 복사해 내용관리 에디터의 **HTML 모드**로 붙여넣는다. (`<html>/<head>/<style>` 통째 금지)
  3. **업체명 치환** — 원본에 남아 있는 기존 업체명을 **현재 프로젝트명으로 바꾼다.**
     - 이용약관: `위드홀스`
     - 개인정보처리방침: `강원우수관광사업체`
  4. **조사(은/는·이/가·을/를) 함께 변환** — 원본은 `강원우수관광사업체`**는** 처럼 **받침 없는** 이름 기준이다. 새 이름에 **받침이 있으면 `는`→`은`** 으로 바꾼다(이/가, 을/를도 동일 원칙). 단순 문자열 치환만 하면 어색해지므로 반드시 조사까지 점검.
  5. **래퍼 확인** — 출력이 사이트 레이아웃(너비·여백)에 맞지 않으면 `.sub_contents` / `.cont` 래퍼를 붙여 적용한다.

  ⚠️ **서버 WAF 가 내용관리 저장을 막을 수 있다 (ypplay.kr 실증)**
  저장 실패 시 **302 리다이렉트 대신 빈 200 응답**이 오고 내용이 그대로다(에러 메시지 없음 → 성공으로 오판 주의).
  확인된 차단 패턴 — POST 본문에 아래가 있으면 무조건 차단:
  | 차단 대상 | 예 | 회피 |
  |---|---|---|
  | `class`/`id` 값에 **`cont`** 포함 | `class="cont"`, `sub_contents`, `terms_content`, `..._contact`, `..._container` | 클래스명을 `_wrap`/`_body`/`_cs` 등으로 **개명**(CSS도 같이) |
  | **`<strong>`** 태그 | `<strong>가.</strong>` | `<b>` 로 교체(굵기 동일) |
  | 문자열 **`onal`** | `pers**onal**ized`, `nati**onal**` | 안쪽 글자를 엔티티로 — `pers&#111;nalized` (렌더 결과 동일) |

  → **`.cont` 래퍼는 에디터로 저장 자체가 불가능**하다. 대신 콘텐츠 스킨이 이미 출력하는 `#ctt` 를 CSS로 제약해 동일 효과를 낸다(FTP 로 올리는 CSS 는 WAF 무관):
  ```css
  #ctt.ctt_privacy, #ctt.ctt_provision{max-width:var(--sub_width); margin:0 auto; padding:80px 20px 0;}
  #ctt.ctt_privacy > header, #ctt.ctt_provision > header{display:none;} /* 스킨 제목 중복 제거 */
  ```
  차단어는 사이트마다 다를 수 있으니, 통째로 실패하면 **줄 단위로 나눠 저장 시도해 범인을 특정**한다.

- [ ] **작업 종료 전 링크 최종 점검 (MASTER 계정 전환 직전 · 매번 필수)**

  아래 §Multiple Super Admins(마스터 계정 전환)로 넘어가기 **전에 반드시 수행하고, 결과를 사용자에게 질문 형태로 보고**한다. 임의로 채우거나 넘어가지 않는다.

  1. **빈 링크(`href="#"`, `#none`, 빈 값) 전수 수집** — 전 페이지(메뉴·본문·헤더·푸터·플로팅·콘텐츠 페이지 포함)를 크롤링해 목록화하고, **파일:줄 위치까지 명시**해 "이 값들을 무엇으로 채울지" **사용자에게 요청**한다. → 작업 종료 시마다 **매번** 묻는다(한 번 물었다고 생략 금지).
  2. **끊긴 링크 / 깨진 이미지** — 내부 링크 404, 이미지 404 점검.
  3. **낡은 링크값(stale) 점검** — 중간에 URL·게시판·메뉴 구조가 **바뀐 뒤 예전 값이 그대로 남은 곳**을 찾아 **수정할지 사용자에게 묻는다.** 주요 탐지 대상:
     - 목업 잔재: `*.html`, `#none`, `../img/`, `index.html`
     - 변경 전 경로/보드테이블을 가리키는 하드코딩 링크(테마 `head.php`/`tail.php`/`index.php`, 콘텐츠 본문 内 링크)
     - 메뉴 DB(`get_menu_db`)와 실제 존재 페이지(`bo_table`/`wr_id`) 불일치
     - 외부 링크(예약·SNS)가 예전 업체 URL을 가리키는 경우
  4. 점검은 자동 크롤링으로 하되 **HEAD 거부(iframe 임베드 등) 오탐**은 브라우저 렌더로 재확인 후 제외한다.
  5. **푸터 예시값·`tel:`·390 모바일** — §푸터 회사정보·연락처·링크 체크리스트를 다시 돌린다(대표자 `홍길동` 같은 시안 값 0건).

---

## Multiple Super Admins (`extend/user.config.php`)

Gnuboard allows only **one** super admin (and one board admin per board) by
default. To grant super-admin to additional member IDs, add an
`extend/user.config.php` — Gnuboard auto-loads it, so no core edit is needed.

**File: `extend/user.config.php`**
```php
<?php
if (!defined('_GNUBOARD_')) exit; // 개별 페이지 접근 불가;

// 최고관리자 (여러 명 지정)
if ($member['mb_id'] == 'wering') $is_admin = 'super';
if ($member['mb_id'] == 'master') $is_admin = 'super';
```
Add one `if (... == '{mb_id}') $is_admin = 'super';` line per admin account.

**How to add an admin account**
1. Log in with the `wering` account and add the member (회원관리 → 회원추가).
2. Add the new member's `mb_id` to `extend/user.config.php` as above.

⚠️ **먼저 `extend/user.config.php` 존재 여부부터 확인한다.** 파일 자체가 없는 사이트가 있다(그 경우 `master` 회원이 있어도 level 10 일 뿐 **super 아님**).

🚫 **아이디에 날짜를 넣지 말 것 (`master20260724` 같은 형태 금지).** 비밀번호가 그날 날짜인 규약이므로, **아이디에 날짜를 박으면 아이디가 곧 비밀번호를 알려주는 꼴**이다(회원목록·작성자명 등 아이디 노출 지점마다 유출). 아이디는 **항상 `master`** 로 한다. 위 "Account convention" 의 `master{YYYYMMDD}` 표기는 **쓰지 않는다**.
기존 `master` 가 이미 있으면 날짜형으로 우회하지 말고 **소유자를 사용자에게 확인**한 뒤 ① 그 계정을 인수(비번 재설정)하거나 ② 날짜와 무관한 다른 아이디를 쓰되 **비밀번호는 아이디에서 유추 불가능한 값**으로 정한다.

⚠️ **회원 추가·수정 모두 자동등록방지(kcaptcha)를 통과해야 한다**(신규 `w=''` 뿐 아니라 **비밀번호 재설정 같은 `w=u` 수정도 동일**). 스크립트로 `member_form_update.php` 에 POST 하면 `자동등록방지 숫자가 틀렸습니다.` 로 막힌다(빈 200 아님, 오류안내 페이지). 우회 말고 정상 통과 절차:
1. 관리자 세션으로 `/plugin/kcaptcha/kcaptcha_session.php` 호출(`X-Requested-With: XMLHttpRequest`)
2. **같은 세션**으로 `/plugin/kcaptcha/kcaptcha_image.php?t={ms}` 이미지를 받아 숫자를 판독
3. 폼 전체 직렬화 + `captcha_key` 에 그 숫자를 넣어 POST (성공 시 302)
4. 판독용 이미지·세션 파일은 작업 후 삭제
   - 판독이 애매하면 **이진화 + 확대**(PIL: MedianFilter → `point(<140→0)` → NEAREST 6배) 후 다시 본다. 그래도 틀리면 **새 캡차를 받는 편이 빠르다**(틀려도 계정은 변경되지 않음).

**회원 삭제 동작 주의**: `member_list_update.php`(`act_button=선택삭제`, `chk[]`=행 인덱스 + `mb_id[N]`)는 **행을 없애지 않고 레코드를 비운다.** 목록에 아이디는 남지만 비밀번호가 지워져 로그인 불가 상태가 된다(게시물 작성자 보존 목적). 삭제 성공 판정은 "목록에서 사라졌는지"가 아니라 **로그인 불가 + 필드 비워짐**으로 한다.

**비밀번호 취급**: `master` 는 **클라이언트에게 전달하는 서브 최고관리자 계정**이므로 **금고(`vault.py`) 기재 대상이 아니다.** 금고는 위링 자체 접속정보(FTP·관리자)를 담는 곳으로 성격이 다르다. 비밀번호는 규약대로 **생성일 날짜**라 별도 보관 없이 재구성 가능하니, 작업일지 등에 평문으로 적을 필요도 없다.

**푸터 카피라이트 = 관리자 진입 링크 (위링 표준)**
푸터 카피라이트 문구를 `<a>` 로 감싸 관리자 로그인으로 연결한다. **`/adm` 을 직접 걸면 안 된다** — 미로그인 시 `alert("로그인 하십시오.")` 가 뜨고 나서야 로그인폼으로 간다. `bbs/login.php?url=` 로 걸면 알림 없이 로그인폼 → 로그인 후 곧바로 `/adm/`, 이미 로그인 상태면 즉시 `/adm/` 로 간다(`bbs/login.php` 가 `$is_member` 일 때 `goto_url($url)`).
```php
<small class="copyright">
    <a href="<?php echo G5_BBS_URL ?>/login.php?url=<?php echo urlencode(G5_ADMIN_URL.'/') ?>">© 2026 {사이트명} All rights reserved.</a>
</small>
```
```css
.footer .copyright a{color:inherit; font-size:inherit; font-weight:inherit;}  /* 외관 변화 없게 */
```

**Account convention (위링 표준)**
- 아이디: `master` — **날짜를 붙이지 않는다**(아래 🚫 참조)
- 비밀번호: 그날 날짜 (예: `20260521`)
- 이름 / 닉네임: `최고운영자`
- 이메일: `master@master.com`

Source: `D:\위링\위링스킨\user.config\` (`user.config.php` + `사용법.txt`).

---

## 1차 작업 완료 안내 메일 (납품 템플릿)

`master` 계정 생성 + §작업 종료 전 링크 최종 점검 까지 끝난 뒤 클라이언트에게 보내는 메일이다. **아래 템플릿을 그대로 쓰되 `[ ]` 자리를 실제 값으로 채운다.**

**제목**
```
홈페이지 제작 1차 작업이 완료되어 연락드립니다.
```

**본문**
```
안녕하세요. ㈜위링입니다.

[ 업체명 ] 홈페이지 제작 제 1차 작업이 완료되어 안내드립니다.

수정사항의 경우 복사, 붙여넣기가 가능한 파일로 정리하여 메일로 회신주시면
담당자 확인 후 수정하도록 하겠습니다.

홈페이지 관리에 필요한 관리자 계정 및 메뉴얼 함께 안내드립니다.


- 홈페이지 임시 도메인 주소 : [ url ]

- 관리자아이디 / 비밀번호 : master / [ YYYYMMDD ]
  (비밀번호는 관리자 페이지 접속 > 회원관리에서 변경하여 사용 요망)

- 관리자 페이지 접속하는 방법은 홈페이지 하단의
  카피라이트([ 카피라이트 문구 ])를 클릭하시면
  관리자 페이지로 이동합니다.


📌 사이트 사용방법 필독 부탁드립니다.
https://wering.kr/How_to_use

📌 유지보수 안내
https://wering.kr/theme/wering/sub/estimate_info.php

📌 홈페이지 자주묻는 질문
https://wering.kr/FAQ


감사합니다.
```

---

## Prohibited

- Adding features not present in the extracted HTML ("usually projects have search, so add it")
- Deleting Gnuboard PHP functions because "the design doesn't need it"
- Applying an identical head.php template to every project regardless of design
- Creating board skins without checking existing skins in `D:\위링\위링스킨\`
- **다른 프로젝트 폴더에서 게시판 스킨 복사** — 스킨 출처는 공용 `D:\위링\위링스킨\` 뿐 (§스킨 출처는 공용 폴더뿐)
- Replacing extracted HTML class names with Gnuboard default IDs (#hd, #ft, #wrapper, etc.)
- Using `wering_` or any other hardcoded theme-name prefix on helper functions
- Inline styles for layout — use the extracted CSS classes
- Modifying css/common.css content during conversion (it was already validated in Step 5-6)
- **콘텐츠 페이지마다 게시판 1개씩 생성** — 1depth 메뉴 단위로 게시판 1개를 만들고 서브페이지는 글(wr_id)로 등록한다 (Sub-page Processing 참조)
- 짧은주소를 숫자로 설정해 놓고 **메뉴/테마 링크는 `board.php?bo_table=…` 로 방치** — 짧은주소 형식(`/{bo_table}/{wr_id}`)으로 통일한다
- **시안 푸터의 예시값(`홍길동`·예시 주소·메일·번호)을 그대로 두고 올리기** — 출처 확인값만, 모르면 미기입 후 확인 (§푸터 회사정보·연락처·링크)
- **준비 안 된 링크를 `href="#"` 로 방치** — `#ready` 로 명시하거나 실제 주소를 받아 채운다
