EnergyTracer
============

*A tool to measure the energy consumption of a MacOS computer per code iteration, comparing two variants of the same code.*

---

## Description

This small project is a tool to measure the energy consumption of a MacOS computer while executing a specific code. It uses the `zeus_apple_silicon` library to collect energy metrics (CPU, GPU, ANE, DRAM) for each individual iteration of the code. The results are then plotted using `matplotlib` to compare the energy consumption per iteration between two code variants — typically one implementing a code smell (or a specific pattern) and one without.

## Usage

This project is designed to be easy to use. To perform this, `uv` is used to manage the Python environment and dependencies. Once `uv` is installed on your system, you can follow these steps:

```shell
# Install dependencies
uv sync

# Run the energy tracer
uv run src/main.py
```

This will execute the `main.py` script, which will measure the energy consumption of the default code variants and plot the results. To customize the code variants and metrics, you can use command-line arguments as follows:

1. `--help` or `-h`: Show the help message and exit.
2. `--profiler`: Choose the energy profiler to use. Options are `carbon` for CodeCarbon and `mac-silicon` for zeus_apple_silicon. Default is `carbon`.
3. `--iter`: Specify the number of iterations for the code under measurement. Default is 1000.
4. `--src-file-1`: Path to the source file with the code smell to measure. Default is `src/python/file_with_code_smell.py`.
5. `--src-file-2`: Path to the source file without the code smell to measure. Default is `src/python/file_without_code_smell.py`.

> Further improvements could include other measurement libraries, with other metrics.

As you can specify the source files, you can easily compare the energy consumption of different code variants, allowing you to identify which one is more energy-efficient. By default, the tool will compare a code located in `src/python/file_with_code_smell.py` with another code located in `src/python/file_without_code_smell.py`, but you can change these paths to compare any two Python scripts you want.

The generated plots are saved in the `output` directory.

## Author

Florian Stormacq - [GitHub](https://github.com/fstormacq)

## Acknowledgements

This project was developed as part of the Master 1 Computer Science program at the University of Namur, Belgium.