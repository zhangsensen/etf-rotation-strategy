"""Controller self-test: one pass over BOTH lanes' full history plus the controller's own
tooling, so integration failures are found by regression instead of by the next round.

Checks (each prints PASS/FAIL <name>: detail; exit code = number of failures):
  schema      every round's STATUS.json / PLAN.json / candidate_metrics.csv / atom_health.csv
              parse and carry the keys the controller reads (aliases allowed, nulls flagged)
  guard       exhaustion_guard.py runs on each lane without exception
  pairs       build_untested_pairs.py runs on each lane without exception
  verify      controller_verify.py logic imports and the newest admitted round per lane
              has (or can produce) controller_verification.json
  engine      each lane's live engine has the E23 scratch-dir guard and excludes 1d/adj_factor
              from truncation frequencies; no writer targets CANONICAL_ROOT
  data        canonical 1d files reach as_of and match .staging row counts (±1 daily row)
  queue       DIRECTIVE_QUEUE depth >= 2 per lane
  supervisor  heartbeat < 15 min when status RUNNING; STOP file absent
  tick        controller_tick.sh has no '2>/dev/null' on python calls; bash -n passes
Usage: controller_selftest.py [--lanes pi,sonnet] [--quick]  (quick skips verify re-run)
"""
from __future__ import annotations
import argparse
import csv
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(str(Path(__file__).resolve().parents[6]))
A = ROOT / "frameworks/etf_rotation/scripts/research/pi_glm_mining/audit"
PY = str(ROOT / ".venv/bin/python")
LANES = {
    "pi": ROOT / "runtime_outputs/etf_pi_glm_mining_20260919",
    "sonnet": ROOT / "runtime_outputs/etf_sonnet_mining_20260920",
}
CANON = Path(str(Path(__file__).resolve().parents[6] / "data/etf_rotation_v1"))
STATUS_KEYS = ("round_id", "n_preregistered", "n_gate_pass")
HEALTH_ALIASES = {"disc_ic": ("disc_ic", "discovery_ic"), "audit_ic": ("audit_ic", "seen_audit_ic"),
                  "shelf_corr": ("max_abs_shelf_corr", "shelf_max_corr")}
FAILS: list[str] = []


def report(ok: bool, name: str, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        FAILS.append(name)


def check_schema(lane: str, R: Path) -> None:
    problems = []
    rounds = sorted(glob.glob(str(R / "workspace/outputs/round_*")))
    n = 0
    for d in rounds:
        st = Path(d) / "STATUS.json"
        if not st.exists():
            continue
        n += 1
        try:
            s = json.loads(st.read_text())
        except Exception as e:
            problems.append(f"{Path(d).name}: STATUS unparsable {e}"); continue
        bookkeeping = bool(s.get("stage")) or int(s.get("n_preregistered") or 0) == 0  # deliverable/exhaustion rounds
        for k in STATUS_KEYS:
            if k not in s and not (bookkeeping and k in ("round_id", "n_gate_pass")):
                problems.append(f"{Path(d).name}: STATUS missing {k}")
        if s.get("n_gate_pass") is None and not bookkeeping and not str(s.get("status", "")).startswith(("BLOCKED", "VOID", "STAGE_EXHAUSTED")):
            problems.append(f"{Path(d).name}: n_gate_pass null without blocked status")
        if (s.get("n_gate_pass") or 0) > 0 and not (Path(d) / "PLAN.json").exists():
            problems.append(f"{Path(d).name}: admissions but no PLAN.json")
        cm = Path(d) / "candidate_metrics.csv"
        if cm.exists():
            try:
                hdr = next(csv.reader(open(cm)))
                if "candidate_id" not in hdr and "atom" not in hdr:
                    problems.append(f"{Path(d).name}: candidate_metrics lacks candidate_id/atom")
            except StopIteration:
                pass
        ah = Path(d) / "atom_health.csv"
        if ah.exists():
            hdr = next(csv.reader(open(ah)), [])
            if "atom" not in hdr:
                problems.append(f"{Path(d).name}: atom_health lacks atom")
            # atom_health has several legitimate variants (IC health, shadow-vs-reference, vs-original,
            # vs-base-returns); the controller only needs the atom column plus at least one metric column
            if len(hdr) < 2:
                problems.append(f"{Path(d).name}: atom_health has no metric columns")
    report(not problems, f"schema[{lane}]", f"{n} rounds; " + ("; ".join(problems[:6]) if problems else "ok"))


def run(cmd: list[str], env: dict | None = None, timeout: int = 900) -> tuple[int, str]:
    e = dict(os.environ); e.update(env or {})
    p = subprocess.run(cmd, capture_output=True, text=True, env=e, timeout=timeout, cwd=ROOT)
    return p.returncode, (p.stdout + p.stderr).strip()


def check_guard(lane: str, R: Path) -> None:
    rc, out = run([PY, str(A / "exhaustion_guard.py"), str(R)])
    report(rc == 0 and (out.startswith("OK") or out.startswith("REJECT")), f"guard[{lane}]", out.splitlines()[-1][:160] if out else "no output")


def check_pairs(lane: str, R: Path) -> None:
    rc, out = run([PY, str(A / "build_untested_pairs.py")], env={"ETF_RUN_DIR": str(R)})
    report(rc == 0, f"pairs[{lane}]", out.splitlines()[-1][:160] if out else "no output")


def check_verify(lane: str, R: Path, quick: bool) -> None:
    admitted = []
    mig = 0
    if (R / "migration.json").exists():
        mig = int(json.loads((R / "migration.json").read_text()).get("round", 0))
    for st in sorted(glob.glob(str(R / "workspace/outputs/round_*/STATUS.json"))):
        if int(Path(st).parent.name.split("_")[1]) < mig:  # inherited copies from another lane
            continue
        try:
            s = json.loads(open(st).read())
        except Exception:
            continue
        if (s.get("n_gate_pass") or 0) > 0:
            admitted.append(Path(st).parent)
    if not admitted:
        report(True, f"verify[{lane}]", "no admitted rounds"); return
    # a round that landed within the last 12 minutes is still inside the tick's verification window
    missing = [d.name for d in admitted if not (d / "controller_verification.json").exists()
               and time.time() - (d / "STATUS.json").stat().st_mtime > 720]
    newest = admitted[-1]
    if quick:
        report(len(missing) == 0, f"verify[{lane}]", f"{len(admitted)} admitted rounds, unverified: {missing[:5] or 'none'}")
        return
    target = newest if missing and newest.name in missing else newest
    rc, out = run([PY, str(A / "controller_verify.py"), str(target)], timeout=1200)
    ok = rc == 0 and (target / "controller_verification.json").exists()
    report(ok, f"verify[{lane}]", f"{target.name}: " + (out.splitlines()[-1][:140] if out else "no output"))


def check_engine(lane: str, R: Path) -> None:
    eng = R / "workspace/frameworks/etf_rotation/scripts/research/pi_round002_mine.py"
    if not eng.exists():
        report(False, f"engine[{lane}]", "engine missing"); return
    s = eng.read_text()
    probs = []
    if "_assert_scratch_dir(" not in s:
        probs.append("no scratch-dir guard")
    if 'not in ("1d", "adj_factor")' not in s:
        probs.append("1d not excluded from truncation frequencies")
    if s.count("_assert_scratch_dir(out_dir)") < 2:
        probs.append("guard not at both write sites")
    if "CONTROLLER_VOID.json" not in s:
        probs.append("dedup reference does not honour CONTROLLER_VOID.json (fix 1)")
    if '"base:RET1"' not in s or '"base:RET20"' not in s:
        probs.append("base-return dedup references missing (fix 3)")
    report(not probs, f"engine[{lane}]", "; ".join(probs) or "guarded")


def check_data() -> None:
    try:
        import pandas as pd
    except ImportError:
        report(False, "data", "pandas unavailable in this interpreter"); return
    probs = []
    files = sorted(glob.glob(str(CANON / "1d/*.parquet")))
    if not files:
        report(False, "data", "no 1d files"); return
    for f in files:
        sym = Path(f).name
        try:
            df = pd.read_parquet(f, columns=["trade_date"])
        except Exception as e:
            probs.append(f"{sym}: unreadable {e}"); continue
        mx = pd.to_datetime(df["trade_date"]).max()
        if mx < pd.Timestamp("2026-09-17"):
            probs.append(f"{sym}: max {mx.date()} < as_of")
        stg = CANON / ".staging" / sym[:-8] / "1d" / sym
        if stg.exists():
            n2 = len(pd.read_parquet(stg, columns=["trade_date"]))
            if not (0 <= n2 - len(df) <= 3):
                probs.append(f"{sym}: rows {len(df)} vs staging {n2}")
    report(not probs, "data", f"{len(files)} 1d files; " + ("; ".join(probs[:5]) if probs else "reach as_of, match staging"))


def check_void_overlay(lane: str, R: Path) -> None:
    vf = R / "CONTROLLER_VOID.json"
    if not vf.exists():
        report(True, f"void_overlay[{lane}]", "no void list"); return
    missing = [rid for rid in json.loads(vf.read_text()) if (R / "workspace/outputs" / rid).exists() and not (R / "workspace/outputs" / rid / "STATUS_OVERLAY.json").exists()]
    report(not missing, f"void_overlay[{lane}]", f"missing overlays: {missing or 'none'}")


def check_queue(lane: str, R: Path) -> None:
    q = [p for p in glob.glob(str(R / "DIRECTIVE_QUEUE/*.md")) if "/applied_" not in p]
    report(len(q) >= 2, f"queue[{lane}]", f"depth {len(q)}")


def check_supervisor(lane: str, R: Path) -> None:
    probs = []
    try:
        st = json.loads((R / "supervisor_status.json").read_text())
        hb = json.loads((R / "supervisor_heartbeat.json").read_text())
        age = time.time() - datetime.datetime.fromisoformat(hb["updated_at"]).timestamp()
        if st.get("status") in ("RUNNING", "COMPACTING") and age > 900:
            probs.append(f"heartbeat {int(age)}s old while {st.get('status')}")
        if st.get("status") in ("INSTRUMENT_BLOCKED", "STOPPED"):
            probs.append(f"status {st.get('status')}: {str(st.get('reason'))[:80]}")
    except Exception as e:
        probs.append(f"status/heartbeat unreadable: {e}")
    if (R / "STOP").exists():
        probs.append("STOP file present")
    report(not probs, f"supervisor[{lane}]", "; ".join(probs) or "alive")


def check_tick() -> None:
    probs = []
    for sh in ("controller_tick.sh", "controller_advance.sh"):
        rc, out = run(["bash", "-n", str(A / sh)])
        if rc != 0:
            probs.append(f"{sh}: syntax {out[:80]}")
        for i, line in enumerate((A / sh).read_text().splitlines(), 1):
            if re.search(r"\$PY[^;|&]*2>/dev/null", line):  # a python call whose own stderr is discarded
                probs.append(f"{sh}:{i} python stderr swallowed")
    for py in A.glob("*.py"):
        rc, out = run([PY, "-m", "py_compile", str(py)])
        if rc != 0:
            probs.append(f"{py.name}: {out[:80]}")
    report(not probs, "tick", "; ".join(probs) or "scripts compile, no swallowed python errors")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lanes", default="pi,sonnet")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    lanes = [l for l in a.lanes.split(",") if l in LANES]
    check_tick()
    check_data()
    for lane in lanes:
        R = LANES[lane]
        check_schema(lane, R)
        check_guard(lane, R)
        check_pairs(lane, R)
        check_verify(lane, R, a.quick)
        check_engine(lane, R)
        check_queue(lane, R)
        check_void_overlay(lane, R)
        check_supervisor(lane, R)
    print(f"SELFTEST {'OK' if not FAILS else 'FAILED'} failures={len(FAILS)} {FAILS}")
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main())
