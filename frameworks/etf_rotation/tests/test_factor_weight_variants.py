import numpy as np
import pytest

from build_factor_weight_variants import capped_weights


def test_capped_weights_preserve_sum_and_cap():
    result = capped_weights(np.array([8., 1., 1., 1.]), .30)
    assert result.sum() == pytest.approx(1.)
    assert result.max() == pytest.approx(.30)
    assert result[1:].tolist() == pytest.approx([.7 / 3] * 3)


def test_capped_weights_reject_infeasible_cap():
    with pytest.raises(ValueError, match="infeasible"):
        capped_weights(np.ones(3), .30)
