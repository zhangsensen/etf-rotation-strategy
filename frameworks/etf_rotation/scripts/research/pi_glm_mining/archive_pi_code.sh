#!/usr/bin/env bash
# Copy a mining lane's live engine and round drivers into the tracked archive.
# Lane selection: ETF_ARCHIVE_LANE=pi (default) | sonnet. Engine versions are
# named by sha256 prefix (shared across lanes); drivers go to round_drivers/<lane>/
# for non-pi lanes so the two lanes never overwrite each other.
set -euo pipefail
ROOT=/home/sensen/dev/projects/gpu_ml-coral
LANE=${ETF_ARCHIVE_LANE:-pi}
case "$LANE" in
  pi) SRC=$ROOT/runtime_outputs/etf_pi_glm_mining_20260919/workspace/frameworks/etf_rotation/scripts/research; DRV=$ROOT/frameworks/etf_rotation/scripts/research/pi_glm_mining/round_drivers;;
  sonnet) SRC=$ROOT/runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research; DRV=$ROOT/frameworks/etf_rotation/scripts/research/pi_glm_mining/round_drivers/sonnet;;
  *) echo "unknown lane $LANE"; exit 1;;
esac
DST=$ROOT/frameworks/etf_rotation/scripts/research/pi_glm_mining
mkdir -p "$DRV" "$DST/engine_versions"
eng=$SRC/pi_round002_mine.py
h=$(sha256sum "$eng" | cut -c1-8)
[ -f "$DST/engine_versions/pi_round002_mine.$h.py" ] || { cp "$eng" "$DST/engine_versions/pi_round002_mine.$h.py"; echo "new engine version $h ($LANE)"; }
for f in "$SRC"/pi_round*_mine.py "$SRC"/pi_round*_census.py "$SRC"/topk_referee_admitted.py; do [ -f "$f" ] && cp "$f" "$DRV/$(basename "$f")"; done
cd "$ROOT" && git status --short "$DST" | sed 's/^/  /'
