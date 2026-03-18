"""
Report generation module for energy measurement comparisons.

Produces a concise, GitHub PR-ready Markdown report comparing
energy consumption between two code variants (with / without a code smell).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

from .statistical_analysis import (
    ALPHA,
    METRICS,
    cohens_d,
    effect_size_label,
    remove_outliers_zscore,
    welch_ttest,
)


def _fmt_pvalue(p: float) -> str:
    """Format a p-value: scientific notation when < 0.001, else 4 decimals."""
    if p < 0.001:
        return f"{p:.2e}"
    return f"{p:.4f}"


def generate_pr_report(
    df_with: pd.DataFrame,
    df_without: pd.DataFrame,
    profiler: str,
    data_type: str,
) -> str:
    """
    Generate a concise Markdown report suitable for a GitHub PR description.

    The report compares energy consumption between code with and without a
    code smell to justify whether removing the smell has a measurable
    energy impact.

    Inputs
    ------
        df_with: DataFrame of measurements *with* the code smell.
        df_without: DataFrame of measurements *without* the code smell.
        profiler: Profiler name (e.g. "mac-silicon", "carbon").
        data_type: "cleaned" or "raw".

    Returns
    -------
        A Markdown-formatted string.
    """
    lines: list[str] = []
    significant_rows: list[str] = []
    verdicts: list[str] = []

    for metric in METRICS:
        if metric not in df_with.columns or metric not in df_without.columns:
            continue

        vals_with = remove_outliers_zscore(df_with[metric].dropna().tolist())
        vals_without = remove_outliers_zscore(df_without[metric].dropna().tolist())

        if len(vals_with) < 2 or len(vals_without) < 2:
            continue

        arr_with, arr_without = np.array(vals_with), np.array(vals_without)
        mean_with = float(np.mean(arr_with))
        mean_without = float(np.mean(arr_without))

        delta = (
            (mean_with - mean_without) / mean_with * 100
            if mean_with != 0
            else float("nan")
        )

        _, p_val, significant = welch_ttest(vals_with, vals_without)
        d = cohens_d(vals_with, vals_without)
        effect = effect_size_label(d)

        display_metric = (
            "co2_eq" if (profiler == "carbon" and metric == "ane_mj") else metric
        )

        if not significant:
            continue

        delta_str = f"{delta:+.2f}%" if not np.isnan(delta) else "N/A"

        significant_rows.append(
            f"| `{display_metric}` | {delta_str} | {_fmt_pvalue(p_val)} "
            f"| {d:+.3f} | {effect} | \u2705 |"
        )

        if abs(d) >= 0.2:
            direction = "lower" if mean_without < mean_with else "higher"
            metric_type = "time" if metric == "time_s" else "energy"
            verdicts.append(
                f"- **`{display_metric}`**: {abs(delta):.1f}% {direction} {metric_type} "
                f"(Cohen\u2019s d\u2009=\u2009{d:+.3f}, {effect})"
            )

    # ── Title & context ───────────────────────────────────
    lines.append(f"## Energy Report \u2014 `{profiler}` ({data_type})\n")
    lines.append(
        f"> {len(df_with)} samples (with smell) vs "
        f"{len(df_without)} samples (without smell) \u2014 "
        f"\u03b1\u2009=\u2009{ALPHA}\n"
    )

    # ── Totals ──────────────────────────────────────────────
    energy_cols = ["cpu_mj", "gpu_mj", "dram_mj"]
    if profiler == "mac":
        energy_cols.append("ane_mj")

    total_j_with = 0.0
    total_j_without = 0.0

    for col in energy_cols:
        if col in df_with.columns:
            total_j_with += (
                sum(remove_outliers_zscore(df_with[col].dropna().tolist())) / 1000
            )
        if col in df_without.columns:
            total_j_without += (
                sum(remove_outliers_zscore(df_without[col].dropna().tolist())) / 1000
            )

    if total_j_with > 0 and total_j_without > 0:
        lines.append("### Global Consumption\n")
        lines.append("|  | With smell | Without smell |")
        lines.append("|---|---:|---:|")

        total_s_with = (
            sum(remove_outliers_zscore(df_with["time_s"].dropna().tolist()))
            if "time_s" in df_with.columns
            else 0
        )
        total_s_without = (
            sum(remove_outliers_zscore(df_without["time_s"].dropna().tolist()))
            if "time_s" in df_without.columns
            else 0
        )

        n_with = len(df_with)
        n_without = len(df_without)

        if total_s_with > 0 and total_s_without > 0:
            avg_s_with = total_s_with / n_with
            avg_s_without = total_s_without / n_without
            lines.append(
                f"| **Execution Time** | ~{avg_s_with:.3f} s | ~{avg_s_without:.3f} s |"
            )

            avg_w_with = total_j_with / total_s_with
            avg_w_without = total_j_without / total_s_without
            lines.append(
                f"| **Average Power** | {avg_w_with:.3f} W | {avg_w_without:.3f} W |"
            )

        lines.append(
            f"| **Total Energy** | {total_j_with:.2f} J | {total_j_without:.2f} J |"
        )

        lines.append("\n")

    lines.append("### Statistical Analysis\n")

    # ── Table (only if there are significant results) ─────
    if significant_rows:
        lines.append(
            "| Metric | \u0394 mean | p-value | Cohen\u2019s d | Effect | Sig. |"
        )
        lines.append("|---|---|---|---|---|---|")
        lines.extend(significant_rows)
        lines.append("")
    else:
        lines.append(
            "No statistically significant differences were found between the two variants.\n"
        )

    # ── Verdict ───────────────────────────────────────────
    lines.append("### Verdict\n")
    if verdicts:
        lines.append("Removing the code smell leads to measurable energy differences:")
        lines.append("")
        lines.extend(verdicts)
        lines.append("")
        lines.append(
            "> \u0394 mean = (mean\\_with \u2212 mean\\_without) / mean\\_with \u00d7 100. "
            "Positive \u2192 the smell consumes more energy."
        )
    else:
        lines.append(
            "The code smell does not measurably impact energy consumption "
            "under the tested conditions."
        )

    lines.append("")
    return "\n".join(lines)
