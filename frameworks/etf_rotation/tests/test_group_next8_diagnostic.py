from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/research/group_next8_diagnostic.py'


def test_breadth_diagnostic_is_separate_from_evaluation_runner():
    text = SCRIPT.read_text()
    assert 'breadth_vs_existing80_rank_corr.csv' in text
    assert 'breadth_vs_baselines_paired.csv' in text
    assert 'run_group_next8_20260922.py' not in text
