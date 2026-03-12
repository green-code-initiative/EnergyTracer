from collections import defaultdict
from pathlib import Path

from alive_progress import alive_bar
import pandas as pd

from src.utilities.parser import parse_arguments

from .analysis.statistical_analysis import generate_pr_report
from .utilities import log

ANALYSIS_DIR = Path("results")


def main(args):
    if args.verbose:
        log.header("EnergyTracer Analyzer Configuration")
        log.dim(f"Input directory: {args.path}")

    Path(ANALYSIS_DIR).mkdir(exist_ok=True)

    process_csv_files(Path(args.path), verbose=args.verbose)


def process_csv_files(path: Path, verbose: bool = False) -> None:
    frames: dict[tuple, list] = defaultdict(list)
    csv_files = list(path.rglob("*.csv"))

    for csv_file in csv_files:
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

        stem = csv_file.stem
        if "without_smell" in stem:
            smell_type = "without_smell"
        elif "with_smell" in stem:
            smell_type = "with_smell"
        else:
            log.warn(f"Skipping {csv_file}: unrecognised filename '{stem}'.")
            continue

        frames[(profiler, data_type, smell_type)].append(csv_file)

    # Phase 1: read all CSVs; Phase 2: write one combined file per group
    saved: dict[tuple, Path] = {}
    total = len(csv_files) + len(frames)
    with alive_bar(total, disable=not verbose) as bar:
        all_dfs: dict[tuple, list[pd.DataFrame]] = defaultdict(list)
        for key, files in frames.items():
            for f in files:
                all_dfs[key].append(pd.read_csv(f))
                bar()

        for (profiler, data_type, smell_type), dfs in all_dfs.items():
            output_file = ANALYSIS_DIR / data_type / profiler / f"{smell_type}.csv"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            pd.concat(dfs, ignore_index=True).to_csv(output_file, index=False)
            saved[(profiler, data_type, smell_type)] = output_file
            bar()

    # Generate a PR report for every (profiler, data_type) that has both variants
    for profiler, data_type in {(k[0], k[1]) for k in saved}:
        with_key = (profiler, data_type, "with_smell")
        without_key = (profiler, data_type, "without_smell")
        if with_key not in saved or without_key not in saved:
            log.warn(
                f"[{profiler}][{data_type}] missing one variant — skipping report."
            )
            continue

        df_with = pd.read_csv(saved[with_key])
        df_without = pd.read_csv(saved[without_key])
        report = generate_pr_report(df_with, df_without, profiler, data_type)
        report_file = ANALYSIS_DIR / data_type / profiler / f"{profiler}_report.md"
        report_file.write_text(report)
        if verbose:
            log.ok(f"PR report saved → {report_file}")


def cli():
    args = parse_arguments(origin="analyzer")

    if not Path(args.path).exists():
        log.error(f"Directory '{args.path}' does not exist.")
        return

    main(args)


if __name__ == "__main__":
    cli()
