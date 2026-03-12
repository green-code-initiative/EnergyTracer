import argparse

# Default argument values
DEFAULT_PROFILER = "carbon"
DEFAULT_ITERATIONS = 1_000
DEFAULT_SRC_FILE_1 = "src/python/file_with_code_smell.py"
DEFAULT_SRC_FILE_2 = "src/python/file_without_code_smell.py"
DEFAULT_OUTPUT_DIR = "output"


def parse_arguments(origin: str = "main"):
    if origin == "main":
        return parse_main_arguments()

    if origin == "analyzer":
        return parse_analyzer_arguments()
    raise ValueError(f"Unknown argument origin: {origin}")


def parse_main_arguments():
    parser = argparse.ArgumentParser(
        description="EnergyTracer: A tool to measure the energy consumption of code with and without code smells."
    )
    parser.add_argument(
        "-p",
        "--profiler",
        type=str,
        choices=["mac", "carbon"],
        default=DEFAULT_PROFILER,
        help="Energy profiler to use: 'carbon' for CodeCarbon, 'mac' for zeus_apple_silicon. Default is 'carbon'.",
    )
    parser.add_argument(
        "-n",
        "--iter",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of iterations for the code under measurement. Default is 1000.",
    )
    parser.add_argument(
        "-f1",
        "--src-file-1",
        type=str,
        default=DEFAULT_SRC_FILE_1,
        help="Path to the source file with the code smell to measure. Default is 'src/python/file_with_code_smell.py'.",
    )
    parser.add_argument(
        "-f2",
        "--src-file-2",
        type=str,
        default=DEFAULT_SRC_FILE_2,
        help="Path to the source file without the code smell to measure. Default is 'src/python/file_without_code_smell.py'.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Path to the output directory. Default is 'output'.",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle the order of code execution (with and without code smell) to mitigate temporal effects.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output during profiling.",
    )

    return parser.parse_args()


def parse_analyzer_arguments():
    parser = argparse.ArgumentParser(
        description="EnergyTracer Analyzer: A tool to analyze the energy consumption data collected by EnergyTracer."
    )
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Path to the directory containing the raw data to analyze. Default is 'output'.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output during analysis.",
    )

    return parser.parse_args()
