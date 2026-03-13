# bids

BIDS (Brain Imaging Data Structure) conventions and dataset validation for
neuroimaging datasets. Provides entity-ordering rules, datatype/suffix tables,
sidecar field references, and full dataset compliance checking via
`bids-validator`.

## Install the plugin

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/bids

# Permanent install
claude plugin install ./plugins/bids
```

## Install bids-validator (required for full dataset validation)

The `/bids` skill wraps the official [bids-validator](https://github.com/bids-standard/bids-validator)
CLI for full dataset compliance checking. Without it, the skill falls back to
a lightweight structural check with limited coverage.

### Primary (recommended) — 2.x via pip

```bash
pip install bids-validator-deno   # installs bids-validator-deno binary (Deno bundled — no separate install)

# Verify
bids-validator-deno --version
```

bids-validator 2.x is the actively developed branch. The Deno runtime is
embedded in the wheel — no separate Deno installation required.

### Legacy — 1.x via npm (not recommended for new setups)

```bash
npm install -g bids-validator     # 1.x (1.15.x); schema version is locked to the package

# Verify
bids-validator --version
```

1.x is still supported by `validate.sh` but will run with a deprecation
warning. The `--schema` override is not available in 1.x.

### Schema version control (2.x only)

Each 2.x release bundles a specific BIDS spec version (e.g. 2.4.1 bundles
schema v1.2.1). To control which schema version is used:

**Pin the validator release** (pins the bundled schema):
```bash
pip install "bids-validator-deno==2.4.1"
```

**Override the schema at runtime** via env var or flag:
```bash
# env var (applied automatically by validate.sh)
BIDS_SCHEMA=/path/to/schema.json bash validate.sh /my/dataset

# or pass --schema directly
bash validate.sh /my/dataset --schema /path/to/schema.json

# or point to a remote schema (URL supported)
BIDS_SCHEMA=https://bids-specification.readthedocs.io/en/v1.9.0/schema.json \
    bash validate.sh /my/dataset
```

**Where to get schema files:**
Download `schema.json` from a specific BIDS spec tag at:
`https://github.com/bids-standard/bids-specification/releases`

## Usage

```
/bids                          # Load BIDS context
/bids <dataset-path>           # Validate a dataset
/bids func                     # Focus on func datatype conventions
/bids sub-01_task-rest_bold    # Check a specific filename
```

The skill also auto-invokes when you mention BIDS-related filenames, entities
(`sub`, `ses`, `task`, `run`, …), JSON sidecars, or a `bids/` directory.

## What the validator checks

### Full bids-validator (2.x or 1.x)

- All filename entity ordering and label format violations
- Valid suffix + datatype combinations
- Required and recommended JSON sidecar fields per modality
- Companion file presence (`.bvec`/`.bval` for DWI)
- `IntendedFor` path resolution in field maps
- Cross-subject session consistency
- Dataset-level required files

### Fallback structural check (no bids-validator installed)

- `dataset_description.json` presence and required fields (`Name`, `BIDSVersion`)
- `README` presence
- `participants.tsv` / `CHANGES` (warnings if missing)
- `sub-*` directory naming
- Datatype directory names
- Entity ordering and alphanumeric label validation
- `task` entity presence for BOLD/func files
- `.bvec`/`.bval` companion files for DWI
- JSON sidecar existence for each NIfTI
- BOLD sidecars: `RepetitionTime` and `TaskName`
- Field map sidecars: `IntendedFor` presence and path resolution

## Structure

```
plugins/bids/
├── .claude-plugin/plugin.json
├── README.md
└── skills/bids/
    ├── SKILL.md
    ├── scripts/
    │   ├── validate.sh            # wraps bids-validator; falls back to check-structure.py
    │   ├── _parse_validator.py    # formats bids-validator --json output
    │   └── check-structure.py    # standalone fallback checker (stdlib only)
    └── references/
        ├── entities.md            # entity table + canonical ordering
        ├── datatypes.md           # datatype dirs, suffixes, dataset-level files
        └── sidecars.md            # required/recommended JSON fields per modality
```
