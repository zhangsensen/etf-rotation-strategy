#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "not inside a git repository" >&2
  exit 2
fi

is_data_artifact() {
  local path="${1,,}"

  # Data extensions are forbidden everywhere, including source and fixture directories.
  if [[ "${path,,}" =~ \.(parquet|feather|duckdb|sqlite3?|db|h5|hdf5|npy|npz|pkl|pickle|joblib|pt|pth|ckpt|safetensors|zip|tar|gz|7z|csv|tsv|jsonl|xlsx?|arrow|orc|avro|png|jpe?g|webp|pdf)$ ]]; then
    return 0
  fi

  case "$path" in
    */outputs/*|outputs/*|*/artifacts/*|artifacts/*|*/reports/*|reports/*|*/raw_transcripts/*)
      return 0 ;;
    data/downloaders/*|core/data/*|src/modules/core/data/*|src/modules/ml_trading/data/*)
      # Permit actual source/docs/config only, never arbitrary files below a code directory.
      [[ "$path" =~ \.(py|sh|ps1|md|rst|toml|yaml|yml|json|txt)$ ]] && return 1
      return 0 ;;
  esac

  case "$path" in
    fuzong_md/*|*/raw_transcripts/*) return 0 ;;
    data/*|runtime_outputs/*) return 0 ;;
    alpha_mining/mining_session/db/*) return 0 ;;
    alpha_mining/AI/outputs/*|alpha_mining/outputs/*) return 0 ;;
    alpha_mining/AI/concept_etf/*_artifacts/*) return 0 ;;
    alpha_mining/AI/concept_etf/v4_subconcept_assist_gate/*) return 0 ;;
    deployments/qmt_r1_live/golden/*) return 0 ;;
    deployments/qmt_r1_live/strategies/*/golden/*) return 0 ;;
    deployments/strategy_freeze/*/golden/*) return 0 ;;
    deployments/strategy_freeze/*/trace/*) return 0 ;;
    deployments/strategy_freeze/*/frozen_panel/*) return 0 ;;
    src/modules/ml_trading/factory/outputs/*) return 0 ;;
  esac

  [[ "$path" =~ \.(csv|tsv|parquet|feather|duckdb|sqlite3|db|h5|hdf5|npy|npz|pkl|pickle|joblib|pt|pth|ckpt|safetensors|jsonl)$ ]]
}

collect_hits() {
  local path
  while IFS= read -r -d '' path; do
    if is_data_artifact "$path"; then
      printf '%s\n' "$path"
    fi
  done
}

mode="${1:-staged}"
case "$mode" in
  staged)
    [[ $# -le 1 ]] || { echo "Invalid guard arguments" >&2; exit 2; }
    hits="$(git diff --cached --name-only -z --no-renames --diff-filter=ACMRTUXB | collect_hits)"
    ;;
  --range)
    [[ $# -eq 3 ]] || { echo "Usage: $0 --range BASE TIP" >&2; exit 2; }
    base="$(git rev-parse --verify "${2}^{commit}")"
    tip="$(git rev-parse --verify "${3}^{commit}")"
    # Check every introduced commit, including data added then deleted before TIP.
    commits="$(git rev-list "$tip" "^$base")"
    hits="$(while IFS= read -r commit; do
      [[ -z "$commit" ]] && continue
      git diff-tree --root -m --no-commit-id --name-only -r -z --no-renames \
        --diff-filter=ACMRTUXB "$commit"
    done <<<"$commits" | collect_hits)"
    ;;
  *) echo "Unknown guard mode: $mode" >&2; exit 2 ;;
esac

if [[ -n "$hits" ]]; then
  echo "DATA-IN-GIT GUARD FAILED ($mode)" >&2
  printf '%s\n' "$hits" >&2
  exit 1
fi

tracked_hits="$(git ls-files -z | collect_hits)"
if [[ -n "$tracked_hits" ]]; then
  n=$(printf '%s\n' "$tracked_hits" | wc -l)
  echo "WARN: $n pre-existing tracked data artifacts; not permission for new data" >&2
fi

echo "OK: no new data artifacts ($mode)"
