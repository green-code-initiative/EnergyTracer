"""Tests for the generate_report module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis.generate_report import _fmt_pvalue, generate_pr_report

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_df(cpu, gpu=None, ane=None, dram=None):
    """Build a DataFrame with the standard metric columns."""
    n = len(cpu)
    return pd.DataFrame(
        {
            "cpu_mj": cpu,
            "gpu_mj": gpu if gpu is not None else [0.0] * n,
            "ane_mj": ane if ane is not None else [0.0] * n,
            "dram_mj": dram if dram is not None else [0.0] * n,
        }
    )


# ──────────────────────────────────────────────────────────────────────────────
# _fmt_pvalue
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestFmtPvalue:
    def test_large_pvalue(self):
        assert _fmt_pvalue(0.05) == "0.0500"

    def test_small_pvalue(self):
        assert _fmt_pvalue(0.0001) == "1.00e-04"

    def test_zero(self):
        assert _fmt_pvalue(0.0) == "0.00e+00"

    def test_boundary(self):
        # Exactly 0.001 → not < 0.001, so 4 decimals
        assert _fmt_pvalue(0.001) == "0.0010"


# ──────────────────────────────────────────────────────────────────────────────
# generate_pr_report — structure & content
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestGeneratePrReport:
    def test_report_contains_title_and_context(self):
        rng = np.random.default_rng(0)
        df_with = _make_df(rng.normal(10, 1, 30).tolist())
        df_without = _make_df(rng.normal(10, 1, 30).tolist())

        report = generate_pr_report(df_with, df_without, "mac-silicon", "cleaned")

        assert "## Energy Report" in report
        assert "`mac-silicon`" in report
        assert "cleaned" in report
        assert "30 samples (with smell)" in report
        assert "30 samples (without smell)" in report
        assert "### Verdict" in report

    def test_significant_difference_produces_table(self):
        """When means differ significantly, the report should contain a table."""
        rng = np.random.default_rng(42)
        df_with = _make_df(rng.normal(100, 2, 50).tolist())
        df_without = _make_df(rng.normal(50, 2, 50).tolist())

        report = generate_pr_report(df_with, df_without, "mac-silicon", "cleaned")

        # Table header must be present
        assert "| Metric |" in report
        assert "`cpu_mj`" in report
        assert "✅" in report
        # Must have a verdict about measurable differences
        assert "measurable energy differences" in report

    def test_no_significant_difference_no_table(self):
        """When there's no significant difference, no table should appear."""
        rng = np.random.default_rng(7)
        # Same distribution → no significant difference
        values = rng.normal(50, 5, 30).tolist()
        df_with = _make_df(values)
        df_without = _make_df(values)

        report = generate_pr_report(df_with, df_without, "mac-silicon", "cleaned")

        assert "| Metric |" not in report
        assert "No statistically significant differences" in report
        assert "does not measurably impact" in report

    def test_carbon_profiler_renames_ane_to_co2_eq(self):
        """For the 'carbon' profiler, ane_mj should be displayed as co2_eq."""
        rng = np.random.default_rng(1)
        df_with = _make_df(
            rng.normal(100, 2, 50).tolist(), ane=rng.normal(5, 0.5, 50).tolist()
        )
        df_without = _make_df(
            rng.normal(50, 2, 50).tolist(), ane=rng.normal(2, 0.5, 50).tolist()
        )

        report = generate_pr_report(df_with, df_without, "carbon", "cleaned")

        assert "`co2_eq`" in report
        # ane_mj should NOT appear as a metric name
        assert "`ane_mj`" not in report

    def test_delta_formula_note_present_when_significant(self):
        rng = np.random.default_rng(42)
        df_with = _make_df(rng.normal(100, 2, 50).tolist())
        df_without = _make_df(rng.normal(50, 2, 50).tolist())

        report = generate_pr_report(df_with, df_without, "mac-silicon", "cleaned")

        assert "Δ mean" in report
        assert "Positive" in report

    def test_report_is_string(self):
        df = _make_df([1.0, 2.0, 3.0])
        report = generate_pr_report(df, df, "mac-silicon", "raw")
        assert isinstance(report, str)

    def test_missing_metric_columns_handled(self):
        """If DataFrames are missing some metric columns, no crash."""
        df_with = pd.DataFrame({"cpu_mj": [1.0, 2.0, 3.0]})
        df_without = pd.DataFrame({"cpu_mj": [1.0, 2.0, 3.0]})

        report = generate_pr_report(df_with, df_without, "mac-silicon", "cleaned")

        assert "## Energy Report" in report

    def test_too_few_samples_skips_metric(self):
        """Metrics with fewer than 2 values after cleaning are skipped."""
        df_with = _make_df([5.0])
        df_without = _make_df([5.0])

        report = generate_pr_report(df_with, df_without, "mac-silicon", "cleaned")

        # Should still generate a valid report with no table
        assert "## Energy Report" in report
        assert "### Verdict" in report
