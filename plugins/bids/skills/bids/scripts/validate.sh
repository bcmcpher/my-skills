#!/usr/bin/env bash
# validate.sh — run bids-validator on a dataset and report results
#
# Usage: validate.sh <dataset-path> [--schema <path-or-url>]
# Env:   BIDS_SCHEMA=/path/to/schema.json  (alternative to --schema)
#
# Validator detection order:
#   1. bids-validator-deno  (2.x, pip install bids-validator-deno)
#   2. bids-validator       (1.x legacy npm, or 2.x installed via other means)
#   3. Falls back to check-structure.py if neither found
#
# Exit codes:
#   0 — dataset is valid (errors=0)
#   1 — dataset has errors
#   2 — validator not found (fell back to check-structure.py)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATASET="${1:-}"
SCHEMA_OVERRIDE="${BIDS_SCHEMA:-}"

# Parse --schema from remaining args
shift || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --schema)
            SCHEMA_OVERRIDE="${2:-}"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [[ -z "$DATASET" ]]; then
    echo "Usage: $(basename "$0") <dataset-path> [--schema <path-or-url>]" >&2
    exit 1
fi

if [[ ! -d "$DATASET" ]]; then
    echo "Error: not a directory: $DATASET" >&2
    exit 1
fi

DATASET="$(cd "$DATASET" && pwd)"   # resolve absolute path

# ── Locate bids-validator ─────────────────────────────────────────────────────

strip_ansi() { sed 's/\x1b\[[0-9;]*m//g'; }

VALIDATOR=""
VALIDATOR_VERSION=""
VALIDATOR_MAJOR=0

if command -v bids-validator-deno &>/dev/null; then
    VALIDATOR="bids-validator-deno"
    VALIDATOR_VERSION=$(bids-validator-deno --version 2>&1 | strip_ansi | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    VALIDATOR_MAJOR=$(echo "$VALIDATOR_VERSION" | cut -d. -f1)
elif command -v bids-validator &>/dev/null; then
    VALIDATOR="bids-validator"
    VALIDATOR_VERSION=$(bids-validator --version 2>&1 | strip_ansi | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    VALIDATOR_MAJOR=$(echo "$VALIDATOR_VERSION" | cut -d. -f1)
fi

if [[ -z "$VALIDATOR" ]]; then
    echo "bids-validator not found on PATH."
    echo "Install bids-validator 2.x (recommended):"
    echo "  pip install bids-validator-deno"
    echo ""
    echo "Falling back to structural check (limited coverage)..."
    echo ""
    exec python3 "$SCRIPT_DIR/check-structure.py" "$DATASET"
fi

# ── Warn if legacy 1.x ───────────────────────────────────────────────────────

if [[ "$VALIDATOR_MAJOR" -lt 2 ]]; then
    echo "WARNING: bids-validator $VALIDATOR_VERSION is the legacy 1.x validator."
    echo "  Upgrade to 2.x for full support: pip install bids-validator-deno"
    if [[ -n "$SCHEMA_OVERRIDE" ]]; then
        echo "WARNING: --schema requires bids-validator 2.x; ignoring schema override."
        SCHEMA_OVERRIDE=""
    fi
    echo ""
fi

# ── Build validator command ───────────────────────────────────────────────────

if [[ "$VALIDATOR_MAJOR" -ge 2 ]]; then
    VALIDATOR_ARGS=("$DATASET" "--format" "json")
    if [[ -n "$SCHEMA_OVERRIDE" ]]; then
        VALIDATOR_ARGS+=("--schema" "$SCHEMA_OVERRIDE")
    fi
else
    # 1.x uses --json flag
    VALIDATOR_ARGS=("$DATASET" "--json")
fi

# ── Run validator (non-zero on errors; capture regardless) ────────────────────

RAW=$("$VALIDATOR" "${VALIDATOR_ARGS[@]}" 2>/dev/null) || true

# ── Parse and format output ───────────────────────────────────────────────────

echo "$RAW" | python3 "$SCRIPT_DIR/_parse_validator.py" "$DATASET" "$VALIDATOR_VERSION"
