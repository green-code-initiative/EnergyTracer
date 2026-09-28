"""
Report generation module for energy measurement comparisons.

Produces a concise, GitHub PR-ready report comparing
energy consumption between two code variants (with / without a code smell).
The output format depends on the DocWriter implementation provided.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .utils.doc_writer import DocWriter
from .utils.get_hardware_details import get_hardware_details

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
    doc_writer: DocWriter,
    df_with: pd.DataFrame,
    df_without: pd.DataFrame,
    profiler: str,
    data_type: str,
    verbose: bool = False,
) -> str:
    """
    Generate a concise report suitable for a GitHub PR description.

    The report compares energy consumption between code with and without a
    code smell to justify whether removing the smell has a measurable
    energy impact. The output format depends on the DocWriter implementation.

    Inputs
    ------
        doc_writer: A DocWriter implementation controlling the output format.
        df_with: DataFrame of measurements *with* the code smell.
        df_without: DataFrame of measurements *without* the code smell.
        profiler: Profiler name (e.g. "mac-silicon", "carbon").
        data_type: "cleaned" or "raw".
        verbose: Whether to log additional details.

    Returns
    -------
        A formatted string produced by the writer.
    """
    significant_rows: list[list[str]] = []
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
            [
                doc_writer.get_inline_code(display_metric),
                delta_str,
                _fmt_pvalue(p_val),
                f"{d:+.3f}",
                effect,
                "\u2705",
            ]
        )

        if abs(d) >= 0.2:
            direction = "lower" if mean_without < mean_with else "higher"
            metric_type = "time" if metric == "time_s" else "energy"
            verdicts.append(
                f"{doc_writer.get_bold(doc_writer.get_inline_code(display_metric))}: "
                f"{abs(delta):.1f}% {direction} {metric_type} "
                f"(Cohen\u2019s d\u2009=\u2009{d:+.3f}, {effect})"
            )

    # ── Title & context ───────────────────────────────────
    doc_writer.add_h2(f"Energy Report \u2014 {doc_writer.get_inline_code(profiler)} ({data_type})")
    doc_writer.add_quote(
        f"{len(df_with)} samples (with smell) vs "
        f"{len(df_without)} samples (without smell) \u2014 "
        f"\u03b1\u2009=\u2009{ALPHA}"
    )

    # ── Instance info ─────────────────────────────────────
    doc_writer.add_h3("Instance Info")
    doc_writer.add_list(
        [
            f"{doc_writer.get_bold(key)}: {doc_writer.get_inline_code(value)}"
            for key, value in get_hardware_details().items()
        ]
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
        doc_writer.add_h3("Global Consumption")

        table_head = [["Metric", "With smell", "Without smell"]]
        table_rows: list[list[str]] = []

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
            avg_ms_with = total_s_with / n_with * 1000
            avg_ms_without = total_s_without / n_without * 1000
            table_rows.append(
                [doc_writer.get_bold("Execution Time"), f"{avg_ms_with:.2f} ms", f"{avg_ms_without:.2f} ms"]
            )

            avg_w_with = total_j_with / total_s_with
            avg_w_without = total_j_without / total_s_without
            table_rows.append(
                [doc_writer.get_bold("Average Power"), f"{avg_w_with:.3f} W", f"{avg_w_without:.3f} W"]
            )

        table_rows.append(
            [doc_writer.get_bold("Total Energy"), f"{total_j_with:.2f} J", f"{total_j_without:.2f} J"]
        )

        doc_writer.add_table(table_head, table_rows)

    doc_writer.add_newline()
    doc_writer.add_quote(
        "The total energy is the sum of measurements across all iterations, "
        "converted to joules (J). If you ran the ./run_experiment.sh script, "
        "this reflects the cumulative energy of all 30 iterations of the process."
    )

    doc_writer.add_h3("Statistical Analysis")

    # ── Table (only if there are significant results) ─────
    if significant_rows:
        stats_head = [["Metric", "\u0394 mean", "p-value", "Cohen\u2019s d", "Effect", "Sig."]]
        doc_writer.add_table(stats_head, significant_rows)
    else:
        doc_writer.add_paragraph(
            "No statistically significant differences were found between the two variants."
        )

    # ── Verdict ───────────────────────────────────────────
    doc_writer.add_h3("Verdict")
    if verdicts:
        doc_writer.add_paragraph("Removing the code smell leads to measurable energy differences:")
        doc_writer.add_list(verdicts)
        doc_writer.add_newline()
        doc_writer.add_quote(
            "\u0394 mean = (mean_with \u2212 mean_without) / mean_with \u00d7 100. "
            "Positive \u2192 the smell consumes more energy."
        )
    else:
        doc_writer.add_paragraph(
            "The code smell does not measurably impact energy consumption "
            "under the tested conditions."
        )

    return doc_writer.build()
