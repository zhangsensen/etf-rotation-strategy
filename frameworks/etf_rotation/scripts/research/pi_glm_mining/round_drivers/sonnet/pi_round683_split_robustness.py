import sys, json
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import numpy as np
import pandas as pd
import pi_round002_mine as base
from etf_strategy.core.family_registry import load_builtin_families, resolve_family
from etf_strategy.core.etf_family_referee import block_means

panels, eligibility_all, symbols, forward = base._load_context()
load_builtin_families()
eligibility = eligibility_all[symbols]
DUMMY_1M = {"frequency": "1m"}


def fam(name):
    return resolve_family(name).builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)


# ---- base series (already-verified family outputs) ----
perm_ent = fam("permutation_entropy_1m")["PERM_ENTROPY_RET_20"][symbols]
lunch_post_run = fam("lunch_break_1m")["LUNCH_POST_RUN_20"][symbols]
underwater_frac_chg = fam("intraday_drawdown_1m")["UNDERWATER_FRAC_CHG_20"][symbols]
continuous_beta = resolve_family("jump_continuous_beta").builder(
    panels, eligibility, base.CANONICAL_ROOT, {"frequency": "1m", "benchmark_symbols": ["510300.SH", "510500.SH"]}
)["CONTINUOUS_BETA_60"][symbols]
gap_dd_consumption = fam("overnight_intraday_mismatch_v1")["GAP_DD_CONSUMPTION_RATIO_20"][symbols]
amihud = fam("microstructure_1m")["AMIHUD_1M_20"][symbols]

close = panels["close"][symbols]
open_p = panels["open"][symbols]
amount = panels["amount"][symbols]
volume = panels["volume"][symbols]
overnight_ret = (open_p / close.shift(1) - 1.0)
neg_amihud = -amihud

dates = close.index


# ---- split-diff helpers (generalized versions of overnight_conditioned_drawdown_volume.py's) ----
def rolling_median_split_diff(level: pd.Series, target: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        med = np.median(lv_w)
        upper = tg_w[lv_w >= med]
        lower = tg_w[lv_w < med]
        if len(upper) == 0 or len(lower) == 0:
            continue
        out.iloc[i] = float(np.mean(upper) - np.mean(lower))
    return out


def rolling_pct_outer_split_diff(level: pd.Series, target: pd.Series, window: int, lo_q=0.4, hi_q=0.6) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        lo, hi = np.quantile(lv_w, [lo_q, hi_q])
        upper = tg_w[lv_w >= hi]
        lower = tg_w[lv_w <= lo]
        if len(upper) == 0 or len(lower) == 0:
            continue
        out.iloc[i] = float(np.mean(upper) - np.mean(lower))
    return out


def rolling_sign_split_diff(level: pd.Series, target: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        pos = tg_w[lv_w > 0]
        neg = tg_w[lv_w < 0]
        if len(pos) < 5 or len(neg) < 5:
            continue
        out.iloc[i] = float(np.mean(pos) - np.mean(neg))
    return out


def rolling_median_group_mean(level: pd.Series, target: pd.Series, window: int, side: str) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        med = np.median(lv_w)
        grp = tg_w[lv_w >= med] if side == "upper" else tg_w[lv_w < med]
        if len(grp) == 0:
            continue
        out.iloc[i] = float(np.mean(grp))
    return out


def build_panel(fn, level_panel, target_panel, **kw):
    out = pd.DataFrame(np.nan, index=dates, columns=symbols)
    for sym in symbols:
        s = fn(level_panel[sym], target_panel[sym], **kw)
        out[sym] = s.reindex(dates)
    return out


def audit_block_t(sig: pd.DataFrame, fwd: pd.DataFrame, direction: float, k: int = 3, min_pairs: int = base.MIN_PAIRS):
    s = (sig * direction).where(eligibility)
    f = fwd.where(eligibility)
    valid = s.notna() & f.notna()
    s, f = s.where(valid), f.where(valid)
    n = valid.sum(axis=1)
    ok = n >= max(min_pairs, k + 1)
    top_mask = s.rank(axis=1, ascending=False, method="first") <= k
    top_ret = f.where(top_mask).mean(axis=1).where(ok)
    ew_ret = f.mean(axis=1).where(ok)

    def _stats(excess: pd.Series):
        excess = excess.dropna()
        if len(excess) == 0:
            return float("nan"), float("nan")
        blocks = block_means(excess.to_frame("x"), base.PRIMARY)["x"].dropna()
        t_val = (
            float(blocks.mean() / (blocks.std(ddof=1) / np.sqrt(len(blocks))))
            if len(blocks) > 3
            else float("nan")
        )
        return float(excess.mean() * 1e4), t_val

    excess = top_ret - ew_ret
    disc_bp, disc_t = _stats(excess.loc[: base.DISCOVERY_END])
    aud_bp, aud_t = _stats(excess.loc[base.AUDIT_START : base.AUDIT_END])
    return disc_bp, disc_t, aud_bp, aud_t


def rank_spread(left_panel: pd.DataFrame, right_panel: pd.DataFrame) -> pd.DataFrame:
    return left_panel.rank(axis=1, pct=True) - right_panel.rank(axis=1, pct=True)


def eval_row(label, left_panel, right_panel, direction=1.0):
    sig = rank_spread(left_panel, right_panel)
    row = {"config": label}
    for h in (5, 10, 20):
        disc_bp, disc_t, aud_bp, aud_t = audit_block_t(sig, forward[h], direction)
        row[f"h{h}_disc_bp"] = round(disc_bp, 2)
        row[f"h{h}_disc_t"] = round(disc_t, 3)
        row[f"h{h}_audit_bp"] = round(aud_bp, 2)
        row[f"h{h}_audit_t"] = round(aud_t, 3)
    print(row)
    return row


rows = []

# ============================================================
# Pairing 1: PERMENT_TURNOVER_SPLIT_20 x CONTINUOUS_BETA_60 (round_673, t=4.15)
# ============================================================
print("=== Pairing 1: PERMENT_TURNOVER x CONTINUOUS_BETA_60 ===")
baseline1 = build_panel(rolling_median_split_diff, amount, perm_ent, window=20)
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x CONTINUOUS_BETA_60", **eval_row("baseline(median,w20,amount)", baseline1, continuous_beta)})
pct1 = build_panel(rolling_pct_outer_split_diff, amount, perm_ent, window=20)
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x CONTINUOUS_BETA_60", **eval_row("threshold=pct40/60outer,w20,amount", pct1, continuous_beta)})
w40_1 = build_panel(rolling_median_split_diff, amount, perm_ent, window=40)
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x CONTINUOUS_BETA_60", **eval_row("median,w40,amount", w40_1, continuous_beta)})
w60_1 = build_panel(rolling_median_split_diff, amount, perm_ent, window=60)
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x CONTINUOUS_BETA_60", **eval_row("median,w60,amount", w60_1, continuous_beta)})
vol1 = build_panel(rolling_median_split_diff, volume, perm_ent, window=20)
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x CONTINUOUS_BETA_60", **eval_row("median,w20,cond=volume", vol1, continuous_beta)})
amihud1 = build_panel(rolling_median_split_diff, neg_amihud, perm_ent, window=20)
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x CONTINUOUS_BETA_60", **eval_row("median,w20,cond=-Amihud", amihud1, continuous_beta)})

# ============================================================
# Pairing 2: PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20 (round_675, t=2.45)
# ============================================================
print("=== Pairing 2: PERMENT_TURNOVER x UNDERWATER_FRAC_CHG_20 ===")
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20", **eval_row("baseline(median,w20,amount)", baseline1, underwater_frac_chg)})
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20", **eval_row("threshold=pct40/60outer,w20,amount", pct1, underwater_frac_chg)})
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20", **eval_row("median,w40,amount", w40_1, underwater_frac_chg)})
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20", **eval_row("median,w60,amount", w60_1, underwater_frac_chg)})
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20", **eval_row("median,w20,cond=volume", vol1, underwater_frac_chg)})
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20", **eval_row("median,w20,cond=-Amihud", amihud1, underwater_frac_chg)})

# single-leg diagnostic: which side carries the information
upper_grp = build_panel(rolling_median_group_mean, amount, perm_ent, window=20, side="upper")
lower_grp = build_panel(rolling_median_group_mean, amount, perm_ent, window=20, side="lower")
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20", **eval_row("single-leg: high-turnover-day PERM_ENT only", upper_grp, underwater_frac_chg)})
rows.append({"pair": "PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20", **eval_row("single-leg: low-turnover-day PERM_ENT only", lower_grp, underwater_frac_chg)})

# ============================================================
# Pairing 3: LUNCHPR_ONGAP_SPLIT_20 x GAP_DD_CONSUMPTION_RATIO_20 (round_673, t=3.68)
# NOTE: original window is 40 (sign-split), NOT 20 -- directive text's "窗{20(原版),40,60}"
# mislabels the original window; using the TRUE original (40) as baseline here.
# Condition variable is overnight-gap SIGN, not turnover/amount, so the amount->volume /
# amount->Amihud substitution axis from the directive does not apply to this atom;
# skipped and noted, using a magnitude-based outer-split of the same overnight_ret as
# the closest analogous "threshold shape" variant instead.
# ============================================================
print("=== Pairing 3: LUNCHPR_ONGAP x GAP_DD_CONSUMPTION_RATIO_20 ===")
baseline3 = build_panel(rolling_sign_split_diff, overnight_ret, lunch_post_run, window=40)
rows.append({"pair": "LUNCHPR_ONGAP_SPLIT_20 x GAP_DD_CONSUMPTION_RATIO_20", **eval_row("baseline(sign,w40,true original)", baseline3, gap_dd_consumption)})
pct3 = build_panel(rolling_pct_outer_split_diff, overnight_ret, lunch_post_run, window=40, lo_q=0.3, hi_q=0.7)
rows.append({"pair": "LUNCHPR_ONGAP_SPLIT_20 x GAP_DD_CONSUMPTION_RATIO_20", **eval_row("threshold=pct30/70outer(magnitude,analog of sign),w40", pct3, gap_dd_consumption)})
w20_3 = build_panel(rolling_sign_split_diff, overnight_ret, lunch_post_run, window=20)
rows.append({"pair": "LUNCHPR_ONGAP_SPLIT_20 x GAP_DD_CONSUMPTION_RATIO_20", **eval_row("sign,w20", w20_3, gap_dd_consumption)})
w60_3 = build_panel(rolling_sign_split_diff, overnight_ret, lunch_post_run, window=60)
rows.append({"pair": "LUNCHPR_ONGAP_SPLIT_20 x GAP_DD_CONSUMPTION_RATIO_20", **eval_row("sign,w60", w60_3, gap_dd_consumption)})

df = pd.DataFrame(rows)
OUT = base.WORKSPACE_OUTPUTS / "round_683"
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "split_robustness.csv", index=False)
print("wrote", OUT / "split_robustness.csv")
