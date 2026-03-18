import csv
from pathlib import Path


def save_history(history: list, filename: str, directory: str = "output"):
    """
    Saves the energy profiling history to a CSV file.

    Inputs
    ------
        history: A list of dicts, where each dict contains energy metrics for an iteration.
        filename: The name of the CSV file to save the history to. The file will be saved in the "{directory}/csv" directory.
        directory: The base directory where the "csv" subdirectory will be created if it doesn't exist. Default is "output".

    Notes
    -----
        The CSV file will have the following columns: i, cpu_mj, gpu_mj, ane_mj, dram_mj, time_s.
         - i: The iteration index (starting from 0).
         - cpu_mj: The energy consumed by the CPU in millijoules (mJ).
         - gpu_mj: The energy consumed by the GPU in millijoules (mJ).
         - ane_mj: The energy consumed by the Apple Neural Engine (ANE) in millijoules (mJ) or the CO2 equivalent emissions in milligrams (mg) for the Carbon profiler.
         - dram_mj: The energy consumed by the RAM in millijoules (mJ).
         - time_s: The wall-clock duration of the iteration in seconds (s).

    Author
    ------
        Claude Sonnet 4.6
    """
    if not history:
        return

    output_dir = Path(directory) / "csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / filename

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["i", "cpu_mj", "gpu_mj", "ane_mj", "dram_mj", "time_s"]
        )
        writer.writeheader()
        writer.writerows(history)
