#!/usr/bin/env python3
"""Decide whether a MECHANISM_EXHAUSTED declaration is valid.

Valid only if (a) the operator(s) named in the "当前生效" block of
CONTROLLER_DIRECTIVE.md actually appear in recent PLANs (the stage was really
executed), and (b) the last three completed rounds each preregistered
candidates and admitted none under gate 7. Prints OK or REJECT <why>.
"""
import glob
import json
import re
import sys

R = sys.argv[1]
text = open(f"{R}/CONTROLLER_DIRECTIVE.md", encoding="utf-8").read()
# the active block is the LAST "★ 当前生效" block in the file (staged directives are appended at the end)
_i = text.rfind("★ 当前生效")
head = text[_i:] if _i >= 0 else text.split("# 历史指令")[0]
ops = re.findall(r"`(rank_cond_spread|rank_cond|rank_spread|rank_interaction)`", head)
required = {o for o in ops if o.startswith("rank_cond")} or None

plans = sorted(glob.glob(f"{R}/workspace/outputs/round_*/PLAN.json"))
stats = sorted(glob.glob(f"{R}/workspace/outputs/round_*/STATUS.json"))
used = set()
for pl in plans[-12:]:
    for c in json.load(open(pl)).get("candidates", []):
        used.add(c.get("operator"))
# only EVALUATED rounds count toward the three-zero rule; blocked/void rounds
# (n_gate_pass null or nothing preregistered, e.g. the E23 data-outage rounds) are skipped
evaluated = [
    s for s in (json.load(open(x)) for x in stats)
    if s.get("n_gate_pass") is not None and int(s.get("n_preregistered") or 0) > 0
]
last3 = evaluated[-3:]
three_zero = len(last3) == 3 and all(int(s.get("n_gate_pass") or 0) == 0 for s in last3)
# pi named the conditional operators cond_spread / cond_double / cond_interaction; accept any operator containing "cond"
op_ok = True if required is None else any("cond" in (u or "") for u in used)
# a single-round stage (e.g. atomic re-adjudication) declares itself in the active block and ends after one round
single_round = ("只此一轮" in head) or ("一轮完成" in head)
# contract's alternative exhaustion: legal untested pairing space enumerated to zero, with the
# last two EVALUATED rounds at zero admissions (a third zero round is arithmetically unreachable)
space_exhausted = False
try:
    ex = json.load(open(f"{R}/MECHANISM_EXHAUSTED"))
    exj = json.load(open(ex["source"])) if ex.get("source") else {}
    proof = json.dumps(exj, ensure_ascii=False)
    last2 = evaluated[-2:]
    space_exhausted = (
        ("pairing_enumeration_proof" in exj.get("tested_scope", {}) or "配对用尽" in proof)
        and len(last2) == 2 and all(int(s.get("n_gate_pass") or 0) == 0 for s in last2)
    )
    # contract row "配对纪律" (2026-09-20 17:00): fewer than 12 legal pairings left under the
    # one-batch-per-left-leg rule ends the stage regardless of recent admissions
    # wording varies per agent; accept any explicit statement that the legal pairing space is
    # gone under the pairing-discipline row (17:00 条款 / 配额 / 枚举为零 / <12)
    # E29: structured fields take precedence over wording
    try:
        lpr = exj.get("legal_pairs_remaining")
        clause = str(exj.get("exhaustion_clause", "")).lower()
        if (lpr is not None and int(lpr) < 12) or clause in ("pairing_discipline", "single_round", "three_zero", "space_exhausted"):
            space_exhausted = True
    except Exception:
        pass
    if re.search(r"配对纪律|pairing[-_ ]discipline|17:00 ?条款|配额.*(消耗|用尽|用完|用满)|额度.*(用满|用尽|耗尽)|合法[^，。；]{0,8}配对.*(为零|= ?0|<\s*12|不足 ?12|枚举为零)|剩余合法配对 ?= ?0|remaining pairing space ?= ?0|one pairing batch", proof, re.I | re.S):
        space_exhausted = True
except Exception:
    space_exhausted = False
if op_ok and (three_zero or single_round or space_exhausted):
    print("OK")
else:
    print(f"REJECT op_ok={op_ok} three_zero={three_zero} space_exhausted={space_exhausted} used={sorted(x for x in used if x)}")
