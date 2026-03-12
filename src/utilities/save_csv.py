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
        The CSV file will have the following columns: i, cpu_mj, gpu_mj, ane_mj, dram_mj.

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
            f, fieldnames=["i", "cpu_mj", "gpu_mj", "ane_mj", "dram_mj"]
        )
        writer.writeheader()
        writer.writerows(history)
