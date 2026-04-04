# Post-Extraction Enhancement Flow

Figma extraction and publishing complete → automatic enhancement analysis and execution.

> Reference: `css-enhancement.md` §7 (7-Phase checklist), §8 (dependency graph), §9 (color variable pattern)

---

## 1. Trigger Conditions

Enhancement flow is triggered when:
- **Auto**: Figma extraction REQ reaches Phase 5 (done) — PM automatically runs analysis
- **Manual**: User requests `/mst:plan --enhance`
- **Scope**: Publishing projects only (HTML/CSS/JS)

---

## 2. Auto-Detection Patterns

PM runs these grep/search patterns against the project's CSS/HTML files to detect enhancement candidates.

### 2.1 기초 (Phase 1 candidates)

```bash
# Empty selectors (rules with no declarations)
grep -Pn '\{[\s]*\}' css/common.css

# Duplicate selectors (same selector declared multiple times)
grep -oP '^\.[a-zA-Z_][\w-]*(?=\s*\{)' css/common.css | sort | uniq -d

# AI-generated reset.css detection (Eric Meyer / normalize.css signatures)
grep -l 'Eric Meyer\|normalize.css\|html,body,div,span' css/reset.css

# :root variable existence
grep -c ':root' css/common.css

# Duplicate @import or @font-face
grep -c '@import\|@font-face' css/common.css
```

### 2.2 구조 (Phase 2-3 candidates)

```bash
# body/html specificity hacks in media queries
grep -Pn '(body|html)\s+\.' css/common.css

# @media format inconsistency (missing 'screen and')
grep -Pn '@media\s*\(max-width' css/common.css

# Media queries clustered at file bottom (>5 consecutive @media blocks)
grep -n '@media' css/common.css | tail -20

# Leading whitespace in media query content
grep -Pn '^\s+\.' css/common.css | head -20

# Container width pattern (no max-width usage)
grep -c 'max-width' css/common.css
```

### 2.3 시멘틱 (Phase 4 candidates)

```bash
# nav > a without ul wrapper
grep -Pn '<nav[^>]*>[\s]*<a' *.html

# div > a repeated pattern (list-like links without ul)
grep -Pn '<div[^>]*>[\s]*(<a[^>]*>.*</a>[\s]*){2,}' *.html

# Footer menu without ul
grep -A5 '<footer' *.html | grep -P '<a[^>]*>'

# Individual class on every element (class density check)
grep -oP 'class="[^"]*"' *.html | wc -l
```

### 2.4 반응형 (Phase 5 candidates)

```bash
# Fixed height values (potential aspect-ratio candidates)
grep -Pn 'height:\s*\d{3,}px' css/common.css

# Fixed width in flex children
grep -Pn 'width:\s*\d{3,}px' css/common.css
```

### 2.5 품질 (Phase 6-7 candidates)

```bash
# Hardcoded color frequency
grep -oP '#[0-9a-fA-F]{3,8}' css/common.css | sort | uniq -c | sort -rn | head -20

# border-radius 999px or 120px
grep -Pn 'border-radius:\s*(999|120)px' css/common.css

# Script without defer
grep -Pn '<script[^>]*src=[^>]*(?<!defer)>' *.html

# Script position (should be in <head>, not before </body>)
grep -n '</body>' *.html
grep -B3 '</body>' *.html | grep '<script'
```

---

## 3. Analysis Report Format

PM generates a summary report for user review before proceeding:

```markdown
## Enhancement Analysis Report

**Project**: {project_name}
**Files analyzed**: {file_list}
**Date**: {date}

### Detected Issues

| Phase | Category | Count | Severity | Details |
|-------|----------|-------|----------|---------|
| 1 | Empty selectors | N | Low | Lines: ... |
| 1 | AI reset.css | 1 | Medium | reset.css is not template version |
| 3 | Specificity hacks | N | High | body/html prefix in N selectors |
| 3 | Media format | N | Medium | Missing 'screen and' in N queries |
| 4 | Missing ul>li | N | High | nav>a pattern in N locations |
| 7 | Hardcoded colors | N | Medium | N unique colors, top: #xxx (Nuses) |

### Recommended Plan

Phase 1: ~{estimate} changes
Phase 2: ~{estimate} changes
...

### Skipped (no issues detected)
Phase N: {reason}
```

---

## 4. Auto-PLN / REQ Generation

### PLN structure

```
PLN-ENH-{project}
├── REQ-ENH-01: Phase 1 — 기초 설정 (reset, :root, fonts)
├── REQ-ENH-02: Phase 2 — 레이아웃 정규화 (max-width, containers)
├── REQ-ENH-03: Phase 3 — 미디어쿼리 구조 정리
├── REQ-ENH-04: Phase 4 — 시멘틱 마크업 변환
├── REQ-ENH-05: Phase 5 — 반응형 유연성 확보
├── REQ-ENH-06: Phase 6 — 성능/표준
└── REQ-ENH-07: Phase 7 — CSS 품질 정제
```

### REQ generation rules

- Each Phase becomes one REQ (unless Phase has 0 detected issues → skip)
- REQ dependencies follow §8 dependency graph:
  - REQ-ENH-02, REQ-ENH-03: depends on REQ-ENH-01
  - REQ-ENH-04: depends on REQ-ENH-02, REQ-ENH-03
  - REQ-ENH-05: depends on REQ-ENH-03, REQ-ENH-04
  - REQ-ENH-06: depends on REQ-ENH-04
  - REQ-ENH-07: depends on all previous
- Parallel execution: Phase 2 + 3 can run concurrently, Phase 5 + 6 can run concurrently
- Assigned agent: follows project config (`default_agent` in config.json)

### REQ template

```markdown
# REQ-ENH-{NN}: Phase {N} — {phase_title}

## Depends on
{list of dependency REQs}

## Scope
{list of files to modify}

## Tasks
{checklist items from css-enhancement.md §7, filtered to detected issues only}

## Detection results
{grep output from auto-detection step}

## Rules
See: css-enhancement.md §7 Phase {N}
See: common.md (CSS formatting rules)
```

---

## 5. Execution Flow

```
[Figma REQ done]
      │
      ▼
[PM: Run auto-detection patterns]
      │
      ▼
[PM: Generate analysis report]
      │
      ▼
[PM: Present to user for approval]
      │
      ├── User: "proceed" ──────────────► [Generate PLN + REQs]
      │                                         │
      │                                         ▼
      │                                   [Execute Phase 1]
      │                                         │
      │                                         ▼
      │                                   [Execute Phase 2+3 (parallel)]
      │                                         │
      │                                         ▼
      │                                   [Execute Phase 4]
      │                                         │
      │                                         ▼
      │                                   [Execute Phase 5+6 (parallel)]
      │                                         │
      │                                         ▼
      │                                   [Execute Phase 7 (final)]
      │                                         │
      │                                         ▼
      │                                   [Run validate.js]
      │
      ├── User: "skip" ────────────────► [No enhancement]
      │
      └── User: "partial" ─────────────► [Generate selected Phases only]
```

---

## 6. Post-Enhancement Validation

After all enhancement Phases complete:

```bash
# Standard validation
node D:/dev-base/tools/validate.js --html *.html --css css/common.css --type {project_type}

# With mapping (if available from extraction phase)
node D:/dev-base/tools/validate.js --html *.html --css css/common.css --mapping ./extracted/*_mapping.json --type {project_type}
```

Check:
- No regressions in figma value matching
- All enhancement rules applied (empty selectors, specificity, format)
- Visual regression: browser screenshot comparison (optional, via Playwright)
