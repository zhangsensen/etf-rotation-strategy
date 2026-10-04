from __future__ import annotations

from pathlib import Path

from etf_strategy.core.etf_mining_referee import campaign_bonferroni_pass


def _load_audit_module():
    import importlib.util

    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/research/pi_glm_mining/audit/rejudge_referee_v4.py"
    )
    spec = importlib.util.spec_from_file_location("rejudge_referee_v4", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_frozen_rounds_excludes_replays_and_requires_artifacts(tmp_path: Path) -> None:
    module = _load_audit_module()
    outputs = tmp_path / "outputs"
    for name in ("round_002", "round_022_replay", "round_003", "referee_v2_rescore"):
        (outputs / name).mkdir(parents=True)
    for name in ("round_002", "round_003"):
        for artifact in ("PLAN.json", "STATUS.json", "candidate_metrics.csv"):
            (outputs / name / artifact).touch()
    (outputs / "round_003" / "candidate_metrics.csv").unlink()
    assert [path.name for path in module.frozen_rounds(tmp_path)] == ["round_002"]


def test_campaign_gate_uses_fixed_budget() -> None:
    passed, _ = campaign_bonferroni_pass(5.0, alpha=0.05, hypothesis_budget=6000)
    failed, _ = campaign_bonferroni_pass(3.0, alpha=0.05, hypothesis_budget=6000)
    assert passed and not failed
