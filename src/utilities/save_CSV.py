import os, csv

def save_history(history: list, filename: str):
    '''
    Saves the energy profiling history to a CSV file.

    Inputs
    ------
        history: A list of dicts, where each dict contains energy metrics for an iteration.
        filename: The name of the CSV file to save the history to. The file will be saved in the "output/csv" directory.

    Notes
    -----
        The CSV file will have the following columns: i, cpu_mj, gpu_mj, ane_mj, dram_mj.

    Author
    ------
        Claude Sonnet 4.6
    '''
    output_dir = "output/csv"
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, filename)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["i", "cpu_mj", "gpu_mj", "ane_mj", "dram_mj"])
        writer.writeheader()
        writer.writerows(history)