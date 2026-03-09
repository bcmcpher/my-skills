---
name: write-unit-tests
description: >
  Write comprehensive unit tests for a source code file using a TDD workflow: plan full
  coverage first, then implement tests one unit at a time to stay focused and minimize
  context bloat. Use this skill when the user wants to add unit tests, improve test coverage,
  write tests for a function or class, or work through a TDD red-green cycle. Invoke for
  prompts like "write tests for X", "add test coverage to this file", "test this module",
  "generate unit tests", "/write-unit-tests", or when the user is working through a test
  TODO list and needs to tackle the next item.
argument-hint: <source-file>
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Skill: write-unit-tests

Write well-structured unit tests for a source file using a focused, iterative TDD workflow.
The design principle: plan coverage for the whole file upfront, then implement one unit at a
time — pausing between units to keep context lean and attention sharp.

## Phase 1: Plan (first invocation for a file)

Before doing anything, check whether a TODO file already exists for this source file (see
Naming below). If one exists, skip directly to Phase 2.

**Step 1 — Detect language and load reference**

Identify the language from the file extension and read the corresponding reference file from
`references/` for framework-specific conventions (test runner, file naming, AI marker style):

| Extension | Reference file |
|---|---|
| `.py` | `references/python.md` |
| `.js`, `.mjs`, `.cjs` | `references/javascript.md` |
| `.ts`, `.tsx` | `references/typescript.md` |
| `.r`, `.R` | `references/r.md` |
| `.c`, `.cpp`, `.cc`, `.h`, `.hpp` | `references/c_cpp.md` |
| `.rs` | `references/rust.md` |

If the language isn't listed, apply generic TDD principles and use `# AI-Generated` as the marker.

**Step 2 — Inventory testable units**

Read the source file and list every testable unit:
- Module-level functions
- Class methods (focus on the public interface)
- For each: note the happy path, any edge cases visible from the signature or docstring
  (None/null inputs, empty collections, boundary values), and error states (exceptions, invalid types)

**Step 3 — Write the TODO file**

Create `<source-dir>/write-unit-tests-todo.md` with this format:

```markdown
# Test TODO: <source-file>
Language: <language>
Test file: <test-file-path>
Generated: <date>

## Units
- [ ] `function_name` — happy path; edge case: <describe>; error: <describe>
- [ ] `ClassName.method` — happy path; edge case: <describe>
- [ ] `ClassName.__init__` — valid args; invalid args raise TypeError
```

**Step 4 — Begin immediately**

Tell the user "I've planned N units in `<todo-file>`. Starting unit 1 now..." then
proceed directly to Phase 2 without waiting.

---

## Phase 2: Execute (one unit per turn)

Read the TODO file. Find the first unchecked item (`- [ ]`). If all items are checked,
tell the user all units are covered and stop.

The goal here is to stay focused. Only load the source context needed for the current unit —
not the whole file. This keeps each turn efficient and lets the tests be written with full
attention on one thing.

**Step 1 — Load minimal source context**

Use Grep or a targeted Read (with line offset and limit) to load just the function or class
body for the current unit. Avoid re-reading the entire file.

**Step 2 — Check the test file**

If a test file already exists (see Naming), read it briefly to understand the existing
structure and confirm you won't duplicate anything. Never modify or delete existing tests.

**Step 3 — Write a failing test first**

Write a test that exercises a boundary condition or incorrect input that should fail (or tests
behavior not yet implemented). Run it with the test runner to confirm it actually fails.
This is the "red" step — it proves the test is meaningful, not a false positive.

**Step 4 — Write the passing tests**

Write tests for the happy path, then the remaining edge cases and error states from the TODO.
Run all new tests and confirm they pass. This is the "green" step.

**Step 5 — Mark done and pause**

Update the TODO: change `- [ ]` to `- [x]` for the completed unit.

Report to the user:
- Which unit is done
- How many tests were written (pass/fail counts)
- What's next in the TODO

Then ask: **"Ready to continue with the next unit?"** — this is an intentional pause.
Starting the next unit in the same context would carry over source code and test code that's
no longer needed. The user can reply "yes/continue" or invoke `/write-unit-tests` again to
start fresh with only the TODO loaded.

---

## Naming conventions

**TODO file:** `<source-dir>/write-unit-tests-todo.md`
- `src/utils.py` → `src/write-unit-tests-todo.md`

**Test file:** Follow language conventions from the reference file.
- Python default: `tests/test_<module>.py` (or `test_<module>.py` alongside source)
- If a test file already exists, append to it. Never delete existing tests.

---

## Marking AI-generated tests

Mark every test you write so humans can quickly audit and verify AI-generated coverage.
Each language has a preferred style — see the reference file. The generic fallback is a
`# AI-Generated` comment directly above the test function.

Never apply AI-generated markers to tests that already exist in the file.

---

## Core constraints

- **Never modify or delete existing tests** — only append.
- **Never change source code** to make tests pass. If a test fails due to a source bug,
  note it in a comment and mark the test as `xfail` (or language equivalent). Move on.
- **One unit per turn** — resist the urge to batch. The pause between units is intentional.
- **Always run tests** after writing to confirm the red-green cycle.
- **Load only what you need** — targeted reads, not full-file loads during execution.
