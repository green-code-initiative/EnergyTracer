import os
import pandas as pd
import matplotlib.pyplot as plt

from plot.utilities.padding import pad
from plot.utilities.metrics_extractors import extract_metrics

def compare_histories(history1, history2, profiler: str = "carbon"):
    '''
    Creates pandas diagrams to compare the energy metrics collected from two different code executions.

    Inputs
    -------
        history1: list of dicts containing energy metrics for the first code execution (with code smell).
        history2: list of dicts containing energy metrics for the second code execution (without code smell).
        profiler: "mac-silicon" for zeus_apple_silicon (ANE metric), "carbon" for CodeCarbon (CO2 metric).

    Notes
    -----
        Generates line plots for CPU, GPU, ANE/CO2, and DRAM energy consumption per iteration for both code
        versions, allowing for a visual comparison of their energy profiles.
    '''
    # Label and unit for the ANE/CO2 metric depending on the profiler
    ane_label = "ANE" if profiler == "mac-silicon" else "CO2"
    ane_unit = "mJ" if profiler == "mac-silicon" else "g CO2eq"

    cpu_metrics1, gpu_metrics1, ane_metrics1, dram_metrics1 = extract_metrics(history1)
    cpu_metrics2, gpu_metrics2, ane_metrics2, dram_metrics2 = extract_metrics(history2)

    # Pad shorter list with NaN in case one run was interrupted early
    max_len = max(len(history1), len(history2))
    iterations = list(range(max_len))

    # Create a DataFrame for plotting
    df = pd.DataFrame({
        "Iteration": iterations,
        "CPU with code smell": pad(cpu_metrics1, max_len),
        "CPU without code smell": pad(cpu_metrics2, max_len),

        "GPU with code smell": pad(gpu_metrics1, max_len),
        "GPU without code smell": pad(gpu_metrics2, max_len),

        f"{ane_label} with code smell": pad(ane_metrics1, max_len),
        f"{ane_label} without code smell": pad(ane_metrics2, max_len),

        "DRAM with code smell": pad(dram_metrics1, max_len),
        "DRAM without code smell": pad(dram_metrics2, max_len),
    })

    # Create output directory if it doesn't exist
    output_dir = "output/plots"
    os.makedirs(output_dir, exist_ok=True)

    # Plotting
    plot_all_metrics(df, os.path.join(output_dir, "all_energy_comparison.png"), ane_label=ane_label)
    plot_specific_metrics(df, "cpu", os.path.join(output_dir, "cpu_energy_comparison.png"))
    plot_specific_metrics(df, "gpu", os.path.join(output_dir, "gpu_energy_comparison.png"))
    plot_specific_metrics(df, ane_label, os.path.join(output_dir, f"{ane_label.lower()}_energy_comparison.png"), unit=ane_unit)
    plot_specific_metrics(df, "dram", os.path.join(output_dir, "dram_energy_comparison.png"))

    
def plot_all_metrics(df: pd.DataFrame, filename: str, ane_label: str = "ANE"):
    plt.figure(figsize=(10, 6))
    plt.plot(df["Iteration"], df["CPU with code smell"], label="CPU with code smell")
    plt.plot(df["Iteration"], df["CPU without code smell"], label="CPU without code smell")

    plt.plot(df["Iteration"], df["GPU with code smell"], label="GPU with code smell")
    plt.plot(df["Iteration"], df["GPU without code smell"], label="GPU without code smell")

    plt.plot(df["Iteration"], df[f"{ane_label} with code smell"], label=f"{ane_label} with code smell")
    plt.plot(df["Iteration"], df[f"{ane_label} without code smell"], label=f"{ane_label} without code smell")

    plt.plot(df["Iteration"], df["DRAM with code smell"], label="DRAM with code smell")
    plt.plot(df["Iteration"], df["DRAM without code smell"], label="DRAM without code smell")

    plt.xlabel("Iteration")
    plt.ylabel("Energy (mJ)")
    plt.title("Energy Consumption Comparison")
    plt.legend(fontsize="small")
    plt.grid(True)
    plt.savefig(filename, dpi=300)
    plt.close()

def plot_specific_metrics(df: pd.DataFrame, metric: str, filename: str, unit: str = "mJ"):
    plt.figure(figsize=(10, 6))

    for variant in ["with code smell", "without code smell"]:
        col = f"{metric.upper()} {variant}"
        avg = df[col].mean()
        line, = plt.plot(df["Iteration"], df[col], label=f"{metric.upper()} {variant}")
        plt.axhline(y=avg, color=line.get_color(), linestyle="--", alpha=0.5, label=f"Avg {variant}: {avg:.3f} {unit} / iteration")

    plt.xlabel("Iteration")
    plt.ylabel(f"{metric.upper()} ({unit})")
    plt.title(f"{metric.upper()} Consumption Comparison")
    plt.legend(fontsize="small")
    plt.grid(True)
    plt.savefig(filename, dpi=300)
    plt.close()