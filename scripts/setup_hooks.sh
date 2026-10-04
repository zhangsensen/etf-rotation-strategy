#!/usr/bin/env bash
# Install the canonical staged and outgoing-commit code-only guards.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hook_dir="$(git rev-parse --path-format=absolute --git-path hooks)"

for hook in pre-commit pre-push; do
  [[ -f "$repo_root/.githooks/$hook" ]] || {
    echo "Missing canonical hook: .githooks/$hook" >&2
    exit 1
  }
done
mkdir -p "$hook_dir"
for hook in pre-commit pre-push; do
  install -m 755 "$repo_root/.githooks/$hook" "$hook_dir/$hook"
done
printf 'Installed code-only pre-commit and pre-push guards in %s\n' "$hook_dir"
