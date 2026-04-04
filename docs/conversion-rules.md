# Conversion Rules: Figma -> Normalized Intermediate JSON

## Layout

| Figma | Output path | Rule |
|---|---|---|
| `layoutMode: VERTICAL` | `layout.direction` | `column` |
| `layoutMode: HORIZONTAL` | `layout.direction` | `row` |
| `layoutMode` present | `layout.display` | `flex` |
| `layoutMode` absent | `layout.display` | `block` |
| `itemSpacing` | `layout.gap` | `>1 -> Npx`, else `0` |
| `paddingTop/Right/Bottom/Left` | `layout.padding` | CSS shorthand (1/2/4-value) |
| `primaryAxisAlignItems` | `layout.justify` | `MIN/CENTER/MAX/SPACE_BETWEEN -> flex-start/center/flex-end/space-between` |
| `counterAxisAlignItems` | `layout.align` | `MIN/CENTER/MAX/BASELINE/STRETCH -> flex-start/center/flex-end/baseline/stretch` |
| `layoutSizingHorizontal` | `layout.sizing.horizontal` | Preserve enum (`FILL/HUG/FIXED`) |
| `layoutSizingVertical` | `layout.sizing.vertical` | Preserve enum (`FILL/HUG/FIXED`) |

## Visual

| Figma | Output path | Rule |
|---|---|---|
| `absoluteBoundingBox.width/height` (fallback `width/height`) | `visual.width`, `visual.height` | Rounded number |
| `fills[]` first visible `SOLID` | `visual.background` | RGBA(0-1) -> hex or `rgba()` |
| visible `strokes[]` only | `visual.border` | `strokeWeight px solid color` |
| no visible stroke | `visual.border` | `null` |
| `cornerRadius` or `rectangleCornerRadii` | `visual.borderRadius` | px string or 4-value shorthand |
| circle heuristic (`w≈h` and `r>=w/2`) | `visual.borderRadius` | `50%` |
| pill heuristic (`w>h` and `r>h/2`) | `visual.borderRadius` | `2em` |
| `opacity` | `visual.opacity` | Preserve float (default `1.0`) |

## Typography

| Figma | Output path | Rule |
|---|---|---|
| `characters` | `text.content` | Preserve original text |
| `characters` includes `\n` | `text.has_newline` | `true` |
| `len(characters)` | `text.char_length` | Integer length |
| default tag | `text.tag_hint` | `span` |
| paragraph heuristic | `text.tag_hint` | `p` when newline, long text (`>95`), or sentence-like ending |
| heading heuristic | `text.tag_hint` | `h2/h3` when node name indicates title/heading |
| `style.fontFamily` | `text.segments[].style.fontFamily` | Preserve |
| `style.fontWeight` | `text.segments[].style.fontWeight` | Preserve |
| `style.fontSize` | `text.segments[].style.fontSize` | Profile-aware unit conversion |
| `style.lineHeightPx` | `text.segments[].style.lineHeight` | Unitless ratio `lineHeightPx / fontSize` |
| `style.letterSpacing` | `text.segments[].style.letterSpacing` | `em` unit `letterSpacing / fontSize` |
| text fill color | `text.segments[].style.color` | RGBA(0-1) -> hex/rgba |
| `style.textAlignHorizontal` | `text.segments[].style.textAlign` | LEFT/CENTER/RIGHT/JUSTIFIED -> left/center/right/justify |
| `style.textDecoration` | `text.segments[].style.textDecoration` | UNDERLINE/STRIKETHROUGH -> underline/line-through |

## Character Override Resolution

| Step | Rule |
|---|---|
| Base style | `baseStyle = { ...node.style, fills: node.fills }` |
| Segment split | Group contiguous characters by same `characterStyleOverrides` id |
| `id=0` or missing table entry | Resolved style = `baseStyle` |
| other id | Resolved style = `{ ...(prevResolved || baseStyle), ...override }` (cumulative merge) |
| segment output | Store fully converted CSS style in each `segments[]` entry |
| override marker | `is_override = segment_style != base_style` |

## Node Preservation

| Condition | Rule |
|---|---|
| `visible: false` | Exclude (only exclusion rule) |
| thin fill-only frame (`w<=2` or `h<=2`) | Preserve as normal node (divider candidate) |
| decorative/background/icon nodes | Preserve |
| empty visible frame | Preserve |

## Profile Rules

| Profile | PC font-size | Mobile font-size | reset_css | required_root_vars |
|---|---|---|---|---|
| `basic` | `rem` (`rem_base=16`) | `px` | `separate_file` | `--width`, `--padding` |
| `landing` | `px` | `px` | `inline_top_of_css` | `--padding`, `--header_h`, `--width`, `--point-color-1` |

Additional profile metadata is loaded from `tools/profiles/<profile>.json` and emitted into `meta.profile` through CLI selection.
