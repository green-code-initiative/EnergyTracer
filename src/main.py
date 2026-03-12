from pathlib import Path
import random
import sys

from alive_progress import alive_bar

from .analysis.statistical_analysis import analyse_histories
from .measure.carbon_energy_profiler import EnergyProfiler as carbonEnergyProfiler
from .plot.generate_plots import compare_histories
from .utilities import log
from .utilities.parser import parse_arguments
from .utilities.save_csv import save_history

# Labels
LABEL_WITH_SMELL = "with the code smell"
LABEL_WITHOUT_SMELL = "without the code smell"

# Output filenames
CSV_WITH_SMELL = "history_with_smell.csv"
CSV_WITHOUT_SMELL = "history_without_smell.csv"


def run_profiling(energy_profiler_cls, src_file, label, n_iter, verbose=False):
    """Run energy profiling on a source file and return the measurement history."""
    if verbose:
        log.header(f"Running code {label}")

    code = Path(src_file).read_text()
    monitor = energy_profiler_cls(verbose=verbose)
    try:
        with alive_bar(n_iter, disable=not verbose) as bar:
            for i in range(n_iter):
                # Set __name__ to "__main__" so that `if __name__ == "__main__"` guards work
                # correctly in the measured code.
                monitor.measure_once(
                    f"iter_{i}", lambda: exec(code, {"__name__": "__main__"})
                )
                bar()
    except KeyboardInterrupt:
        if verbose:
            log.warn(f"Energy profiling for code {label} interrupted by user.")

    monitor.finalize()
    return monitor.history


def collect_measurements(args, energy_profiler_cls):
    """Run profiling on both source files (with optional shuffle) and return ordered histories."""
    runs = [
        (args.src_file_1, LABEL_WITH_SMELL),
        (args.src_file_2, LABEL_WITHOUT_SMELL),
    ]

    swapped = False
    if args.shuffle:
        if args.verbose:
            log.info(
                "Shuffling the order of code execution to mitigate temporal effects."
            )
        if random.random() < 0.5:  # noqa: S311
            runs.reverse()
            swapped = True
            if args.verbose:
                log.dim("Order shuffled: first measuring code without code smell.")
        else:
            if args.verbose:
                log.dim("Order shuffled: first measuring code with code smell.")

    first_result = run_profiling(
        energy_profiler_cls,
        runs[0][0],
        runs[0][1],
        n_iter=args.iter,
        verbose=args.verbose,
    )

    second_result = run_profiling(
        energy_profiler_cls,
        runs[1][0],
        runs[1][1],
        n_iter=args.iter,
        verbose=args.verbose,
    )

    if args.verbose:
        log.ok("Energy profiling completed.")

    if swapped:
        return second_result, first_result
    return first_result, second_result


def save_raw(history_with_smell, history_without_smell, profiler, directory):
    """Save raw measurement histories and generate plots."""
    save_history(history_with_smell, CSV_WITH_SMELL, directory=directory)
    save_history(history_without_smell, CSV_WITHOUT_SMELL, directory=directory)
    compare_histories(
        history_with_smell,
        history_without_smell,
        profiler=profiler,
        directory=directory,
    )


def save_cleaned(
    history_with_smell, history_without_smell, profiler, directory, verbose
):
    """Remove outliers, save cleaned histories and regenerate plots. Returns the analysis dict."""
    analysis = analyse_histories(history_with_smell, history_without_smell)

    if verbose:
        log.info(
            f"Outliers removed — A: {analysis['outliers_removed']['a']}, "
            f"B: {analysis['outliers_removed']['b']}"
        )

    save_history(analysis["cleaned_a"], CSV_WITH_SMELL, directory=directory)
    save_history(analysis["cleaned_b"], CSV_WITHOUT_SMELL, directory=directory)
    compare_histories(
        analysis["cleaned_a"],
        analysis["cleaned_b"],
        profiler=profiler,
        directory=directory,
    )

    return analysis


def main(args, energy_profiler_cls):
    if args.verbose:
        log.header("EnergyTracer Configuration")
        log.dim(f"Energy profiler:               {args.profiler}")
        log.dim(f"Number of iterations:          {args.iter}")
        log.dim(f"Source file with code smell:   {args.src_file_1}")
        log.dim(f"Source file without code smell: {args.src_file_2}")

    history_with_smell, history_without_smell = collect_measurements(
        args, energy_profiler_cls
    )

    if not history_with_smell and not history_without_smell:
        log.warn("Both profiling runs returned empty histories — nothing to save.")
        return

    output_directory = Path("output") / args.profiler / args.output_dir

    save_raw(
        history_with_smell,
        history_without_smell,
        profiler=args.profiler,
        directory=output_directory / "raw",
    )

    if args.verbose:
        log.info("Raw data saved. Running statistical analysis\u2026")

    save_cleaned(
        history_with_smell,
        history_without_smell,
        profiler=args.profiler,
        directory=output_directory / "cleaned",
        verbose=args.verbose,
    )

    if args.verbose:
        log.ok("Cleaned data and plots saved.")
        print()


def cli():
    args = parse_arguments()

    if args.profiler == "mac":
        if sys.platform != "darwin":
            log.error(
                "The 'mac' profiler (zeus_apple_silicon) is only available on macOS with Apple Silicon."
            )
            log.dim("Please use the 'carbon' profiler on this platform: uv run ET")
            sys.exit(1)
        from .measure.mac_energy_profiler import EnergyProfiler as macEnergyProfiler

        energy_profiler_cls = macEnergyProfiler
    else:
        energy_profiler_cls = carbonEnergyProfiler

    main(args, energy_profiler_cls)


if __name__ == "__main__":
    cli()
