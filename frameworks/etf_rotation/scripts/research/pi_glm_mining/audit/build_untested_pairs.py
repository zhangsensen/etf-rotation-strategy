#!/usr/bin/env python3
"""Inventory (not a test): enumerate legal cross-family atom pairs in the live
catalog, mark which have been preregistered in any round (either order, any
operator), attach single-atom health where known, write
workspace/controller/untested_pairs.csv for pi to pick hypotheses from.
"""
import json, glob, itertools
from pathlib import Path
import pandas as pd, yaml
import os
W = Path(os.environ.get("ETF_RUN_DIR", str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_pi_glm_mining_20260919"))) / "workspace"
cat = yaml.safe_load((W / "frameworks/etf_rotation/configs/family_catalog_v2.yaml").read_text())
sources = [f["source"] for f in cat["available_families"]] + ["cost_distribution", "bar_size_order_flow", "intraday_volume_profile_1m"]
atoms = []
for s in sources:
    p = W / f"frameworks/etf_rotation/configs/family_{s}_v1.yaml"
    if not p.exists(): continue
    for a in (yaml.safe_load(p.read_text()).get("atoms") or []):
        atoms.append((a["name"], s))
tested = {}
for pl in sorted(glob.glob(str(W / "outputs/round_*/PLAN.json"))):
    plan = json.loads(Path(pl).read_text())
    for c in plan.get("candidates", []):
        if c.get("operator") == "atomic" or "right" not in c: continue
        key = frozenset([c["left"]["name"], c["right"]["name"]])
        tested.setdefault(key, []).append(f"{plan['round_id']}:{c['id']}:{c['operator']}")
health = {}
for hp in glob.glob(str(W / "outputs/round_*/atom_health.csv")):
    # atom_health.csv schema drifted across rounds (round_018: disc_ic/audit_ic/max_abs_shelf_corr;
    # round_073+: discovery_ic/seen_audit_ic/shelf_max_corr); read by alias, never crash the tick.
    df = pd.read_csv(hp)
    def col(*names):
        for n in names:
            if n in df.columns: return df[n]
        return pd.Series([float("nan")] * len(df))
    for atom, d, a, c in zip(df["atom"], col("disc_ic", "discovery_ic"), col("audit_ic", "seen_audit_ic"),
                             col("max_abs_shelf_corr", "shelf_max_corr")):
        health[atom] = dict(disc_ic=d, audit_ic=a, shelf_corr=c)
rows = []
for (a, sa), (b, sb) in itertools.combinations(atoms, 2):
    if sa == sb: continue
    key = frozenset([a, b]); t = tested.get(key, [])
    ha, hb = health.get(a, {}), health.get(b, {})
    rows.append(dict(left=a, left_source=sa, right=b, right_source=sb, tested=bool(t), tested_as=";".join(t),
                     left_disc_ic=ha.get("disc_ic"), left_audit_ic=ha.get("audit_ic"), left_shelf_corr=ha.get("shelf_corr"),
                     right_disc_ic=hb.get("disc_ic"), right_audit_ic=hb.get("audit_ic"), right_shelf_corr=hb.get("shelf_corr"),
                     has_new_family_leg=(sa in sources[-3:]) or (sb in sources[-3:])))
df = pd.DataFrame(rows)
out = W / "controller"; out.mkdir(exist_ok=True)
df.to_csv(out / "untested_pairs.csv", index=False)
print(f"atoms {len(atoms)} sources {len(set(s for _,s in atoms))} | pairs {len(df)} | tested {int(df.tested.sum())} | untested {int((~df.tested).sum())} | untested with new-family leg {int(((~df.tested)&df.has_new_family_leg).sum())}")
