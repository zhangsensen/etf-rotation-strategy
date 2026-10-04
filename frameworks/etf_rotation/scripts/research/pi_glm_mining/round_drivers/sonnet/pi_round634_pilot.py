#!/usr/bin/env python3
"""Small-sample pilot (3 symbols, per 2026-09-21 00:40 engineering rule)
for round_634's new family pre_breakout_drawdown_1m before committing to
a full 14-symbol run."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.family_registry import load_builtin_families, resolve_family  # noqa: E402

load_builtin_families()
panels, eligibility_all, symbols, forward = eng._load_context()
pilot_symbols = symbols[:3]

mining = yaml.safe_load(eng._config_path("pre_breakout_drawdown_1m").read_text())
pilot_panels = {k: v[pilot_symbols] for k, v in panels.items()}
pilot_elig = eligibility_all[pilot_symbols]

t0 = time.time()
space = resolve_family("pre_breakout_drawdown_1m").builder(pilot_panels, pilot_elig, eng.CANONICAL_ROOT, mining)
elapsed = time.time() - t0
print(f"pilot (3 symbols) elapsed: {elapsed:.2f}s")
for atom_cfg in mining["atoms"]:
    name = atom_cfg["name"]
    frame = space[name]
    n_finite = int(frame.notna().to_numpy().sum())
    total = frame.size
    print(f"  {name}: finite={n_finite}/{total} ({n_finite/total:.1%})")
print(f"extrapolated 14-symbol estimate: ~{elapsed * 14 / 3:.1f}s")
