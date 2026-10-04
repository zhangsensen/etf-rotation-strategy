"""Current IC-discovery configuration checks; no authorization or certification."""
from collections.abc import Mapping


FIXED_FIELDS = {
    'purpose': 'seen_history_discovery_only',
    'evaluation_start': '2025-01-01',
    'as_of': '2026-09-17',
    'entry_lag': 2,
    'horizon': 5,
    'top_k': 2,
    'hac_lag': 10,
}
COLD_HOLDOUT_SESSIONS = 126


def enforce_cold_holdout(config, full_calendar, approval, holdout_sessions=COLD_HOLDOUT_SESSIONS):
    """USER 2026-09-24: the most recent ~6 months of data are cold and off-limits to mining.

    ``full_calendar`` is the untruncated reference trading calendar. A new run may
    only read data up to ``full_calendar[-1 - holdout_sessions]`` (the cold line).
    Exceptions, each recorded in the batch approval: ``rejudge_of`` (re-judging
    already-registered definitions adds no search) and a registered
    ``holdout_release`` block (pre-registered candidate list opened once).
    Returns the mode string; raises on violation.
    """
    import pandas as pd
    if len(full_calendar) <= holdout_sessions:
        raise ValueError('reference calendar shorter than the cold holdout')
    cold_line = pd.Timestamp(full_calendar[-1 - holdout_sessions])
    as_of = pd.Timestamp(config['as_of'])
    if as_of <= cold_line:
        return 'COLD_OK'
    if config.get('rejudge_of'):
        return 'REJUDGE_EXEMPT'
    release = (approval or {}).get('holdout_release') if isinstance(approval, Mapping) else None
    if isinstance(release, Mapping) and release.get('registered_candidates') and release.get('user_request'):
        return 'HOLDOUT_RELEASE'
    raise ValueError(
        f"as_of {as_of.date()} is inside the cold holdout (cold line {cold_line.date()}, "
        f"{holdout_sessions} sessions before {pd.Timestamp(full_calendar[-1]).date()}); "
        "mining may not read it without a registered holdout_release approval")


FIXED_SCREENS = {
    'min_days': 360,
    'min_year_days': 40,
    'min_positive_years': 2,
    'min_ic': .01,
    'min_ic_hac_t': 2.0,
    'min_ic_block_t': 2.0,
    'min_excess8_hac_t': 2.0,  # Report-only economic threshold, not an IC gate.
    'alpha': .05,
    'max_abs_rank_corr': .7,
}


def candidate_ids(config):
    """Return exact output identifiers for a frozen batch configuration."""
    if config.get('source_type') in ('daily_outcome', 'autoresearch'):
        return list(config.get('mechanisms', {}))
    if config.get('source_type') == 'claude_rounds':
        # Per-mechanism window (Batch A/B need 60/120/250, not the daily_rounds
        # engine's single global window=20), so there is no shared top-level
        # windows list to take a cross-product over.
        return [f'{name}_{definition["window"]}' for name, definition in config['mechanisms'].items()]
    return [f'{name}_{w}' for w in config['windows'] for name in config['mechanisms']]


def validate_ic_discovery_config(config):
    """Reject implicit evaluation windows or silently changed numeric screens.

    Historical configurations stay frozen and may be inspected via saved
    artifacts. They are not new-run plans. ``start`` remains a history-loading
    field and cannot substitute for ``evaluation_start``.
    """
    if not isinstance(config, Mapping):
        raise ValueError('IC discovery config must be a mapping')
    direction_stage = config.get('discovery_surface') == '2025_DIRECTION_DISCOVERY_ONLY'
    fixed_fields = dict(FIXED_FIELDS)
    if direction_stage:
        fixed_fields['as_of'] = '2025-12-31'
    for key, expected in fixed_fields.items():
        if (key == 'purpose' and config.get('source_type') == 'domestic_benchmark'
                and config.get(key) == 'seen_history_ic_discovery_only'):
            # The frozen two-definition domestic benchmark proposal uses this
            # explicit spelling; its evidence surface remains discovery-only.
            continue
        if key == 'as_of' and not direction_stage:
            # Earlier cutoffs preserve the label and IC contract while allowing
            # the separate calendar-based cold-holdout guard to remain strict.
            from datetime import date
            value = config.get(key)
            try:
                valid = (isinstance(value, str)
                         and date.fromisoformat(value).isoformat() == value
                         and fixed_fields['evaluation_start'] <= value <= expected)
            except (TypeError, ValueError):
                valid = False
            if not valid:
                raise ValueError(f'IC discovery requires explicit as_of within '
                                 f"{fixed_fields['evaluation_start']}..{expected}")
            continue
        if config.get(key) != expected or isinstance(config.get(key), bool):
            raise ValueError(f'IC discovery requires explicit {key}={expected!r}')
    screens = config.get('screens')
    if not isinstance(screens, Mapping):
        raise ValueError('IC discovery requires explicit screens')
    screens_version = config.get('screens_version', 'legacy_360')
    if screens_version not in ('legacy_360', 'cold_250_v1'):
        raise ValueError('unknown IC screen version')
    if screens_version == 'cold_250_v1':
        if config.get('discovery_surface') != 'IC_DISCOVERY_ONLY' or config.get('as_of') != '2026-03-24':
            raise ValueError('cold_250_v1 requires the frozen prior-direction cold window')
        if config.get('rejudge_of'):
            raise ValueError('cold_250_v1 cannot rejudge opened historical definitions')
    expected_screens = {**FIXED_SCREENS, 'min_days': 250} if screens_version == 'cold_250_v1' else FIXED_SCREENS
    for key, expected in expected_screens.items():
        if screens.get(key) != expected or isinstance(screens.get(key), bool):
            raise ValueError(f'IC discovery fixed screen {key}={expected!r}')
    if config.get('source_type') == 'interaction' and config.get('paired_min_hac_t') != 2.0:
        raise ValueError('interaction requires explicit paired_min_hac_t=2.0')
    if config.get('source_type') == 'autoresearch':
        if (config.get('campaign_extension') is not True
                or config.get('evidence_policy') != 'SEEN_2026_ADAPTIVE_NOT_CONFIRMATION'
                or config.get('windows') != [1]
                or len(config.get('mechanisms', {})) != 1
                or config.get('new_definitions') != 1):
            raise ValueError('autoresearch promotion must retain adaptive evidence and one frozen definition')


def validate_batch_approval(config, config_sha256, run_id, approval):
    """Bind this bounded run to master's recorded review, not user identity proof."""
    if not isinstance(approval, Mapping):
        raise ValueError('a batch approval record is required')
    direction_stage = config.get('discovery_surface') == '2025_DIRECTION_DISCOVERY_ONLY'
    required = {
        'reviewer': 'master', 'scope': 'fixed14_eight_groups',
        'stage': '2025_DIRECTION_DISCOVERY_ONLY' if direction_stage else 'IC_DISCOVERY_ONLY',
        'run_id': run_id,
        'config_sha256': config_sha256,
    }
    for key, expected in required.items():
        if approval.get(key) != expected:
            raise ValueError(f'batch approval mismatch: {key}')
    if not isinstance(approval.get('user_request'), str) or not approval['user_request'].strip():
        raise ValueError('batch approval must retain user request')
    ids = candidate_ids(config)
    max_batch = 16 if direction_stage else 8
    if not 1 <= len(ids) <= max_batch or len(set(ids)) != len(ids):
        raise ValueError(f'batch must contain 1..{max_batch} unique definitions')
    is_rejudge = isinstance(config.get('rejudge_of'), str) and bool(config['rejudge_of'].strip())
    expected_new = 0 if is_rejudge else len(ids)
    if approval.get('candidate_ids') != ids or approval.get('max_new_definitions') != expected_new:
        raise ValueError('batch approval candidate list/count mismatch')
    # Existing main-entry 96 registrations plus the reviewed external next8.
    prior = config.get('prior_registered', 104)
    if config.get('campaign_extension') is True:
        if type(prior) is not int or prior < 109:
            raise ValueError('campaign extensions must retain all completed registrations')
    elif config.get('source_type') == 'daily_rounds':
        if type(prior) is not int or prior < 106:
            raise ValueError('new rounds must retain completed batch2 registrations')
    elif prior != 104:
        raise ValueError('historical batch2 prior remains frozen')
    if approval.get('prior_registered') != prior or config.get('external_registered_definitions') != 8:
        raise ValueError('must retain prior96 plus reviewed next8')
    cap = prior + expected_new
    if config.get('budget_cap') != cap or approval.get('budget_cap') != cap:
        raise ValueError('batch approval budget mismatch')
    if is_rejudge and approval.get('rejudge_of') != config['rejudge_of']:
        raise ValueError('rejudge parent mismatch')
    return ids
