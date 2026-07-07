# Gnuboard Skin Rules

HTML/CSS code extraction output to Gnuboard5 theme conversion rules.
Theme base: `theme/wering/` (project-specific customization per site).

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
□ Full-screen menu overlay (.all_menu, #gnb_all)

[Footer]
□ Company info (.footer_info, dl/dt/dd blocks)
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

[Conditional — only if the feature was detected and applied]
□ GNB detected → get_menu_db() call exists in head.php
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
3. Viewport meta if not already present:
   ```php
   <meta name="viewport" content="width=device-width, user-scalable=0, initial-scale=1, minimum-scale=1, maximum-scale=1" />
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
- Company info: use design HTML as-is, convert image paths
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

---

## Module Catalog

Each module is independent. Apply only if the feature was detected in Phase 1.

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

### Workflow
1. Identify sub-pages from extracted HTML (all pages except index.html)
2. For each sub-page, extract only the content area:
   - Exclude: header, footer, sub_visual (head.php generates these)
   - Include: everything between sub_visual and footer
3. Convert image paths to server absolute paths
4. Output: one HTML file per sub-page, ready to paste into board post (wr_content)
5. Board setup (manual in admin): create board → apply we_js skin → write post → link from GNB menu

### we_js Skin Behavior
The `we_js` view skin renders `wr_content` as raw HTML without board UI chrome.
This enables full-design pages within the board system for SEO/RSS/search benefits.

### Board Skin Selection Guide
Choose skins based on the page function detected in extracted HTML:

| Page function | Recommended skin | Notes |
|--------------|-----------------|-------|
| Static content page (intro, about) | we_js | raw HTML rendering |
| Notice / news list | we_notice or we_basic | list + view with date/hit |
| Gallery / portfolio | we_gallery | thumbnail grid + lightbox |
| Contact / inquiry form | we_inquiry | form fields + submission |
| FAQ | we_faq | accordion UI |
| Map / directions | we_js + map script | raw HTML with map embed |

Do not create custom board skins unless the project design requires UI that
no existing skin supports. Check `D:\위링\위링스킨\` for available skins first.

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

## Prohibited

- Adding features not present in the extracted HTML ("usually projects have search, so add it")
- Deleting Gnuboard PHP functions because "the design doesn't need it"
- Applying an identical head.php template to every project regardless of design
- Creating board skins without checking existing skins in `D:\위링\위링스킨\`
- Replacing extracted HTML class names with Gnuboard default IDs (#hd, #ft, #wrapper, etc.)
- Using `wering_` or any other hardcoded theme-name prefix on helper functions
- Inline styles for layout — use the extracted CSS classes
- Modifying css/common.css content during conversion (it was already validated in Step 5-6)
