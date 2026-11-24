#!/usr/bin/env bash
# The planted-leak project from the tests: a guide, its .tech-terms and glossary.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$here/../lib/setup.sh"
proj="$plugins/tech-docs/tests/fixtures/project"
mkdir -p docs
cp "$proj/docs/guide.md" docs/ && cp "$proj/.tech-terms" "$proj/GLOSSARY.md" .
copy_lexicon
