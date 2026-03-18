import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.utilities import log

from .utilities.metrics_extractors import extract_metrics
from .utilities.padding import pad

FIGURE_SIZE = (10, 6)
FIGURE_DPI = 300
LEGEND_FONTSIZE = "small"
PLOTS_SUBDIR = "plots"


def get_metric_unit(metric: str, profiler: str, ane_label: str) -> str:
    """
    Returns the appropriate unit for a given metric based on profiler type.
    """
    metric_lower = metric.lower()
    # Determine which metric label should be treated as CO2-equivalent.
    # Fall back to the original hard-coded "co2" if ane_label is empty.
    co2_metric = ane_label.lower() if ane_label else "co2"

    if metric_lower == "time":
        return "s"
    if metric_lower == co2_metric and profiler == "carbon":
        return "g CO2eq"
    return "mJ"


def setup_plotting_directories(output_dir: Path) -> dict:
    """
    Creates all required subdirectories for plot outputs.
    Returns a dictionary with paths to each subdirectory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    dirs = {
        "comparisons": output_dir / "comparisons",
        "time": output_dir / "time",
        "moustaches": output_dir / "moustaches",
        "violins": output_dir / "violins",
    }

    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dirs


def plot_metric_comparisons(
    df: pd.DataFrame, dirs: dict, metrics: list, ane_label: str, profiler: str
) -> None:
    """
    Generates comparison plots for each metric across iterations and over time.
    """
    for metric in metrics:
        unit = get_metric_unit(metric, profiler, ane_label)

        plot_specific_metrics(
            df,
            metric,
            dirs["comparisons"] / f"{metric}_energy_comparison.png",
            unit=unit,
        )
        if metric.lower() != "time":
            plot_specific_metrics(
                df,
                metric,
                dirs["time"] / f"{metric}_energy_over_time.png",
                unit=unit,
                x_axis="time",
            )

    plot_specific_metrics(
        df,
        "total power",
        dirs["time"] / "total_power_over_time.png",
        unit="W",
        x_axis="time",
    )


def plot_metric_distributions(
    df: pd.DataFrame, dirs: dict, metrics: list, ane_label: str, profiler: str
) -> None:
    """
    Generates distribution plots (box and violin plots) for each metric.
    """
    for metric in metrics:
        unit = get_metric_unit(metric, profiler, ane_label)

        plot_moustache(
            df,
            metric,
            dirs["moustaches"] / f"{metric}_moustache.png",
            unit=unit,
        )

        plot_violin(
            df,
            metric,
            dirs["violins"] / f"{metric}_violin.png",
            unit=unit,
        )


def compare_histories(
    history1, history2, profiler: str = "carbon", directory: str = "output"
):
    """
    Creates pandas diagrams to compare the energy metrics collected from two different code executions.

    Inputs
    -------
        history1: list of dicts containing energy metrics for the first code execution (with code smell).
        history2: list of dicts containing energy metrics for the second code execution (without code smell).
        profiler: "mac" for zeus_apple_silicon (ANE metric), "carbon" for CodeCarbon (CO2 metric).
        directory: Directory where the generated plots will be saved.

    Notes
    -----
        Generates line plots for CPU, GPU, ANE/CO2, and DRAM energy consumption per iteration for both code
        versions, allowing for a visual comparison of their energy profiles.
    """
    if not history1 and not history2:
        log.warn("Both histories are empty — skipping all plots.")
        return

    ane_label = "ANE" if profiler == "mac" else "CO2"
    df = prepare_dataframe(history1, history2, ane_label)

    if df.empty:
        log.warn("Prepared DataFrame is empty — skipping all plots.")
        return

    output_dir = Path(directory) / PLOTS_SUBDIR
    dirs = setup_plotting_directories(output_dir)

    plot_all_metrics(
        df, dirs["comparisons"] / "all_energy_comparison.png", ane_label=ane_label
    )

    metrics = ["cpu", "gpu", "dram", ane_label.lower(), "time"]

    plot_metric_comparisons(df, dirs, metrics, ane_label, profiler)
    plot_metric_distributions(df, dirs, metrics, ane_label, profiler)


def prepare_dataframe(history1, history2, ane_label: str):
    """
    Prepares a pandas DataFrame from the energy metrics collected in two different code executions.

    Inputs
    -------
        history1: list of dicts containing energy metrics for the first code execution (with code smell).
        history2: list of dicts containing energy metrics for the second code execution (without code smell).
        ane_label: Label for the ANE/CO2 metric depending on the profiler used ("ANE" for mac, "CO2" for carbon).

    Returns
    -------
        A pandas DataFrame structured for plotting, with columns for each energy metric and code version, and rows corresponding to iterations.
    """
    cpu_metrics1, gpu_metrics1, ane_metrics1, dram_metrics1, time_metrics1 = (
        extract_metrics(history1)
    )
    cpu_metrics2, gpu_metrics2, ane_metrics2, dram_metrics2, time_metrics2 = (
        extract_metrics(history2)
    )

    max_len = max(len(history1), len(history2))
    iterations = list(range(max_len))

    df = pd.DataFrame(
        {
            "Iteration": iterations,
            "CPU with code smell": pad(cpu_metrics1, max_len),
            "CPU without code smell": pad(cpu_metrics2, max_len),
            "GPU with code smell": pad(gpu_metrics1, max_len),
            "GPU without code smell": pad(gpu_metrics2, max_len),
            f"{ane_label} with code smell": pad(ane_metrics1, max_len),
            f"{ane_label} without code smell": pad(ane_metrics2, max_len),
            "DRAM with code smell": pad(dram_metrics1, max_len),
            "DRAM without code smell": pad(dram_metrics2, max_len),
            "Time with code smell": pad(time_metrics1, max_len),
            "Time without code smell": pad(time_metrics2, max_len),
        }
    )

    df["Cumulative Time with code smell"] = cumulative_time_series(
        df["Time with code smell"]
    )
    df["Cumulative Time without code smell"] = cumulative_time_series(
        df["Time without code smell"]
    )

    total_energy_with = (
        df["CPU with code smell"]
        + df["GPU with code smell"]
        + df["DRAM with code smell"]
    )
    total_energy_without = (
        df["CPU without code smell"]
        + df["GPU without code smell"]
        + df["DRAM without code smell"]
    )

    if ane_label == "ANE":
        total_energy_with = total_energy_with + df["ANE with code smell"]
        total_energy_without = total_energy_without + df["ANE without code smell"]

    # mJ -> J (divide by 1000), then J / s -> W.
    df["TOTAL POWER with code smell"] = (total_energy_with / 1000).div(
        df["Time with code smell"].where(df["Time with code smell"] > 0)
    )
    df["TOTAL POWER without code smell"] = (total_energy_without / 1000).div(
        df["Time without code smell"].where(df["Time without code smell"] > 0)
    )

    return df


def cumulative_time_series(series: pd.Series) -> pd.Series:
    cumulative = series.fillna(0).cumsum()
    return cumulative.where(series.notna())


def plot_all_metrics(df: pd.DataFrame, filename: str, ane_label: str = "ANE"):
    """
    Generates a line plot comparing CPU, GPU, ANE/CO2, and DRAM energy consumption per iteration for both code versions.

    Inputs
    -------
        df: DataFrame containing energy metrics for both code versions, with columns for each metric and code version.
        filename: Path where the generated plot will be saved.
        ane_label: Label for the ANE/CO2 metric depending on the profiler used ("ANE" for mac, "CO2" for carbon).

    Notes
    -----
        Creates a comprehensive line plot that allows for a visual comparison of the energy profiles of the two code versions across all collected metrics.
    """
    if df.empty:
        log.warn("DataFrame is empty - skipping combined metrics plot.")
        return

    plt.figure(figsize=FIGURE_SIZE)
    plt.plot(df["Iteration"], df["CPU with code smell"], label="CPU with code smell")
    plt.plot(
        df["Iteration"], df["CPU without code smell"], label="CPU without code smell"
    )

    plt.plot(df["Iteration"], df["GPU with code smell"], label="GPU with code smell")
    plt.plot(
        df["Iteration"], df["GPU without code smell"], label="GPU without code smell"
    )

    plt.plot(
        df["Iteration"],
        df[f"{ane_label} with code smell"],
        label=f"{ane_label} with code smell",
    )
    plt.plot(
        df["Iteration"],
        df[f"{ane_label} without code smell"],
        label=f"{ane_label} without code smell",
    )

    plt.plot(df["Iteration"], df["DRAM with code smell"], label="DRAM with code smell")
    plt.plot(
        df["Iteration"], df["DRAM without code smell"], label="DRAM without code smell"
    )

    plt.xlabel("Iteration")
    plt.ylabel("Energy (mJ)")
    plt.title("Energy Consumption Comparison")
    plt.legend(fontsize=LEGEND_FONTSIZE)
    plt.grid(True)
    plt.savefig(filename, dpi=FIGURE_DPI)
    plt.close()


def plot_specific_metrics(
    df: pd.DataFrame,
    metric: str,
    filename: str,
    unit: str = "mJ",
    x_axis: str = "iteration",
):
    """
    Generates a line plot comparing a specific energy metric (CPU, GPU, ANE/CO2, or DRAM) per iteration for both code versions.

    Inputs
    -------
        df: DataFrame containing energy metrics for both code versions, with columns for each metric and code version.
        metric: The specific metric to plot ("cpu", "gpu", "dram", or "ane"/"co2" depending on the profiler).
        filename: Path where the generated plot will be saved.
        unit: Unit of the metric for labeling the y-axis (default is "mJ", but can be "g CO2eq" for the CO2 metric when using the carbon profiler).
        x_axis: X-axis mode. Use "iteration" (default) to plot per iteration, or "time" to plot metric values over cumulative execution time.

    Notes
    -----
        Creates a line plot that allows for a visual comparison of the specified energy metric between the two code versions across iterations, including average lines for each version.
    """
    metric_label = "Time" if metric.lower() == "time" else metric.upper()
    col_with = f"{metric_label} with code smell"
    col_without = f"{metric_label} without code smell"

    if df[col_with].dropna().empty or df[col_without].dropna().empty:
        log.warn(f"Skipping line plot for '{metric}': one or both datasets are empty.")
        return

    x_axis_normalized = x_axis.lower()
    if x_axis_normalized not in {"iteration", "time"}:
        raise ValueError("x_axis must be either 'iteration' or 'time'")

    for variant in ["with code smell", "without code smell"]:
        x_col = (
            "Iteration"
            if x_axis_normalized == "iteration"
            else f"Cumulative Time {variant}"
        )
        if df[x_col].dropna().empty:
            log.warn(
                f"Skipping line plot for '{metric}': x-axis data is empty for '{variant}'."
            )
            return

    plt.figure(figsize=FIGURE_SIZE)

    for variant in ["with code smell", "without code smell"]:
        col = f"{metric_label} {variant}"
        x_col = (
            "Iteration"
            if x_axis_normalized == "iteration"
            else f"Cumulative Time {variant}"
        )

        avg = df[col].mean()
        (line,) = plt.plot(df[x_col], df[col], label=f"{metric_label} {variant}")

        is_scalable_metric = metric.lower() == "co2" or metric.lower() == "time"
        can_scale = (
            is_scalable_metric and avg is not None and math.isfinite(avg) and avg > 0
        )
        if can_scale:
            leading_zeros = count_leading_zeros(avg)
            scale_factor = 10**leading_zeros
            scale_suffix = f" x 10^{leading_zeros}"
        else:
            scale_factor = 1
            scale_suffix = ""
        per_label = " / iteration" if x_axis_normalized == "iteration" else ""
        label = (
            f"Avg {variant}: {avg * scale_factor:.3f} {scale_suffix}{unit}{per_label}"
        )

        if metric.lower() == "total power" and x_axis_normalized == "time":
            time_col_iteration = f"Time {variant}"
            if time_col_iteration in df:
                energy_j = (df[col] * df[time_col_iteration]).dropna().sum()
                label += f" | Total: {energy_j:.2f} J"

        plt.axhline(
            y=avg,
            color=line.get_color(),
            linestyle="--",
            alpha=0.5,
            label=label,
        )

    plt.xlabel("Iteration" if x_axis_normalized == "iteration" else "Time (s)")
    plt.ylabel(f"{metric_label} ({unit})")
    plt.title(
        f"{metric_label} Consumption Comparison"
        if x_axis_normalized == "iteration"
        else f"{metric_label} over Time"
    )
    plt.legend(fontsize=LEGEND_FONTSIZE)
    plt.grid(True)
    plt.savefig(filename, dpi=FIGURE_DPI)
    plt.close()


def count_leading_zeros(x: float) -> int:
    if x <= 0:
        raise ValueError("x doit être positif")
    return max(0, -math.floor(math.log10(x)) - 1)


def plot_moustache(df: pd.DataFrame, metric: str, filename: str, unit: str = "mJ"):
    """
    Generates a box plot (moustache plot) comparing the distribution of a specific energy metric (CPU, GPU, ANE/CO2, or DRAM) for both code versions.

    Inputs
    -------
        df: DataFrame containing energy metrics for both code versions, with columns for each metric and code version.
        metric: The specific metric to plot ("cpu", "gpu", "dram", or "ane"/"co2" depending on the profiler).
        filename: Path where the generated plot will be saved.
        unit: Unit of the metric for labeling the y-axis (default is "mJ", but can be "g CO2eq" for the CO2 metric when using the carbon profiler).

    Notes
    -----
        Creates a box plot that allows for a visual comparison of the distribution of the specified energy metric between the two code versions, showing medians, quartiles, and potential outliers in the data.
    """
    metric_label = "Time" if metric.lower() == "time" else metric.upper()
    col_with = f"{metric_label} with code smell"
    col_without = f"{metric_label} without code smell"

    data_with_smell = df[col_with].dropna()
    data_without_smell = df[col_without].dropna()

    if data_with_smell.empty or data_without_smell.empty:
        log.warn(
            f"Skipping moustache plot for '{metric}': one or both datasets are empty."
        )
        return

    plt.figure(figsize=FIGURE_SIZE)

    plt.boxplot(
        [data_with_smell, data_without_smell],
        tick_labels=["With code smell", "Without code smell"],
    )

    plt.ylabel(f"{metric.upper()} ({unit})")
    plt.title(f"{metric.upper()} Consumption Moustache Plot")
    plt.grid(True)
    plt.savefig(filename, dpi=FIGURE_DPI)
    plt.close()


def plot_violin(df: pd.DataFrame, metric: str, filename: str, unit: str = "mJ"):
    """
    Generates a violin plot comparing the distribution of a specific energy metric (CPU, GPU, ANE/CO2, or DRAM) for both code versions.

    Inputs
    -------
        df: DataFrame containing energy metrics for both code versions, with columns for each metric and code version.
        metric: The specific metric to plot ("cpu", "gpu", "dram", or "ane"/"co2" depending on the profiler).
        filename: Path where the generated plot will be saved.
        unit: Unit of the metric for labeling the y-axis (default is "mJ", but can be "g CO2eq" for the CO2 metric when using the carbon profiler).
    Author
    -----
        This function was generated by Claude Sonnet 4.6, with the plot_moustache function as a reference.
    """
    metric_label = "Time" if metric.lower() == "time" else metric.upper()
    col_with = f"{metric_label} with code smell"
    col_without = f"{metric_label} without code smell"

    data_with_smell = df[col_with].dropna()
    data_without_smell = df[col_without].dropna()

    if data_with_smell.empty or data_without_smell.empty:
        log.warn(
            f"Skipping violin plot for '{metric}': one or both datasets are empty."
        )
        return

    plt.figure(figsize=(10, 6))

    parts = plt.violinplot(
        [data_with_smell, data_without_smell],
        positions=[1, 2],
        showmeans=True,
        showmedians=True,
        showextrema=True,
    )

    for pc in parts["bodies"]:
        pc.set_facecolor("lightblue")
        pc.set_alpha(0.7)
        pc.set_edgecolor("black")
        pc.set_linewidth(1)

    plt.xticks([1, 2], ["With code smell", "Without code smell"])
    plt.ylabel(f"{metric.upper()} ({unit})")
    plt.title(f"Distribution {metric.upper()} Consumption")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()
