import argparse

from measure.carbonEnergyProfiler import EnergyProfiler as carbonEnergyProfiler
from measure.macEnergyProfiler import EnergyProfiler as macEnergyProfiler

from utilities.save_CSV import save_history
from plot.generate_plot import compare_histories

def main(args, energy_profiler_cls):
    print("Starting energy profiler")
    print("------------------------")
    print(f"Energy profiler: {args.profiler}")
    print(f"Number of iterations: {args.iter}")
    print(f"Source file with code smell: {args.src_file_1}")
    print(f"Source file without code smell: {args.src_file_2}\n")

    print("\tRunning code with the code smell")
    print("\t--------------------------------")

    code1 = open(args.src_file_1).read()
    monitor1 = energy_profiler_cls()
    try:
        for i in range(args.iter):
            monitor1.measure_once(f"iter_{i}", lambda: exec(code1))
        print("\tEnergy profiling for code with code smell completed.\n")
    except KeyboardInterrupt:
        print("\tEnergy profiling for code with code smell interrupted by user.\n")
    
    first_history = monitor1.history

    print("\n\tRunning code without the code smell")
    print("\t-------------------------------------")

    code2 = open(args.src_file_2).read()
    monitor2 = energy_profiler_cls()
    try:
        for i in range(args.iter):
            monitor2.measure_once(f"iter_{i}", lambda: exec(code2))
        print("\tEnergy profiling for code without code smell completed.\n")
    except KeyboardInterrupt:
        print("\tEnergy profiling for code without code smell interrupted by user.\n")
    
    second_history = monitor2.history

    print("Energy profiling completed.")

    save_history(first_history, "history_with_smell.csv")
    save_history(second_history, "history_without_smell.csv")

    compare_histories(first_history, second_history, profiler=args.profiler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Energy Profiler for Apple Silicon")
    parser.add_argument("-p", "--profiler", type=str, choices=["mac-silicon", "carbon"], default="carbon", help="Energy profiler to use: 'carbon' for CodeCarbon, 'mac-silicon' for zeus_apple_silicon. Default is 'carbon'.")
    parser.add_argument("-n", "--iter", type=int, default=1_000, help="Number of iterations for the code under measurement. Default is 1000.")
    parser.add_argument("-f1", "--src-file-1", type=str, default="src/python/file_with_code_smell.py", help="Path to the source file with the code smell to measure. Default is 'src/python/file_with_code_smell.py'.")
    parser.add_argument("-f2", "--src-file-2", type=str, default="src/python/file_without_code_smell.py", help="Path to the source file without the code smell to measure. Default is 'src/python/file_without_code_smell.py'.")

    args = parser.parse_args()

    energy_profiler_cls = macEnergyProfiler if args.profiler == "mac-silicon" else carbonEnergyProfiler
    
    main(args, energy_profiler_cls)