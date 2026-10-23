# Audit dimensions

Each dimension has one question, one script, and one judgment rule. `<py>` is the project
interpreter. `<s>` is the scripts directory. Paths assume `src/<pkg>`, `tests/` and
`openspec/specs/`; change them to fit the repository.

## Area A: source

### A-dup — duplicated logic

- **Question:** Is the same logic written more than once, or re-implemented beside a
  shared helper that already does it?
- **Script:** `<py> <s>/dup_logic.py src/<pkg> --helpers src/<pkg>/utils`
- **Candidates:** identical bodies; bodies that differ only in constants; repeated
  3-statement blocks across functions; optional-import guards; clusters touching a helper.
- **Judge:** A finding when one helper could serve every site with no new parameter
  beyond the differing constant. Reject symmetric pairs that a recorded decision keeps
  apart (for example, "extract at the third copy"), and say which rule.

### A-api — public API with no non-test caller

- **Question:** Which public definitions are called only by tests, or by nothing?
- **Script:** `<py> <s>/public_callers.py src/<pkg> --tests tests --extra examples`
- **Judge:** Keep when the docstring presents it as user API, a spec requires it, or it
  is exported. Otherwise a removal finding (pre-release) or a "make it private" finding.
  The script matches by name, so a common name hides a dead definition: note that limit.

### A-err — error taxonomy

- **Question:** Does one kind of check raise different exception types at different sites?
- **Script:** `<py> <s>/raise_taxonomy.py src/<pkg>`
- **Judge:** The kind classification is heuristic. Re-classify misfiled sites first, then
  report each kind that still mixes types, with the count per type. A value-changing fix.

### A-doc — docstrings against signatures

- **Question:** Do documented names, defaults and allowed values match the signature?
- **Script:** `<py> <s>/docstring_signature.py src/<pkg>`
- **Judge:** "documented value not accepted" is a finding unless the quoted word is not a
  value (a function name, a key). Undocumented arguments are one row with the count.

### A-size — module split points

- **Question:** Where would each large module split?
- **Script:** `<py> <s>/inventory.py src/<pkg> --outline-min 1500`
- **Judge:** For each outlined module, name its responsibilities and the split points by
  line range, or say why it stays whole (a facade, one class, one algorithm).

### A-leak — private access across modules

- **Question:** Does code reach through another object's `_attributes`, or does a public
  protocol name private members?
- **Script:** `rg -n '\b(?!self\b|cls\b)\w+\._[a-z]\w*' src/<pkg>` plus reading protocols.
- **Judge:** A finding when a public accessor exists or should exist.

## Area B: tests

### B-dup — near-duplicate tests

- **Question:** Which tests differ only in an argument, an accessor or a fixture?
- **Script:** `<py> <s>/test_near_dupes.py tests`
- **Judge:** One row per *kind* (argument, accessor, class pair), listing files and
  counts. Reject clusters whose differences are the point (each case pins a distinct
  requirement scenario). Already-parametrized tests are marked.

### B-cov — coverage-subset tests

- **Question:** Which tests are made redundant by a stronger test of the same requirement?
- **Script:** `<py> <s>/coverage_subsets.py .coverage`
- **Judge:** Read the "coverage and assertion subset" group in full. For each, state
  what the weaker test asserts that the stronger does not. Report it only if the answer
  is "nothing" (same input, same assertion). Give candidates read and rejected.

### B-priv — tests of implementation detail

- **Question:** Which tests import private names or read private attributes?
- **Script:** `<py> <s>/test_private_access.py tests --src src/<pkg>`
- **Judge:** Deliberate pins (a stated reason) stay. Incidental ones get a public route
  or a stated reason. Report per file, separating marked from unmarked.

### B-size — fixtures and file size

- **Script:** `<py> <s>/inventory.py tests --outline-min 1500`
- **Judge:** Split points for oversized files and for the shared `conftest.py`.

## Area C: specs (OpenSpec)

### C-inv — capabilities and requirements

- **Question:** Which capabilities split one behaviour, which are too small to stand
  alone, which requirements repeat across capabilities, and which state mechanics?
- **Script:** `<py> <s>/spec_inventory.py openspec/specs --tests tests`
- **Judge:**
  - small capability: name the capability it folds into, or why it stands alone;
  - name family: merge only when the members describe one behaviour;
  - near-duplicate: merge, or keep with the reason (a capability must stand alone);
  - implementation wording: keep when it is the contract for an outside author;
  - every proposed merge lists the markers that move.
