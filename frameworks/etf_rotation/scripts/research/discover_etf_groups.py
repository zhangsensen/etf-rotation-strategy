#!/usr/bin/env python3
"""Run a bounded, seen-history eight-group discovery batch (never certification)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT/'frameworks/etf_rotation'
sys.path.insert(0, str(ETF/'src'))
from etf_strategy.project_paths import local_path
from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as engine
from etf_strategy.core import etf_mining_referee as primitives
from etf_strategy.core import etf_group_sources as source_engine
from etf_strategy.core import etf_group_interactions as interaction_engine
from etf_strategy.core import etf_group_evidence as evidence_engine
from etf_strategy.core import etf_group_confirmation as confirmation_engine
from etf_strategy.core import etf_group_run_rules as run_rules
from etf_strategy.core.etf_rank_utils import stable_rank
from etf_strategy.core import etf_group_preflight as preflight
import preflight_us_index_source as us_source


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def unchanged_hashes(paths, expected):
    """True iff hashing every path in `paths` right now reproduces exactly
    `expected` (same keys, same values) -- the end-of-run integrity
    invariant this entry's two post-computation checks both need. A pure,
    directly testable extraction of what was previously two inline dict-
    literal comparisons (round 11 bug, master 2026-09-24: the `inputs`
    check only re-hashed `files`, never `macro_files`, so once
    macro_inputs=true added 5 extra keys to `inputs` at capture time, the
    re-hash could never equal it -- a deterministic failure on every run,
    not real concurrent data corruption, diagnosed by 5 runs producing
    byte-identical IC numbers yet still failing this check every time).
    Fixed by always hashing the SAME path set used to build the value
    being compared against."""
    return {str(p): sha(p) for p in paths} == expected


def write_json(path, value):
    def clean(x):
        if isinstance(x, dict):
            return {str(k): clean(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [clean(v) for v in x]
        if isinstance(x, (np.floating, float)):
            return float(x) if np.isfinite(x) else None
        if isinstance(x, np.integer):
            return int(x)
        if isinstance(x, np.bool_):
            return bool(x)
        return x
    path.write_text(json.dumps(clean(value), ensure_ascii=False, indent=2)+'\n')


def candidate_known_mask(base_known, atom):
    """Apply availability per candidate; one sparse atom must not mask a batch."""
    return base_known & atom.notna().all(axis=1)


def _window_mechanism_pairs(cfg):
    """(window, mechanism, definition) triples. claude_rounds carries its
    window per-mechanism (no single global window); every other kind still
    takes the window from the shared top-level cfg['windows'] list."""
    if cfg.get('source_type') == 'claude_rounds':
        return [(d['window'], m, d) for m, d in cfg['mechanisms'].items()]
    return [(w, m, d) for w in cfg['windows'] for m, d in cfg['mechanisms'].items()]


def definition_keys(plan):
    cfg=plan['config']
    kind=cfg.get('source_type','daily')
    filename=(Path(cfg['candidate_module']).name if kind=='autoresearch' else
              'etf_group_discovery.py' if kind=='daily' else
              'etf_group_daily_mechanisms.py' if kind=='daily_mechanisms' else
              'etf_group_daily_rounds.py' if kind=='daily_rounds' else
              'etf_group_daily_outcome.py' if kind=='daily_outcome' else
              'etf_group_claude_rounds.py' if kind=='claude_rounds' else
              'etf_group_aux_bond.py' if kind=='auxiliary_bond' else
              'etf_group_us_index.py' if kind=='us_index' else
              'etf_group_us_sector.py' if kind=='us_sector' else
              'etf_group_us_vix.py' if kind=='us_vix' else
              'etf_group_us_style.py' if kind=='us_style' else
              'etf_group_ext_gold.py' if kind=='ext_gold' else
              'etf_group_ext_copper.py' if kind=='ext_copper' else
              'etf_group_ext_crude.py' if kind=='ext_crude' else
              'etf_group_ext_cnh.py' if kind=='ext_cnh' else
              'etf_group_ext_hktech.py' if kind=='ext_hktech' else
              'etf_group_ext_realrate.py' if kind=='ext_realrate' else
              'etf_group_ext_coal.py' if kind=='ext_coal' else
              'etf_group_domestic_benchmark.py' if kind=='domestic_benchmark' else
              'etf_group_interactions.py' if kind=='interaction' else 'etf_group_sources.py')
    code_hash=next(v for k,v in plan['source_hashes'].items() if Path(k).name==filename)
    return {json.dumps([kind,m,w,d['direction'],code_hash,'mean_raw_same_units']+
                       ([{'parent_run':d['parent_run'],'parent_candidate':d['parent_candidate']}]
                        if kind=='self_state' else [d['left'],d['right']] if kind=='interaction' else []),sort_keys=True)
            for w,m,d in _window_mechanism_pairs(cfg)}


def semantic_definition_keys(plan):
    """Definition identity without implementation hash, only for an explicit rejudge."""
    cfg=plan['config']
    kind=cfg.get('source_type','daily')
    return {json.dumps([kind,m,w,d['direction'],'mean_raw_same_units']+
                       ([{'parent_run':d['parent_run'],'parent_candidate':d['parent_candidate']}]
                        if kind=='self_state' else [d['left'],d['right']] if kind=='interaction' else []),sort_keys=True)
            for w,m,d in _window_mechanism_pairs(cfg)}


def reserve_plan(out, plan):
    """Count unique frozen definitions across this entry's runs, including failed runs."""
    with (out.parent/'.group_discovery_budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        keys=definition_keys(plan)
        prior_keys = set()
        for p in sorted(out.parent.glob('*/PLAN.json')):
            previous=json.loads(p.read_text())
            if 'config' in previous and 'mechanisms' in previous['config']:
                previous_parent = previous['config'].get('rejudge_of')
                if previous_parent:
                    frozen_parent = out.parent/previous_parent/'PLAN.json'
                    if not frozen_parent.exists():
                        raise ValueError('historical rejudge parent PLAN missing')
                    prior_keys |= definition_keys(json.loads(frozen_parent.read_text()))
                else:
                    prior_keys |= definition_keys(previous)
        external = plan['config'].get('external_registered_definitions', 0)
        if type(external) is not int or external < 0:
            raise ValueError('invalid external registration count')
        if plan['config'].get('source_type') == 'daily_rounds' or plan['config'].get('campaign_extension') is True:
            if plan['config'].get('prior_registered') != len(prior_keys) + external:
                raise ValueError('approved prior count differs from persistent ledger')
            rejudge_of = plan['config'].get('rejudge_of')
            if rejudge_of:
                parent_path = out.parent/rejudge_of/'PLAN.json'
                if not parent_path.exists():
                    raise ValueError('rejudge parent PLAN missing')
                parent_plan = json.loads(parent_path.read_text())
                if semantic_definition_keys(plan) != semantic_definition_keys(parent_plan):
                    raise ValueError('rejudge definitions differ from frozen parent')
                if plan['config']['budget_cap'] != len(prior_keys) + external:
                    raise ValueError('rejudge cannot increase definition budget')
                # A judge or leakage repair changes source hashes but not the frozen
                # hypotheses. Preserve the historical definition ledger verbatim.
                keys = set(prior_keys)
            elif keys & prior_keys:
                raise ValueError('new round repeats a registered definition')
        keys |= prior_keys
        if len(keys)+external>plan['config']['budget_cap']:
            raise ValueError(f'cumulative group discovery budget exceeded: {len(keys)+external}')
        plan['entry_registered_definitions']=len(keys)
        plan['external_registered_definitions']=external
        plan['cumulative_registered_definitions']=len(keys)+external
        write_json(out/'PLAN.json',plan)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', default=str(ETF/'configs/group_discovery_daily_v1.yaml'))
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--approval', help='Exact master-reviewed config/source-bound batch record')
    ap.add_argument('--pilot', action='store_true', help='Evaluate only momentum_20; same batch definition')
    args = ap.parse_args()
    if not args.run_id.replace('_', '').replace('-', '').isalnum():
        raise ValueError('invalid run id')
    config_path = Path(args.config).resolve()
    cfg = yaml.safe_load(config_path.read_text())
    run_rules.validate_ic_discovery_config(cfg)
    kind=cfg.get('source_type','daily')
    if kind not in ('daily','daily_mechanisms','daily_rounds','daily_outcome','claude_rounds','auxiliary_bond','us_index','us_sector','us_vix','us_style','ext_gold','ext_copper','ext_crude','ext_cnh','ext_hktech','ext_realrate','ext_coal','autoresearch','domestic_benchmark','minute','share','nav','self_state','interaction') or (args.pilot and kind!='daily'):
        raise ValueError('unsupported source/pilot combination')
    if cfg['purpose'] != 'seen_history_discovery_only' and not (
            kind == 'domestic_benchmark' and cfg['purpose'] == 'seen_history_ic_discovery_only'):
        raise ValueError('this entry cannot certify factors')
    if (cfg['entry_lag'], cfg['horizon'], cfg['top_k']) != (2, 5, 2):
        raise ValueError('this version fixes D+2/H5/K2; version changes require a new implementation')
    if cfg['as_of'] > '2026-09-17':
        raise ValueError('do not silently consume new forward dates')
    approval_path = Path(args.approval).resolve() if args.approval else None
    approval = json.loads(approval_path.read_text()) if approval_path else None
    if kind in ('daily_mechanisms','daily_rounds','daily_outcome','claude_rounds') or cfg['budget_cap'] > 96:
        run_rules.validate_batch_approval(cfg, sha(config_path), args.run_id, approval)
        if args.pilot:
            raise ValueError('approved new batch cannot silently become a pilot')
    elif approval is not None:
        raise ValueError('approval extension belongs to a newly reviewed batch')
    daily_engine = (importlib.import_module('etf_strategy.core.etf_group_daily_mechanisms')
                    if kind == 'daily_mechanisms' else engine)
    if kind == 'daily_rounds':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_daily_rounds')
    if kind == 'daily_outcome':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_daily_outcome')
    if kind == 'claude_rounds':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_claude_rounds')
    if kind == 'auxiliary_bond':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_aux_bond')
    if kind == 'us_index':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_us_index')
    if kind == 'us_sector':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_us_sector')
    if kind == 'us_vix':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_us_vix')
    if kind == 'us_style':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_us_style')
    if kind == 'ext_gold':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_ext_gold')
    if kind == 'ext_copper':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_ext_copper')
    if kind == 'autoresearch':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_autoresearch')
    if kind == 'ext_crude':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_ext_crude')
    if kind == 'ext_cnh':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_ext_cnh')
    if kind == 'ext_hktech':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_ext_hktech')
    if kind == 'ext_realrate':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_ext_realrate')
    if kind == 'ext_coal':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_ext_coal')
    if kind == 'domestic_benchmark':
        daily_engine = importlib.import_module('etf_strategy.core.etf_group_domestic_benchmark')
    root = local_path(cfg['data_root'])
    allowed = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1")).resolve()
    if root != allowed:
        raise ValueError('data root outside fixed ETF store')
    universe = ROOT/cfg['universe']
    group_path = ROOT/cfg['groups']
    symbols = [r['ts_code'] for r in json.loads(universe.read_text())['etfs'] if r['role']=='candidate']
    groups = yaml.safe_load(group_path.read_text())['groups']
    engine.validate_groups(groups, symbols)
    files = [root/folder/f'{s}.parquet' for folder in ('1d', 'adj_factor') for s in symbols]
    calendar_file = root/'1d'/f"{cfg['calendar_symbol']}.parquet"
    files.append(calendar_file)
    if kind == 'auxiliary_bond':
        files.extend(root/folder/f'{s}.parquet'
                     for folder in ('1d', 'adj_factor')
                     for s in ('511010.SH', '511880.SH'))
    if kind == 'domestic_benchmark':
        if cfg.get('auxiliary_symbols') != ['510300.SH', '510500.SH']:
            raise ValueError('domestic benchmark auxiliary population changed')
        files.extend(root/folder/f'{s}.parquet'
                     for folder in ('1d', 'adj_factor')
                     for s in cfg['auxiliary_symbols'])
    if kind in ('minute','share','nav'):
        folder={'minute':'1m','share':'fund_share','nav':'nav'}[kind]
        files.extend(root/folder/f'{s}.parquet' for s in symbols)
    minute_inputs = kind == 'claude_rounds' and cfg.get('minute_inputs') is True
    if minute_inputs:
        # Optional 5m-bar input for claude_rounds Theme D (minute-level
        # co-movement) candidates, plus 513100.SH's raw 1m file (used only
        # for the open-halt diagnostic, etf_ic_monthly_factory.open_halt_
        # dates). Scoped to this flag so every other claude_rounds config
        # (minute_inputs unset/false) is completely unaffected.
        files.extend(root/'5m'/f'{s}.parquet' for s in symbols)
        files.append(root/'1m'/'513100.SH.parquet')
    if any(not f.resolve().is_relative_to(root) for f in files):
        raise ValueError('input symlink escapes canonical root')
    us_files: list[Path] = []
    if kind == 'us_index':
        expected_us = ROOT/'runtime_outputs/etf_rotation_research/us_index_source_preflight_20260925/NASDAQ100.csv'
        if cfg.get('us_index_file') != str(expected_us.relative_to(ROOT)):
            raise ValueError('US index input must be the reviewed local FRED snapshot')
        if not expected_us.is_file() or expected_us.is_symlink():
            raise FileNotFoundError('reviewed local US index snapshot is absent or a symlink')
        if cfg.get('us_index_sha256') != sha(expected_us):
            raise ValueError('US index snapshot differs from the reviewed preflight input')
        us_files = [expected_us]
    if kind == 'us_sector':
        expected_sox = ROOT/'runtime_outputs/etf_rotation_research/NASDAQSOX_cold_20260324.csv'
        expected_ndx = ROOT/'runtime_outputs/etf_rotation_research/us_index_source_preflight_20260925/NASDAQ100.csv'
        for key, digest_key, expected in [('sox_file', 'sox_sha256', expected_sox),
                                          ('ndx_file', 'ndx_sha256', expected_ndx)]:
            if (cfg.get(key) != str(expected.relative_to(ROOT)) or
                    not expected.is_file() or expected.is_symlink() or
                    cfg.get(digest_key) != sha(expected)):
                raise ValueError(f'US semiconductor source differs from reviewed snapshot: {key}')
        us_files = [expected_sox, expected_ndx]
    if kind == 'us_vix':
        expected_vix = ROOT/'runtime_outputs/etf_rotation_research/VIXCLS_cold_20260324.csv'
        if (cfg.get('vix_file') != str(expected_vix.relative_to(ROOT)) or
                not expected_vix.is_file() or expected_vix.is_symlink() or
                cfg.get('vix_sha256') != sha(expected_vix)):
            raise ValueError('VIX source differs from reviewed local snapshot')
        us_files = [expected_vix]
    if kind == 'us_style':
        expected_value = ROOT/'runtime_outputs/etf_rotation_research/NASDAQNQUSLV_cold_20260324.csv'
        expected_growth = ROOT/'runtime_outputs/etf_rotation_research/NASDAQNQUSLG_cold_20260324.csv'
        for key, digest_key, expected in [('value_file', 'value_sha256', expected_value),
                                          ('growth_file', 'growth_sha256', expected_growth)]:
            if (cfg.get(key) != str(expected.relative_to(ROOT)) or
                    not expected.is_file() or expected.is_symlink() or
                    cfg.get(digest_key) != sha(expected)):
                raise ValueError(f'US style source differs from reviewed snapshot: {key}')
        us_files = [expected_value, expected_growth]
    if kind == 'ext_gold':
        expected_gold = ROOT/'runtime_outputs/etf_rotation_research/long_history_proxies/macro/XAUUSD.parquet'
        if (cfg.get('gold_file') != str(expected_gold.relative_to(ROOT)) or
                not expected_gold.is_file() or expected_gold.is_symlink() or
                cfg.get('gold_sha256') != sha(expected_gold)):
            raise ValueError('gold source differs from reviewed local snapshot')
        us_files = [expected_gold]
    if kind == 'ext_copper':
        expected_copper = ROOT/'runtime_outputs/etf_rotation_research/long_history_proxies/macro/CU.parquet'
        if (cfg.get('copper_file') != str(expected_copper.relative_to(ROOT)) or
                not expected_copper.is_file() or expected_copper.is_symlink() or
                cfg.get('copper_sha256') != sha(expected_copper)):
            raise ValueError('copper source differs from reviewed local snapshot')
        us_files = [expected_copper]
    if kind == 'ext_crude':
        expected_crude = ROOT/'runtime_outputs/etf_rotation_research/long_history_proxies/macro/SC.parquet'
        if (cfg.get('crude_file') != str(expected_crude.relative_to(ROOT)) or
                not expected_crude.is_file() or expected_crude.is_symlink() or
                cfg.get('crude_sha256') != sha(expected_crude)):
            raise ValueError('crude source differs from reviewed local snapshot')
        us_files = [expected_crude]
    if kind == 'ext_cnh':
        expected_cnh = ROOT/'runtime_outputs/etf_rotation_research/long_history_proxies/macro/USDCNH.parquet'
        if (cfg.get('cnh_file') != str(expected_cnh.relative_to(ROOT)) or
                not expected_cnh.is_file() or expected_cnh.is_symlink() or
                cfg.get('cnh_sha256') != sha(expected_cnh)):
            raise ValueError('USDCNH source differs from reviewed local snapshot')
        us_files = [expected_cnh]
    if kind == 'ext_hktech':
        expected_hktech = ROOT/'runtime_outputs/etf_rotation_research/long_history_proxies/HKTECH.parquet'
        if (cfg.get('hktech_file') != str(expected_hktech.relative_to(ROOT)) or
                not expected_hktech.is_file() or expected_hktech.is_symlink() or
                cfg.get('hktech_sha256') != sha(expected_hktech)):
            raise ValueError('HKTECH source differs from reviewed local snapshot')
        us_files = [expected_hktech]
    if kind == 'ext_realrate':
        expected_realrate = ROOT/'runtime_outputs/etf_rotation_research/long_history_proxies/macro/us_trycr.parquet'
        if (cfg.get('realrate_file') != str(expected_realrate.relative_to(ROOT)) or
                not expected_realrate.is_file() or expected_realrate.is_symlink() or
                cfg.get('realrate_sha256') != sha(expected_realrate)):
            raise ValueError('real-rate source differs from reviewed local snapshot')
        us_files = [expected_realrate]
    if kind == 'ext_coal':
        expected_coal = ROOT/'runtime_outputs/etf_rotation_research/long_history_proxies/macro/JM.parquet'
        if (cfg.get('coal_file') != str(expected_coal.relative_to(ROOT)) or
                not expected_coal.is_file() or expected_coal.is_symlink() or
                cfg.get('coal_sha256') != sha(expected_coal)):
            raise ValueError('coal source differs from reviewed local snapshot')
        us_files = [expected_coal]
    macro_inputs = kind == 'claude_rounds' and cfg.get('macro_inputs') is True
    macro_root = ROOT/'runtime_outputs/etf_rotation_research/long_history_proxies/macro'
    macro_files: list[Path] = []
    if macro_inputs:
        # Round 11 (master's own formulas: macro exposure family). These 5
        # files live under runtime_outputs/, a different root than the
        # canonical price data store `root` -- research-only read-only
        # proxy series, not canonical price data, so they are hashed and
        # bound into the PLAN's input_hashes separately from `files`
        # rather than folded into the canonical-root symlink-escape check
        # above (which is specific to `root`'s own symlink safety).
        # Scoped to this flag so every other claude_rounds config
        # (macro_inputs unset/false) is completely unaffected.
        macro_files = [macro_root/f'{name}.parquet'
                       for name in ('us_trycr', 'us_tycr', 'USDCNH', 'CU', 'T')]
        missing_macro = [f for f in macro_files if not f.is_file()]
        if missing_macro:
            raise FileNotFoundError(f'missing macro input files: {missing_macro}')
    parent_engine=interaction_engine if kind=='interaction' else source_engine
    if kind in ('self_state','interaction'):
        files.extend(parent_engine.parent_artifacts(ROOT,cfg))
    inputs = {str(f): sha(f) for f in files}
    inputs.update({str(f): sha(f) for f in macro_files})
    inputs.update({str(f): sha(f) for f in us_files})
    out = ROOT/'runtime_outputs/etf_rotation_research/runs'/args.run_id
    out.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__), Path(engine.__file__), Path(primitives.__file__),
               Path(preflight.__file__),
               Path(evidence_engine.__file__), Path(confirmation_engine.__file__),
               Path(run_rules.__file__),
               ETF/'src/etf_strategy/core/etf_rank_utils.py',
               ETF/'src/etf_strategy/canonical_data.py', config_path, group_path, universe]
    if kind not in ('daily','daily_mechanisms','daily_rounds','daily_outcome','claude_rounds','auxiliary_bond','us_index','us_sector','us_vix','us_style','ext_gold','ext_copper','ext_crude','ext_cnh','ext_hktech','ext_realrate','ext_coal','autoresearch','domestic_benchmark'):
        sources.append(Path(source_engine.__file__))
    if kind in ('daily_mechanisms','daily_rounds','daily_outcome','claude_rounds','auxiliary_bond','us_index','us_sector','us_vix','us_style','ext_gold','ext_copper','ext_crude','ext_cnh','ext_hktech','ext_realrate','ext_coal','autoresearch','domestic_benchmark'):
        sources.append(Path(daily_engine.__file__))
    if kind == 'autoresearch':
        sources.append(daily_engine.frozen_source(cfg))
    if kind == 'us_vix':
        # VIX score construction reuses the frozen D-1 beta arithmetic here.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'us_style':
        # US style scores reuse the same frozen D-1 beta arithmetic.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'ext_gold':
        # Gold scores reuse the same frozen D-1 beta arithmetic.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'ext_copper':
        # Copper scores reuse the same frozen D-1 beta arithmetic.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'ext_crude':
        # Crude scores reuse the same frozen D-1 beta arithmetic.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'ext_cnh':
        # USDCNH scores reuse the same frozen D-1 beta arithmetic.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'ext_hktech':
        # HKTECH scores reuse the same frozen D-1 beta arithmetic.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'ext_realrate':
        # Real-rate scores reuse the same frozen D-1 beta arithmetic.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'ext_coal':
        # Coal scores reuse the same frozen D-1 beta arithmetic.
        sources.append(ETF/'src/etf_strategy/core/etf_group_us_sector.py')
    if kind == 'us_index':
        sources.append(Path(us_source.__file__))
    if kind == 'daily_rounds':
        sources.extend(Path(module.__file__) for module in daily_engine.LUNA_MODULES)
    if kind=='interaction':
        sources.append(Path(interaction_engine.__file__))
    if approval is not None:
        approved_hashes = {str(f): sha(f) for f in sources}
        if approval.get('source_hashes') != approved_hashes:
            raise ValueError('source/config differs from master-reviewed batch')
        sources.append(approval_path)
    snapshot = out/'source'
    snapshot.mkdir()
    for f in sources:
        shutil.copyfile(f, snapshot/f.name)
    definition_names = run_rules.candidate_ids(cfg)
    if len(definition_names)>cfg['budget_cap'] or len(set(definition_names)) != len(definition_names):
        raise ValueError('candidate definitions violate budget or uniqueness')
    plan = {'created_utc': datetime.now(timezone.utc).isoformat(), 'config': cfg,
            'candidate_ids': definition_names, 'evaluated_ids': ['momentum_20'] if args.pilot else definition_names,
            'input_hashes': inputs, 'source_hashes': {str(f): sha(f) for f in sources},
            'surface_status': 'PREVIOUSLY_SEEN_NOT_OOS', 'cost_model': 'none_factor_research_only',
            'command': [sys.executable, *sys.argv], 'historical_pit_population': False,
            'calendar_only_symbol': cfg['calendar_symbol'], 'member_aggregation': 'mean_raw_same_units',
            'weights': 'equal_member_at_entry_then_hold; equal_groups_at_entry',
            'source_type':kind,
            'batch_approval':str(approval_path) if approval_path else None,
            'availability_status':cfg.get('availability_status','D_CLOSE_BARS_SOURCE_VINTAGE_NOT_CERTIFIED'),
            'not_tested': ['existing shelf marginal contribution', 'original publication/vintage verification'],
            'prior_search': 'not reset; legacy and scratchpad searches exist; this is not independent confirmation'}
    cd = pd.read_parquet(calendar_file, columns=['trade_date'])
    plan['cold_holdout'] = run_rules.enforce_cold_holdout(
        cfg, pd.DatetimeIndex(pd.to_datetime(cd.trade_date)).sort_values(), approval)
    print(f"cold holdout: {plan['cold_holdout']}", flush=True)
    reserve_plan(out, plan)
    print(f'PLAN frozen: {out}; {len(definition_names)} registered definitions', flush=True)
    panels = load_canonical_daily(root, universe, as_of=cfg['as_of'], roles=('candidate',))
    calendar = pd.DatetimeIndex(pd.to_datetime(cd.trade_date)).sort_values()
    if calendar.has_duplicates:
        raise ValueError('duplicate calendar date')
    calendar = calendar[(calendar>=panels['close'].index.min()) & (calendar<=pd.Timestamp(cfg['as_of']))]
    if len(panels['close'].index.difference(calendar)):
        raise ValueError('candidate sessions absent from reference calendar')
    panels = {k: p.reindex(calendar) for k, p in panels.items()}
    feature_engine=daily_engine if kind in ('daily','daily_mechanisms','daily_rounds','daily_outcome','claude_rounds','auxiliary_bond','us_index','us_sector','us_vix','us_style','ext_gold','ext_copper','ext_crude','ext_cnh','ext_hktech','ext_realrate','ext_coal','autoresearch','domestic_benchmark') else interaction_engine if kind=='interaction' else source_engine
    feature_cfg={**cfg,'_groups':groups} if kind=='interaction' else cfg
    if kind in ('daily','daily_mechanisms','daily_rounds','daily_outcome','claude_rounds','auxiliary_bond','us_index','us_sector','us_vix','us_style','ext_gold','ext_copper','ext_crude','ext_cnh','ext_hktech','ext_realrate','ext_coal','autoresearch','domestic_benchmark'):
        feature_panels=panels
        if kind == 'auxiliary_bond':
            auxiliary = load_canonical_daily(root, universe, as_of=cfg['as_of'], roles=('defensive_tool',))
            feature_panels = {'close': panels['close'],
                              'bond_close': auxiliary['close'][['511010.SH']].reindex(calendar)}
        if kind == 'us_index':
            raw = us_files[0].read_bytes()
            source = us_source.parse_series(raw, 'NASDAQ100', pd.Timestamp(cfg['as_of']))
            aligned = us_source.align_known_returns(source, calendar)
            feature_panels = {'close': panels['close'],
                              'us_return': aligned[['return']].rename(columns={'return': 'NASDAQ100'})}
        if kind == 'us_sector':
            sox = daily_engine.read_fred(us_files[0], 'NASDAQSOX', cfg['sox_sha256'], pd.Timestamp(cfg['as_of']))
            ndx = daily_engine.read_fred(us_files[1], 'NASDAQ100', cfg['ndx_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_specific_shock(sox, ndx, calendar)
            feature_panels = {'close': panels['close'], 'us_sector_shock': aligned}
        if kind == 'us_vix':
            vix_source = daily_engine.read_vix(us_files[0], cfg['vix_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_vix_shock(vix_source, calendar)
            feature_panels = {'close': panels['close'], 'us_vix_shock': aligned}
        if kind == 'us_style':
            value_source = daily_engine.read_style(us_files[0], 'NASDAQNQUSLV',
                                                   cfg['value_sha256'], pd.Timestamp(cfg['as_of']))
            growth_source = daily_engine.read_style(us_files[1], 'NASDAQNQUSLG',
                                                    cfg['growth_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_style_shock(value_source, growth_source, calendar)
            feature_panels = {'close': panels['close'], 'us_style_shock': aligned}
        if kind == 'ext_gold':
            gold_source = daily_engine.read_gold(us_files[0], cfg['gold_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_gold_shock(gold_source, calendar)
            feature_panels = {'close': panels['close'], 'ext_gold_shock': aligned}
        if kind == 'ext_copper':
            copper_source = daily_engine.read_copper(us_files[0], cfg['copper_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_copper_shock(copper_source, calendar)
            feature_panels = {'close': panels['close'], 'ext_copper_shock': aligned}
        if kind == 'ext_crude':
            crude_source = daily_engine.read_crude(us_files[0], cfg['crude_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_crude_shock(crude_source, calendar)
            feature_panels = {'close': panels['close'], 'ext_crude_shock': aligned}
        if kind == 'ext_cnh':
            cnh_source = daily_engine.read_cnh(us_files[0], cfg['cnh_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_cnh_shock(cnh_source, calendar)
            feature_panels = {'close': panels['close'], 'ext_cnh_shock': aligned}
        if kind == 'ext_hktech':
            hktech_source = daily_engine.read_hktech(us_files[0], cfg['hktech_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_hktech_shock(hktech_source, calendar)
            feature_panels = {'close': panels['close'], 'ext_hktech_shock': aligned}
        if kind == 'ext_realrate':
            realrate_source = daily_engine.read_realrate(us_files[0], cfg['realrate_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_realrate_shock(realrate_source, calendar)
            feature_panels = {'close': panels['close'], 'ext_realrate_shock': aligned}
        if kind == 'ext_coal':
            coal_source = daily_engine.read_coal(us_files[0], cfg['coal_sha256'], pd.Timestamp(cfg['as_of']))
            aligned = daily_engine.align_coal_shock(coal_source, calendar)
            feature_panels = {'close': panels['close'], 'ext_coal_shock': aligned}
        if kind == 'domestic_benchmark':
            auxiliary = load_canonical_daily(root, universe, as_of=cfg['as_of'], roles=('benchmark',))
            feature_panels = {'close': panels['close'],
                              'benchmark_close': auxiliary['close'][cfg['auxiliary_symbols']].reindex(calendar)}
        if minute_inputs:
            minute_panels = daily_engine.load_minute_panels(root, symbols, cfg['as_of'])
            minute_panels = daily_engine.apply_513100_halt_mask(minute_panels, root)
            feature_panels = {**feature_panels, 'minute': minute_panels}
        if macro_inputs:
            macro_panel = daily_engine.load_macro_panel(macro_root, cfg['as_of'])
            feature_panels = {**feature_panels, 'macro': macro_panel}
    elif kind in ('self_state','interaction'):
        feature_panels,audits=parent_engine.load_parent_source(ROOT,groups,calendar,cfg)
        write_json(out/'source_audit.json',audits)
    else:
        feature_panels,audits,raw_checks=source_engine.load_source(root,symbols,calendar,cfg)
        # New source atoms that relate a non-OHLCV/minute summary to the
        # close-to-close return use the canonical adjusted daily close.  The
        # source loader still owns source-specific usable-date/stale checks;
        # this panel supplies only the D-close price leg.
        if kind in ('minute', 'share'):
            feature_panels['close'] = panels['close'].reindex(calendar)
        if kind == 'share':
            # Batch23 share-amount cross mechanisms need canonical daily
            # turnover alongside the share/close panels already supplied
            # above. Existing share mechanisms never read this key.
            feature_panels['amount'] = panels['amount'].reindex(calendar)
        write_json(out/'source_audit.json',audits)
        write_json(out/'raw_source_leak_check.json',raw_checks)
    atoms = feature_engine.build_atoms(feature_panels, feature_cfg)
    base_known = (panels['close'].notna().rolling(cfg['warmup']).sum().eq(cfg['warmup']).all(axis=1)
                  & panels['volume'].gt(0).all(axis=1))
    feature_coverage = preflight.inspect_feature_coverage(atoms, groups, cfg, base_known)
    write_json(out/'feature_precheck.json', feature_coverage)
    infeasible = [name for name, report in feature_coverage.items()
                  if not report['structurally_eligible']]
    if infeasible:
        raise ValueError(f'no common rankable feature dates; record precheck rejection before formal evaluation: {infeasible}')
    checks = {}
    for cut in ('2024-12-31', '2025-12-31'):
        checks[cut] = feature_engine.leakage_checks(feature_panels, feature_cfg, cut)
    # Reload truncated canonical input too: adjustment normalization must not change features.
    prefix_panels = load_canonical_daily(root, universe, as_of='2024-12-31', roles=('candidate',))
    prefix_panels = {k: p.reindex(calendar[calendar<=pd.Timestamp('2024-12-31')]) for k,p in prefix_panels.items()}
    if minute_inputs:
        prefix_minute = daily_engine.load_minute_panels(root, symbols, '2024-12-31')
        prefix_minute = daily_engine.apply_513100_halt_mask(prefix_minute, root)
        prefix_panels = {**prefix_panels, 'minute': prefix_minute}
    if macro_inputs:
        prefix_macro = daily_engine.load_macro_panel(macro_root, '2024-12-31')
        prefix_panels = {**prefix_panels, 'macro': prefix_macro}
    if kind == 'auxiliary_bond':
        prefix_auxiliary = load_canonical_daily(root, universe, as_of='2024-12-31', roles=('defensive_tool',))
        prefix_panels = {'close': prefix_panels['close'],
                         'bond_close': prefix_auxiliary['close'][['511010.SH']].reindex(
                             calendar[calendar <= pd.Timestamp('2024-12-31')])}
    if kind == 'domestic_benchmark':
        prefix_auxiliary = load_canonical_daily(root, universe, as_of='2024-12-31', roles=('benchmark',))
        prefix_panels = {'close': prefix_panels['close'],
                         'benchmark_close': prefix_auxiliary['close'][cfg['auxiliary_symbols']].reindex(
                             calendar[calendar <= pd.Timestamp('2024-12-31')])}
    if kind == 'us_index':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_source = us_source.parse_series(us_files[0].read_bytes(), 'NASDAQ100',
                                               pd.Timestamp(cfg['as_of']))
        prefix_aligned = us_source.align_known_returns(prefix_source, prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'],
                         'us_return': prefix_aligned[['return']].rename(columns={'return': 'NASDAQ100'})}
    if kind == 'us_sector':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_specific_shock(sox.loc[:'2024-12-31'],
                                                         ndx.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'us_sector_shock': prefix_shock}
    if kind == 'us_vix':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_vix_shock(vix_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'us_vix_shock': prefix_shock}
    if kind == 'us_style':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_style_shock(value_source.loc[:'2024-12-31'],
                                                      growth_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'us_style_shock': prefix_shock}
    if kind == 'ext_gold':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_gold_shock(gold_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'ext_gold_shock': prefix_shock}
    if kind == 'ext_copper':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_copper_shock(copper_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'ext_copper_shock': prefix_shock}
    if kind == 'ext_crude':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_crude_shock(crude_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'ext_crude_shock': prefix_shock}
    if kind == 'ext_cnh':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_cnh_shock(cnh_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'ext_cnh_shock': prefix_shock}
    if kind == 'ext_hktech':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_hktech_shock(hktech_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'ext_hktech_shock': prefix_shock}
    if kind == 'ext_realrate':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_realrate_shock(realrate_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'ext_realrate_shock': prefix_shock}
    if kind == 'ext_coal':
        prefix_calendar = calendar[calendar <= pd.Timestamp('2024-12-31')]
        prefix_shock = daily_engine.align_coal_shock(coal_source.loc[:'2024-12-31'], prefix_calendar)
        prefix_panels = {'close': prefix_panels['close'], 'ext_coal_shock': prefix_shock}
    if kind in ('daily','daily_mechanisms','daily_rounds','daily_outcome','claude_rounds','auxiliary_bond','us_index','us_sector','us_vix','us_style','ext_gold','ext_copper','ext_crude','ext_cnh','ext_hktech','ext_realrate','ext_coal','autoresearch','domestic_benchmark'):
        for n, a in feature_engine.build_atoms(prefix_panels, cfg).items():
            pd.testing.assert_frame_equal(atoms[n].loc[:'2024-12-31'], a, check_exact=False, rtol=1e-7, atol=1e-10)
    write_json(out/'future_leak_check.json', {'all_pass': True, 'checks': checks, 'canonical_reload_prefix': kind in ('daily','daily_mechanisms','daily_rounds','daily_outcome','claude_rounds','auxiliary_bond','us_index','us_sector','us_vix','us_style','ext_gold','ext_copper','ext_crude','ext_cnh','ext_hktech','ext_realrate','ext_coal','autoresearch','domestic_benchmark'),
               'raw_source_prefix_and_perturbation':kind in ('minute','share','nav'),
               'parent_artifacts_inherit_original_raw_checks':kind in ('self_state','interaction'),
               'scope': 'tested feature causality; not source-vintage or execution certification'})
    returns, timing = engine.labels(panels, cfg['entry_lag'], cfg['horizon'])
    if kind in ('self_state','interaction'):
        for p in parent_engine.parent_artifacts(ROOT,cfg):
            if p.name=='group_labels.csv':
                pd.testing.assert_frame_equal(engine.aggregate(returns,groups),
                    pd.read_csv(p,index_col=0,parse_dates=True),check_names=False,check_freq=False)
    date_mask = (calendar>=pd.Timestamp(cfg['evaluation_start']))
    evaluation_calendar = calendar[date_mask]
    timing['in_evaluation_window'] = date_mask
    timing['known_complete'] = base_known
    timing['labels_complete'] = returns.notna().all(axis=1)
    timing.to_csv(out/'coverage.csv', index=False)
    group_returns = engine.aggregate(returns, groups)
    group_returns.to_csv(out/'group_labels.csv', index_label='signal_date')
    records, summaries, yearly, loso, paired = [], [], [], [], []
    group_scores = {}
    for name in plan['evaluated_ids']:
        evidence_policy = confirmation_engine.evidence_policy(cfg, name)
        known = candidate_known_mask(base_known, atoms[name])
        score = engine.aggregate(atoms[name], groups)
        group_scores[name] = score
        frame, weights = engine.evaluate(score, returns, groups, known, timing, cfg['top_k'])
        frame = frame.loc[evaluation_calendar]
        valid_dates = frame.ic.dropna().index
        if len(valid_dates):
            assert (frame.loc[valid_dates, 'signal_date'] < frame.loc[valid_dates, 'entry_date']).all()
            assert (frame.loc[valid_dates, 'entry_date'] < frame.loc[valid_dates, 'exit_date']).all()
        frame.insert(0, 'candidate', name)
        records.append(frame)
        row = {'candidate': name, **engine.summarize(frame, evaluation_calendar, cfg['hac_lag'])}
        row['first_signal'] = str(valid_dates.min().date()) if len(valid_dates) else None
        row['last_signal'] = str(valid_dates.max().date()) if len(valid_dates) else None
        year_stats = []
        historical_2026_row = None
        for year in sorted(set(evaluation_calendar.year)):
            part = frame.loc[frame.index.year==year].copy()
            # Purge exits across year boundaries; do not borrow next year's labels.
            part.loc[part.exit_date.dt.year.ne(year), ['ic','excess8','excess14','allocation_effect']] = np.nan
            ys = {'candidate': name, 'year': year, **engine.summarize(part, part.index, cfg['hac_lag'])}
            yearly.append(ys)
            if year == 2026:
                historical_2026_row = dict(ys)
            if ys['n'] >= cfg['screens']['min_year_days']:
                year_stats.append(ys)
        row['positive_years'] = sum(y['ic_mean']>0 for y in year_stats)
        row['all_eligible_years_positive'] = bool(year_stats) and all(y['ic_mean']>0 for y in year_stats)
        means = []
        historical_2026_means = []
        for g in groups:
            if kind=='interaction':
                ss=interaction_engine.leave_group_score(feature_panels,name.removesuffix('_1'),g).where(known,axis=0)
            else:
                ss = score.drop(columns=g).where(known, axis=0)
            yy = group_returns.drop(columns=g)
            # Keep original complete-14-date mask even when leaving out a group.
            ic = stable_rank(ss).corrwith(yy.rank(axis=1, method='average'), axis=1).where(frame.ic.reindex(calendar).notna())
            means.append(float(ic.mean()))
            historical_2026_ic = ic.loc[ic.index.year == 2026]
            historical_2026_means.append(float(historical_2026_ic.mean()))
            loso.append({'candidate': name, 'omitted_group': g, 'ic_mean': float(ic.mean()),
                         'ic_hac_t': primitives.newey_west_t_calendar(ic, calendar, cfg['hac_lag']),
                         'historical_2026_ic_mean': float(historical_2026_ic.mean()),
                         'historical_2026_ic_hac_t': primitives.newey_west_t_calendar(
                             historical_2026_ic, calendar[calendar.year == 2026], cfg['hac_lag'])})
        row['min_leave_group_ic'] = min(means)
        if historical_2026_row is None:
            historical_2026_row = {}
        historical_2026_row['min_leave_group_ic'] = min(historical_2026_means)
        for key, value in historical_2026_row.items():
            if key not in {'candidate', 'year'}:
                row[f'historical_2026_{key}'] = value
        s = cfg['screens']
        gates = {
            'coverage': row['n']>=s['min_days'], 'ic': row['ic_mean']>=s['min_ic'],
            'hac': row['ic_hac_t']>=s['min_ic_hac_t'], 'block': row['ic_block_t']>=s['min_ic_block_t'],
            'budget_diagnostic': row['ic_p_normal_one_sided']<=s['alpha']/cfg['budget_cap'],
            'economic': row['excess8_mean']>0 and row['excess8_hac_t']>=s['min_excess8_hac_t'],
            'years': row['all_eligible_years_positive'] and row['positive_years']>=s['min_positive_years'],
            'leave_group': row['min_leave_group_ic']>0,
        }
        paired_ic_rows = None
        paired_economic_rows = None
        paired_calendar = (
            evaluation_calendar[evaluation_calendar.year == 2026]
            if evidence_policy == '2025_DIRECTION_2026_HISTORICAL_SEGMENT'
            else evaluation_calendar
        )
        paired_min_days = 120 if evidence_policy == '2025_DIRECTION_2026_HISTORICAL_SEGMENT' else s['min_days']
        if kind=='interaction':
            mechanism=name.removesuffix('_1')
            increments=[]
            paired_ic_rows=[]
            paired_economic_rows=[]
            for side in ('left','right'):
                leg=feature_panels[mechanism+'__'+side]
                leg_known = candidate_known_mask(base_known, leg)
                leg_frame,_=engine.evaluate(leg,returns,groups,leg_known,timing,cfg['top_k'])
                stats=interaction_engine.paired_increment(frame,leg_frame,paired_calendar,cfg['hac_lag'])
                paired.append({'candidate':name,'side':side,
                               'parent':cfg['mechanisms'][mechanism][side]['parent_candidate'],**stats})
                increments.append(stats)
                paired_ic_rows.append(stats)
                paired_economic_rows.append(stats)
            gates['paired_increment']=all(
                r['ic_n']>=paired_min_days and r['ic_increment_mean']>0
                and r['ic_increment_hac_t']>=cfg['paired_min_hac_t']
                for r in increments)
            row['min_paired_ic_hac_t']=min(r['ic_increment_hac_t'] for r in increments)
            row['min_paired_excess_hac_t']=min(r['excess8_increment_hac_t'] for r in increments)
        elif hasattr(feature_engine, 'build_paired_legs'):
            legs = feature_engine.build_paired_legs(feature_panels, cfg, name)
            if legs is not None:
                increments=[]
                paired_ic_rows=[]
                paired_economic_rows=[]
                for side, leg_atom in legs.items():
                    leg_known = candidate_known_mask(base_known, leg_atom)
                    leg_score = engine.aggregate(leg_atom, groups)
                    leg_frame,_ = engine.evaluate(
                        leg_score, returns, groups, leg_known, timing, cfg['top_k'])
                    stats = interaction_engine.paired_increment(
                        frame, leg_frame, paired_calendar, cfg['hac_lag'])
                    paired.append({'candidate':name, 'side':side,
                                   'parent':f'{name}:{side}', **stats})
                    increments.append(stats)
                    paired_ic_rows.append(stats)
                    paired_economic_rows.append(stats)
                gates['paired_increment']=all(
                    r['ic_n']>=paired_min_days and r['ic_increment_mean']>0
                    and r['ic_increment_hac_t']>=2.0 for r in increments)
                row['min_paired_ic_hac_t']=min(r['ic_increment_hac_t'] for r in increments)
                row['min_paired_excess_hac_t']=min(r['excess8_increment_hac_t'] for r in increments)
        row['requires_paired_increment'] = paired_ic_rows is not None
        row['screen_pass'] = all(gates.values())
        row['all_layers'] = row['screen_pass']
        evidence_screens = {
            **s,
            'min_historical_2026_days': 120,
            'paired_min_days': paired_min_days,
            'paired_min_hac_t': cfg.get('paired_min_hac_t', 2.0),
        }
        row.update(evidence_engine.evidence_layers(
            row, evidence_screens, cfg['budget_cap'],
            paired_ic=paired_ic_rows,
            paired_economic=paired_economic_rows,
            historical_2026_row=historical_2026_row,
            evidence_policy=evidence_policy,
        ))
        row['failed_screens'] = ','.join(k for k,v in gates.items() if not v)
        row['evidence_status'] = (
            'COVERAGE_INSUFFICIENT' if not row['coverage_sufficient'] else
            'IC_EVIDENCE_SUPPORTED' if row['ic_supported'] else
            'HISTORICAL_IC_LEAD_ONLY' if row['historical_ic_supported'] else
            'SEEN_2026_NOT_CONFIRMATION' if row['historical_2026_contaminated'] else
            'REVERSE_WATCH_NOT_VALIDATED' if row['reverse_watch'] else
            'NOT_SUPPORTED_THIS_SCREEN'
        )
        summaries.append(row)
        score.loc[evaluation_calendar].to_csv(out/f'scores_{name}.csv', index_label='signal_date')
        weights.loc[evaluation_calendar].to_csv(out/f'weights_{name}.csv', index_label='signal_date')
        print(f'{name}: n={row["n"]}, IC={row["ic_mean"]:.4f}, t={row["ic_hac_t"]:.2f}, '
              f'ic_supported={row["ic_supported"]}, screen={row["screen_pass"]}', flush=True)
    if not unchanged_hashes([*files, *macro_files, *us_files], inputs):
        raise RuntimeError('inputs changed during run; no valid verdict')
    if not unchanged_hashes(sources, plan['source_hashes']):
        raise RuntimeError('source/config changed during run; no valid verdict')
    summary = pd.DataFrame(summaries).sort_values(['ic_hac_t','candidate'], ascending=[False,True])
    leads = []
    for row in summary.to_dict('records'):
        if not row['screen_pass'] or len(leads)>=cfg['max_leads']:
            continue
        name = row['candidate']
        redundant = any(stable_rank(group_scores[name]).corrwith(stable_rank(group_scores[n]),axis=1)
            .loc[evaluation_calendar].abs().mean() >= cfg['screens']['max_abs_rank_corr'] for n in leads)
        if not redundant:
            leads.append(name)
    summary['legacy_combined_shortlisted'] = summary.candidate.isin(leads)
    summary['shortlisted'] = summary['legacy_combined_shortlisted']
    # These are discovery views: no de-duplication and no independent
    # confirmation is applied to the IC lists.
    ic_candidates = summary.loc[summary['ic_supported'], 'candidate'].tolist()
    ic_budget_candidates = summary.loc[summary['ic_budget_supported'], 'candidate'].tolist()
    reverse_watch_candidates = summary.loc[summary['reverse_watch'], 'candidate'].tolist()
    economic_candidates = summary.loc[summary['economic_supported'], 'candidate'].tolist()
    joint_mask = summary['ic_budget_supported'] & summary['economic_supported']
    joint_mask &= (~summary['requires_paired_increment']) | summary['paired_ic_supported'].eq(True)
    joint_candidates = summary.loc[joint_mask, 'candidate'].tolist()
    summary['ic_economic_metric_joint'] = joint_mask
    summary.to_csv(out/'summary.csv', index=False)
    pd.concat(records).to_csv(out/'daily_metrics.csv', index=False)
    pd.DataFrame(yearly).to_csv(out/'yearly.csv', index=False)
    pd.DataFrame(loso).to_csv(out/'leave_group.csv', index=False)
    if paired:
        pd.DataFrame(paired).to_csv(out/'paired_increment.csv',index=False)
    verdict = {'status': 'DISCOVERY_ONLY', 'evaluated': len(summaries), 'registered':len(definition_names),
               'primary_evidence_field': 'ic_candidates',
               'shortlisted_semantics': 'legacy_combined_not_ic_evidence_count',
               'budget_cap':cfg['budget_cap'], 'shortlisted':leads, 'certified_factors':0,
               'cumulative_registered_definitions':plan['cumulative_registered_definitions'],
               'availability_status':plan['availability_status'],
               'paired_leg_increment_checked': bool(summary['requires_paired_increment'].any()),
               'paired_candidates': summary.loc[summary['requires_paired_increment'], 'candidate'].tolist(),
               'surface_policy': 'prior directions use full seen-history window; 2025-chosen directions use the 2026 historical segment only; no historical segment is independent confirmation',
               'external_shelf_check': 'NOT_RUN', 'source_vintage_audit':'NOT_CERTIFIED',
               'no_live_permission':True, 'input_hashes_unchanged':True,
               'ic_candidates': ic_candidates,
               'ic_budget_candidates': ic_budget_candidates,
               'economic_candidates': economic_candidates,
               'joint_candidates': joint_candidates,
               'ic_economic_metric_joint': joint_candidates,
               'reverse_watch_candidates': reverse_watch_candidates,
               'legacy_combined_shortlist': leads,
               'evidence_counts': {
                   'ic_base': len(ic_candidates),
                   'ic_budget_corrected': len(ic_budget_candidates),
                   'economic': len(economic_candidates),
                   'joint': len(joint_candidates),
                   'reverse_watch': len(reverse_watch_candidates),
               }}
    write_json(out/'verdict.json', verdict)
    lines = ['# Eight-group discovery report', '', 'Seen history only; not independent OOS or a trading strategy.',
             f"Window: {cfg['evaluation_start']} to {cfg['as_of']}; D+2 -> D+7; K=2; 14 fixed ETFs / 8 groups.",
             'Primary statistic: signed H5 rank IC. Main return benchmark B8; mandatory original-pool comparison B14.',
             'Gross adjusted-open research labels; no costs or claim of achievable fills.',
             f'Evaluated {len(summaries)} / registered {len(definition_names)} / budget cap {cfg["budget_cap"]}.',
             'Legacy combined shortlist: '+(', '.join(leads) or 'none')+'. Certified factors: 0.',
             f"IC base leads (un-deduplicated, not independently confirmed): {len(ic_candidates)}.",
             f"Budget-corrected IC leads: {len(ic_budget_candidates)}.",
             f"Economic-supported leads: {len(economic_candidates)}; joint IC+economic: {len(joint_candidates)}.",
             f"Reverse watch candidates: {len(reverse_watch_candidates)}; reverse flip is not new evidence.",
             'Prior searches remain seen-history debt; normal-tail budget screen is diagnostic, not certification.',
             f"Source: {kind}; availability: {plan['availability_status']}.",
             f"Cumulative registered definitions: {plan['cumulative_registered_definitions']} / {cfg['budget_cap']}.",
             'Existing shelf increment and original publication/vintage verification remain untested.', '',
             '| Candidate | Policy | N | IC | HAC t | 2026 IC | 2026 t | IC supported | IC budget | Economic | Reverse watch | Excess B8 bp | Excess B14 bp | Failed screens |',
             '|---|---|---:|---:|---:|---:|---:|---|---|---|---|---:|---:|---|']
    for r in summary.to_dict('records'):
        lines.append(f"| {r['candidate']} | {r['evidence_policy']} | {r['n']} | {r['ic_mean']:.4f} | {r['ic_hac_t']:.2f} | {r.get('historical_2026_ic_mean', float('nan')):.4f} | {r.get('historical_2026_ic_hac_t', float('nan')):.2f} | {r['ic_supported']} | {r['ic_budget_supported']} | {r['economic_supported']} | {r['reverse_watch']} | {r['excess8_mean']*1e4:.1f} | {r['excess14_mean']*1e4:.1f} | {r['failed_screens']} |")
    lines += ['', 'Reproduce command: `'+ ' '.join(plan['command'])+'` (use a new run-id; existing outputs are immutable).',
              'Evidence: PLAN.json, future_leak_check.json, coverage.csv, summary.csv, yearly.csv, leave_group.csv, daily_metrics.csv, source/.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(verdict), flush=True)


if __name__ == '__main__':
    main()
