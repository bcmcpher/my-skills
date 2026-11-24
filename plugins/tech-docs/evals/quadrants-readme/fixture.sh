#!/usr/bin/env bash
# The repo's root README, frozen at the time of the hand labels in case.yaml.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$here/README.md" README.md
