# Common Rules

All AI assistants should follow these rules.

---

## Language Settings
- Response language: **Korean**
- Code comments: **English only**
- Variable/Function names: English (camelCase or snake_case)

---

## Coding Style

### General
- Indentation: **4 spaces**
- No inline styles/scripts
- Follow existing project conventions first

### HTML
- Use semantic tags (`<header>`, `<main>`, `<section>`, `<article>`, `<footer>`)
- All images must have `alt` attribute
- Buttons must have `type="button"`
- Form elements must be linked with `<label>`

### CSS
- **Write rules in single line format** (except media queries block)
- Use `rem` for font-size
- Use `clamp()` for padding/margin (except gap and buttons)

```css
/* Correct - single line */
.section_name { position: relative; padding: clamp(45px, calc(90 / 1920 * 100vw), 90px); width: 100%; }

/* Correct - media query block with single line rules */
@media screen and (max-width: 768px) {
    .section_name { padding: 40px 20px; }
    .section_name .title { font-size: 1.25rem; }
}

/* Wrong - multi-line */
.section_name {
    position: relative;
    padding: 90px;
}
```

### CSS Property Order
1. position related
2. margin
3. padding
4. width/height
5. display
6. alignment
7. background
8. font-size
9. font-weight
10. color
11. others

### JavaScript
- Indentation: 4 spaces
- Use single quotes (`'`)
- Use semicolons
- Use `const` first, `let` if needed (no `var`)
- Prefer arrow functions

---

## Breakpoints
- PC: 1200px+
- Tablet: 769px ~ 1199px
- Mobile: 768px-

---

## File Structure
```
project/
├── index.html
├── css/
│   ├── reset.css
│   └── common.css
├── js/
│   └── ui_common.js
└── img/
```

---

## Important
- Do not add unrequested features
- Do not refactor without permission
- Keep minimal changes
- Watch for security issues (XSS, etc.)

---

## Reference
- See `basic_rules.md` for detailed HTML/CSS patterns
