# Claude Code Status Line Reference

The status line is a customizable string displayed in the Claude Code UI during a session.
Configure it in `settings.json` (global or project scope).

---

## Configuration

```json
"statusLine": {
  "type": "command",
  "command": "bash ~/.claude/statusline-command.sh"
}
```

The command runs on each UI refresh. It must be fast (< 100 ms) — avoid network calls or
slow subprocess chains.

---

## Command contract

**Input:** JSON object delivered via **stdin** (read with `cat` or equivalent).

**Output:** A single string printed to **stdout**, optionally with ANSI escape codes for
color. Trailing newline is fine; extra lines are ignored.

The script must exit 0. Non-zero exits or stderr output suppress the status line for that
tick without crashing the session.

---

## Available fields (stdin JSON)

| JSON path | Type | Description |
|---|---|---|
| `.workspace.current_dir` | string | Absolute path of the current working directory |
| `.cwd` | string | Fallback if `.workspace.current_dir` is absent |
| `.model.display_name` | string | Human-readable model name (e.g., `"claude-opus-4-6"`) |
| `.context_window.remaining_percentage` | number | % of context window remaining (0–100) |

Use `// empty` or `// ""` in `jq` to handle absent fields gracefully:

```bash
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
```

---

## Example script

The ready-to-use script is at `config/statusline-command.sh` in this repo.
It mirrors a bash PS1 prompt and appends model + context info:

```
bcmcpher@hostname:/path/to/project [claude-opus-4-6 | ctx: 74% left]
```

Copy it to `~/.claude/statusline-command.sh` and make it executable:

```bash
cp config/statusline-command.sh ~/.claude/statusline-command.sh
chmod +x ~/.claude/statusline-command.sh
```

---

## Tips

- **Color codes**: use `printf "\033[01;32m...\033[00m"` for ANSI color in terminals that support it
- **Scope**: put `statusLine` in `~/.claude/settings.json` for a personal global status line;
  put it in `.claude/settings.json` for a project-specific one
- **Disabling**: remove the `statusLine` block or set `"type": "none"` to disable
- **Debugging**: test the script directly with sample JSON piped to stdin:
  ```bash
  echo '{"workspace":{"current_dir":"/tmp"},"model":{"display_name":"test"},"context_window":{"remaining_percentage":80}}' \
    | bash ~/.claude/statusline-command.sh
  ```
