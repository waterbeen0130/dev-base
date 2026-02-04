# Codex Rules

Rules for GitHub Copilot, Cursor, and other Codex-based AI.

---

## Base
- Apply `common.md` rules first
- Code comments: English only

---

## Code Style

### HTML
- Semantic tags
- Indentation: 4 spaces
- Follow BEM or project naming convention

### CSS
- **Single line format** for rules
- Indentation: 4 spaces (for media query blocks)
- Class names: kebab-case
- Use shorthand properties

### JavaScript
- ES6+ syntax
- Indentation: 4 spaces
- Use semicolons
- Use const/let (no var)

---

## Autocomplete Hints

### Comment for Intent
```javascript
// remove duplicates from array
const unique = [...new Set(arr)];

// format date as YYYY-MM-DD
const formatDate = (date) => { ... }
```

### Function Names
- `getUserById` - get user by ID
- `validateEmail` - validate email format
- `formatPrice` - format price with comma

---

## Preferred Patterns

### Conditionals
```javascript
// ternary for simple cases
const status = isActive ? 'active' : 'inactive';

// early return for complex cases
if (!user) return null;
```

### Loops
```javascript
// prefer map, filter, reduce
const names = users.map(user => user.name);
const adults = users.filter(user => user.age >= 18);
```

### Async
```javascript
// prefer async/await
const data = await fetchData();
```

---

## Avoid
- Deep nesting
- Magic numbers/strings
- Over-abstraction
- Unnecessary dependencies
- Multi-line CSS format
