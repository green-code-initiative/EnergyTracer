from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .utilities.metrics_extractors import extract_metrics
from .utilities.padding import pad

FIGURE_SIZE = (10, 6)
FIGURE_DPI = 300
LEGEND_FONTSIZE = "small"
PLOTS_SUBDIR = "plots"


def compare_histories(
    history1, history2, profiler: str = "carbon", directory: str = "output"
):
    """
    Creates pandas diagrams to compare the energy metrics collected from two different code executions.

    Inputs
    -------
        history1: list of dicts containing energy metrics for the first code execution (with code smell).
        history2: list of dicts containing energy metrics for the second code execution (without code smell).
        profiler: "mac-silicon" for zeus_apple_silicon (ANE metric), "carbon" for CodeCarbon (CO2 metric).
        directory: Directory where the generated plots will be saved.

    Notes
    -----
        Generates line plots for CPU, GPU, ANE/CO2, and DRAM energy consumption per iteration for both code
        versions, allowing for a visual comparison of their energy profiles.
    """
    ane_label = "ANE" if profiler == "mac-silicon" else "CO2"
    ane_unit = "mJ" if profiler == "mac-silicon" else "g CO2eq"

    df = prepare_dataframe(history1, history2, ane_label)

    output_dir = Path(directory) / PLOTS_SUBDIR
    output_dir.mkdir(parents=True, exist_ok=True)

    comparaison_directory = output_dir / "comparisons"
    comparaison_directory.mkdir(parents=True, exist_ok=True)

    moustache_directory = output_dir / "moustaches"
    moustache_directory.mkdir(parents=True, exist_ok=True)

    violin_directory = output_dir / "violins"
    violin_directory.mkdir(parents=True, exist_ok=True)

    plot_all_metrics(
        df, comparaison_directory / "all_energy_comparison.png", ane_label=ane_label
    )

    for metric in ["cpu", "gpu", "dram", ane_label.lower()]:
        plot_specific_metrics(
            df,
            metric,
            comparaison_directory / f"{metric}_energy_comparison.png",
            unit=ane_unit if metric == ane_label.lower() else "mJ",
        )

        plot_moustache(
            df,
            metric,
            moustache_directory / f"{metric}_moustache.png",
            unit=ane_unit if metric == ane_label.lower() else "mJ",
        )

        plot_violin(
            df,
            metric,
            violin_directory / f"{metric}_violin.png",
            unit=ane_unit if metric == ane_label.lower() else "mJ",
        )


def prepare_dataframe(history1, history2, ane_label: str):
    """
    Prepares a pandas DataFrame from the energy metrics collected in two different code executions.

    Inputs
    -------
        history1: list of dicts containing energy metrics for the first code execution (with code smell).
        history2: list of dicts containing energy metrics for the second code execution (without code smell).
        ane_label: Label for the ANE/CO2 metric depending on the profiler used ("ANE" for mac-silicon, "CO2" for carbon).

    Returns
    -------
        A pandas DataFrame structured for plotting, with columns for each energy metric and code version, and rows corresponding to iterations.
    """
    cpu_metrics1, gpu_metrics1, ane_metrics1, dram_metrics1 = extract_metrics(history1)
    cpu_metrics2, gpu_metrics2, ane_metrics2, dram_metrics2 = extract_metrics(history2)

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
        }
    )

    return df


def plot_all_metrics(df: pd.DataFrame, filename: str, ane_label: str = "ANE"):
    """
    Generates a line plot comparing CPU, GPU, ANE/CO2, and DRAM energy consumption per iteration for both code versions.

    Inputs
    -------
        df: DataFrame containing energy metrics for both code versions, with columns for each metric and code version.
        filename: Path where the generated plot will be saved.
        ane_label: Label for the ANE/CO2 metric depending on the profiler used ("ANE" for mac-silicon, "CO2" for carbon).

    Notes
    -----
        Creates a comprehensive line plot that allows for a visual comparison of the energy profiles of the two code versions across all collected metrics.
    """
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
    df: pd.DataFrame, metric: str, filename: str, unit: str = "mJ"
):
    """
    Generates a line plot comparing a specific energy metric (CPU, GPU, ANE/CO2, or DRAM) per iteration for both code versions.

    Inputs
    -------
        df: DataFrame containing energy metrics for both code versions, with columns for each metric and code version.
        metric: The specific metric to plot ("cpu", "gpu", "dram", or "ane"/"co2" depending on the profiler).
        filename: Path where the generated plot will be saved.
        unit: Unit of the metric for labeling the y-axis (default is "mJ", but can be "g CO2eq" for the CO2 metric when using the carbon profiler).

    Notes
    -----
        Creates a line plot that allows for a visual comparison of the specified energy metric between the two code versions across iterations, including average lines for each version.
    """
    plt.figure(figsize=FIGURE_SIZE)

    for variant in ["with code smell", "without code smell"]:
        col = f"{metric.upper()} {variant}"
        avg = df[col].mean()
        (line,) = plt.plot(
            df["Iteration"], df[col], label=f"{metric.upper()} {variant}"
        )
        plt.axhline(
            y=avg,
            color=line.get_color(),
            linestyle="--",
            alpha=0.5,
            label=f"Avg {variant}: {avg:.3f} {unit} / iteration",
        )

    plt.xlabel("Iteration")
    plt.ylabel(f"{metric.upper()} ({unit})")
    plt.title(f"{metric.upper()} Consumption Comparison")
    plt.legend(fontsize=LEGEND_FONTSIZE)
    plt.grid(True)
    plt.savefig(filename, dpi=FIGURE_DPI)
    plt.close()


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
    plt.figure(figsize=FIGURE_SIZE)

    data_with_smell = df[f"{metric.upper()} with code smell"].dropna()
    data_without_smell = df[f"{metric.upper()} without code smell"].dropna()

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
    data_with_smell = df[f"{metric.upper()} with code smell"].dropna()
    data_without_smell = df[f"{metric.upper()} without code smell"].dropna()

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
