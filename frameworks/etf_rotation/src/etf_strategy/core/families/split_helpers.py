"""Compatibility shim (2026-09-21): the single implementation lives in split_math. Kept only so
lane families that import split_helpers keep working; new code imports split_math directly."""
from .split_math import rolling_median_split_diff, rolling_sign_split_diff  # noqa: F401
