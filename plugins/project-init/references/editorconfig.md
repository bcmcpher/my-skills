# EditorConfig Reference

## What `.editorconfig` controls

A `.editorconfig` file at the project root enforces consistent editor behavior across
all contributors and editors that support it (VS Code, JetBrains, Vim, Emacs, and
many others — natively or via plugin):

| Property | Effect |
|---|---|
| `indent_style` | `space` or `tab` |
| `indent_size` | Number of spaces (or tab display width) |
| `end_of_line` | `lf`, `crlf`, or `cr` |
| `charset` | `utf-8`, `utf-8-bom`, `latin1`, etc. |
| `trim_trailing_whitespace` | Remove trailing spaces on save |
| `insert_final_newline` | Ensure file ends with a newline |

---

## Per-language recommended settings

| Language | `indent_style` | `indent_size` | Notes |
|---|---|---|---|
| Python | space | 4 | PEP 8 |
| JavaScript | space | 2 | Ecosystem default |
| TypeScript | space | 2 | Ecosystem default |
| Rust | space | 4 | rustfmt default |
| Go | tab | 4 | gofmt enforces tabs; size is display-only |
| R | space | 2 | tidyverse style guide |

---

## Minimal scaffold

Replace `<ext>` with the language's file extension (`.py`, `.js`, `.ts`, `.rs`, `.go`,
`.R`). Adjust `indent_style` and `indent_size` from the table above.

```ini
# EditorConfig: https://editorconfig.org
root = true

[*]
charset = utf-8
end_of_line = lf
trim_trailing_whitespace = true
insert_final_newline = true

[*.<ext>]
indent_style = <space|tab>
indent_size = <2|4>
```

For Go, use `tab` with `indent_size = 4` (tab display width):

```ini
[*.go]
indent_style = tab
indent_size = 4
```

For projects with multiple languages, add one `[*.<ext>]` block per language.
