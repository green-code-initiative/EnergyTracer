from collections import defaultdict
from pathlib import Path

from alive_progress import alive_bar
import pandas as pd

from src.utilities.parser import parse_arguments

from .analysis.statistical_analysis import generate_pr_report
from .utilities import log

ANALYSIS_DIR = Path("results")


def main(args):
    """
    Entry point for the analyzer.

    Input:
        args: Namespace object from argparse containing:
            - path (str): path to the directory containing output CSV files.
            - verbose (bool): whether to display progress and debug information.

    Output:
        None. Side effects: creates the results directory and triggers the
        full analysis pipeline.
    """
    if args.verbose:
        log.header("EnergyTracer Analyzer Configuration")
        log.dim(f"Input directory: {args.path}")

    Path(ANALYSIS_DIR).mkdir(exist_ok=True)

    process_csv_files(Path(args.path), verbose=args.verbose)


def process_csv_files(input_dir: Path, verbose: bool = False) -> None:
    """
    Scan a directory for CSV files, classify them by profiler / data type /
    smell type, merge them, and generate the statistical reports.

    Input:
        input_dir (Path): root directory to search recursively for *.csv files.
            Each file is expected to live under a path containing:
              - an "output/<profiler>/" segment to identify the profiler,
              - a "cleaned" or "raw" segment to identify the data type,
              - "with_smell" or "without_smell" in the filename stem.
        verbose (bool): whether to display progress bars and log messages.
            Defaults to False.

    Output:
        None. Side effects: writes merged CSV files and Markdown reports under
        the results/ directory.

    Note:
        Files that do not match the expected path structure or naming convention
        are skipped with a warning.
    """
    all_csv_files = list(input_dir.rglob("*.csv"))

    if not all_csv_files:
        log.warn(f"No CSV files found under '{input_dir}' — nothing to process.")
        return

    csv_files_by_group = classify_csv_files_by_group(all_csv_files)

    if not csv_files_by_group:
        log.warn(
            "No CSV files matched the expected directory structure — nothing to merge."
        )
        return

    merged_file_paths = merge_and_save_csv_groups(
        all_csv_files, csv_files_by_group, verbose=verbose
    )

    generate_statistical_reports(merged_file_paths, verbose=verbose)


def classify_csv_files_by_group(all_csv_files: list[Path]) -> dict[tuple, list]:
    """
    Classify a flat list of CSV files into groups keyed by
    (profiler, data_type, smell_type).

    Input:
        all_csv_files (list[Path]): list of CSV file paths to classify.
            Each path is expected to contain:
              - an "output/<profiler>/" segment to identify the profiler,
              - a "cleaned" or "raw" segment to identify the data type,
              - "with_smell" or "without_smell" in the filename stem.

    Output:
        dict[tuple, list]: mapping from
        (profiler: str, data_type: str, smell_type: str) to the list of
        Path objects that belong to that group.

    Note:
        Files that do not match the expected structure are skipped with a
        warning and excluded from the returned dict.
    """
    csv_files_by_group: dict[tuple, list] = defaultdict(list)
    for csv_file in all_csv_files:
        parts = csv_file.parts
        try:
            profiler = parts[parts.index("output") + 1]
        except ValueError:
            log.warn(f"Skipping {csv_file}: could not determine profiler.")
            continue

        if "cleaned" in parts:
            data_type = "cleaned"
        elif "raw" in parts:
            data_type = "raw"
        else:
            log.warn(f"Skipping {csv_file}: could not determine data type.")
            continue

        filename_stem = csv_file.stem
        if "without_smell" in filename_stem:
            smell_type = "without_smell"
        elif "with_smell" in filename_stem:
            smell_type = "with_smell"
        else:
            log.warn(f"Skipping {csv_file}: unrecognised filename '{filename_stem}'.")
            continue

        csv_files_by_group[(profiler, data_type, smell_type)].append(csv_file)

    return csv_files_by_group


def merge_and_save_csv_groups(
    all_csv_files: list[Path],
    csv_files_by_group: dict[tuple, list],
    verbose: bool = False,
) -> dict[tuple, Path]:
    """
    Read and concatenate CSV files for each (profiler, data_type, smell_type)
    group, then write the merged result to disk.

    Input:
        all_csv_files (list[Path]): flat list of every CSV file discovered,
            used solely to size the progress bar.
        csv_files_by_group (dict[tuple, list]): mapping from
            (profiler, data_type, smell_type) to the list of CSV files
            belonging to that group.
        verbose (bool): whether to show a progress bar. Defaults to False.

    Output:
        dict[tuple, Path]: mapping from (profiler, data_type, smell_type) to
            the path of the merged CSV file written under
            results/<data_type>/<profiler>/<smell_type>.csv.

    Note:
        The progress bar tracks both the individual file reads and the final
        write per group (total = len(all_csv_files) + len(csv_files_by_group)).
    """
    merged_file_paths: dict[tuple, Path] = {}
    total_steps = len(all_csv_files) + len(csv_files_by_group)
    with alive_bar(total_steps, disable=not verbose) as bar:
        dataframes_by_group: dict[tuple, list[pd.DataFrame]] = defaultdict(list)
        for group_key, files in csv_files_by_group.items():
            for csv_file in files:
                dataframes_by_group[group_key].append(pd.read_csv(csv_file))
                bar()

        for (
            profiler,
            data_type,
            smell_type,
        ), dataframes in dataframes_by_group.items():
            merged_output_path = (
                ANALYSIS_DIR / data_type / profiler / f"{smell_type}.csv"
            )
            merged_output_path.parent.mkdir(parents=True, exist_ok=True)
            pd.concat(dataframes, ignore_index=True).to_csv(
                merged_output_path, index=False
            )
            merged_file_paths[(profiler, data_type, smell_type)] = merged_output_path
            bar()

    return merged_file_paths


def generate_statistical_reports(
    merged_file_paths: dict[tuple, Path], verbose: bool = False
) -> None:
    """
    Generate a Percentage-Reduction (PR) Markdown report for every
    (profiler, data_type) pair that has both smell variants available.

    Input:
        merged_file_paths (dict[tuple, Path]): mapping from
            (profiler, data_type, smell_type) to the merged CSV path, as
            returned by merge_and_save_csv_groups().
        verbose (bool): whether to log the path of each saved report.
            Defaults to False.

    Output:
        None. Side effects: writes one Markdown report per
        (profiler, data_type) pair to
        results/<data_type>/<profiler>/<profiler>_report.md.

    Note:
        Pairs where one of the two smell variants (with_smell / without_smell)
        is absent are skipped with a warning.
    """
    for profiler, data_type in {(key[0], key[1]) for key in merged_file_paths}:
        with_smell_key = (profiler, data_type, "with_smell")
        without_smell_key = (profiler, data_type, "without_smell")
        if (
            with_smell_key not in merged_file_paths
            or without_smell_key not in merged_file_paths
        ):
            log.warn(
                f"[{profiler}][{data_type}] missing one variant — skipping report."
            )
            continue

        df_with_smell = pd.read_csv(merged_file_paths[with_smell_key])
        df_without_smell = pd.read_csv(merged_file_paths[without_smell_key])

        if df_with_smell.empty or df_without_smell.empty:
            log.warn(
                f"[{profiler}][{data_type}] one or both CSVs are empty — skipping report."
            )
            continue

        report_content = generate_pr_report(
            df_with_smell, df_without_smell, profiler, data_type
        )
        report_file = ANALYSIS_DIR / data_type / profiler / f"{profiler}_report.md"
        report_file.write_text(report_content)
        if verbose:
            log.ok(f"PR report saved → {report_file}")


def cli():
    """
    Command-line entry point for the analyzer.

    Input:
        None. Reads arguments from sys.argv via parse_arguments().

    Output:
        None. Exits early with an error log if the specified input directory
        does not exist; otherwise delegates to main().
    """
    args = parse_arguments(origin="analyzer")

    if not Path(args.path).exists():
        log.error(f"Directory '{args.path}' does not exist.")
        return

    main(args)


if __name__ == "__main__":
    cli()
