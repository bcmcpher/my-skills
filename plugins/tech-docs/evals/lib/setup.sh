# Shared scaffold helpers, sourced by each case's fixture.sh. The working directory is the
# run's empty workspace; HOME is the run's temporary home.
set -euo pipefail
plugins="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # the repo's plugins/
real_home="$(getent passwd "$(id -u)" | cut -d: -f6)"

# The boutiques plugin without its README: the case asks for one.
copy_boutiques() {
  mkdir -p boutiques
  cp -r "$plugins/boutiques/.claude-plugin" "$plugins/boutiques/skills" boutiques/
}

# The STE lexicon into the run's home, so the checker in the run can load it by name.
# The lexicon stays out of the workspace and out of the repository.
copy_lexicon() {
  local src="${real_home}/.local/share/tech-docs/lexicons/ste100-issue9.json"
  [[ -f $src ]] || return 0
  mkdir -p "$HOME/.local/share/tech-docs/lexicons"
  cp "$src" "$HOME/.local/share/tech-docs/lexicons/"
}

readme_fixture() {
  local case_dir="$1"
  copy_boutiques
  copy_lexicon
  cp "$case_dir/../lib/boutiques.tech-terms" .tech-terms
}
