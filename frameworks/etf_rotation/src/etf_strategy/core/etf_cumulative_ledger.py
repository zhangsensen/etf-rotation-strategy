"""Append-only ETF family-mining ledger, independent of stock research ledgers."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import duckdb
import pandas as pd


class ETFCumulativeLedger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = duckdb.connect(str(self.path))
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS etf_family_generations (
                generation VARCHAR PRIMARY KEY,
                run_hash VARCHAR NOT NULL,
                artifact_path VARCHAR NOT NULL,
                expression_count INTEGER NOT NULL,
                family_count INTEGER NOT NULL,
                alpha_spent DOUBLE NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS etf_family_attempts (
                generation VARCHAR NOT NULL,
                expression_key VARCHAR NOT NULL,
                true_family VARCHAR NOT NULL,
                expression VARCHAR NOT NULL,
                pooled_pvalue DOUBLE,
                final_pass BOOLEAN NOT NULL,
                PRIMARY KEY (generation, expression_key)
            )
        """)
        # Additive metadata; never rewrite or reclassify historical attempts.
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS etf_family_run_provenance (
                generation VARCHAR PRIMARY KEY,
                run_kind VARCHAR NOT NULL,
                replay_of VARCHAR,
                provenance_json VARCHAR NOT NULL
            )
        """)

    def prior_generation_count(self) -> int:
        return int(self.connection.execute("SELECT count(*) FROM etf_family_generations").fetchone()[0])

    def has_generation(self, generation: str) -> bool:
        return bool(self.connection.execute(
            "SELECT count(*) FROM etf_family_generations WHERE generation = ?", [generation]
        ).fetchone()[0])

    def admitted_factor_artifacts(self) -> list[Path]:
        rows = self.connection.execute("""
            SELECT DISTINCT g.artifact_path
            FROM etf_family_generations g
            JOIN etf_family_attempts a USING (generation)
            WHERE a.final_pass
            ORDER BY g.created_at
        """).fetchall()
        return [Path(row[0]) / "admitted_factor_scores.parquet" for row in rows]

    def record(self, generation: str, run_hash: str, artifact_path: str, alpha_spent: float, summary: pd.DataFrame,
               *, run_kind: str = "HYPOTHESIS", replay_of: str | None = None,
               provenance: dict | None = None) -> None:
        if self.has_generation(generation):
            raise ValueError(f"ETF family generation already recorded: {generation}")
        if run_kind not in {"HYPOTHESIS", "CORRECTED_RERUN", "DIAGNOSTIC"}:
            raise ValueError("unsupported run_kind; unverified REPLAY cannot bypass accounting")
        if run_kind == "CORRECTED_RERUN" and not replay_of:
            raise ValueError("CORRECTED_RERUN requires replay_of")
        if replay_of and not self.has_generation(replay_of):
            raise ValueError("replay_of must reference an existing generation")
        self.connection.execute("BEGIN")
        try:
            self.connection.execute(
                "INSERT INTO etf_family_generations VALUES (?, ?, ?, ?, ?, ?, ?)",
                [generation, run_hash, artifact_path, len(summary), summary.true_family.nunique(), alpha_spent, datetime.now(timezone.utc)],
            )
            rows = summary[["expression_key", "true_family", "expression", "pooled_maxstat_pvalue", "family_gate_pass"]].copy()
            rows.insert(0, "generation", generation)
            self.connection.register("attempt_rows", rows)
            self.connection.execute("INSERT INTO etf_family_attempts SELECT * FROM attempt_rows")
            self.connection.unregister("attempt_rows")
            self.connection.execute(
                "INSERT INTO etf_family_run_provenance VALUES (?, ?, ?, ?)",
                [generation, run_kind, replay_of, json.dumps(provenance or {}, sort_keys=True)],
            )
            self.connection.execute("COMMIT")
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def close(self) -> None:
        self.connection.close()


def alpha_spending(total_alpha: float, generation_number: int) -> float:
    """Summable alpha schedule: alpha_k = alpha/(k*(k+1))."""
    if generation_number < 1:
        raise ValueError("generation_number must be positive")
    return float(total_alpha) / (generation_number * (generation_number + 1))
