import logging
import time

from codecarbon import OfflineEmissionsTracker

from .abstract_energy_profiler import AbstractEnergyProfiler

# Silence all CodeCarbon logs below ERROR (info, warning, debug)
logging.getLogger("codecarbon").setLevel(logging.ERROR)

# Conversion factors
KWH_TO_MJ = 3_600_000_000  # 1 kWh = 3.6 MJ = 3.6e9 mJ
G_TO_MG = 1_000

# Tracker configuration
PROJECT_NAME = "energy_profiling"
COUNTRY_ISO_CODE = "BEL"


class EnergyProfiler(AbstractEnergyProfiler):
    """
    Energy Profiler using the CodeCarbon library.

    The tracker is started once and stopped once via finalize().
    Each measure_once() call only times the function execution.
    After finalize(), total energy is distributed proportionally
    to each iteration's duration, preserving per-iteration variance.
    """

    def __init__(self, verbose=False):
        self.history = []
        self._durations = []
        self._started = False
        self.verbose = verbose

        self._tracker = OfflineEmissionsTracker(
            project_name=PROJECT_NAME,
            country_iso_code=COUNTRY_ISO_CODE,
            save_to_file=False,
            log_level="error",
        )

    def measure_once(self, label: str, fn) -> dict:
        """
        Executes fn and records its wall-clock duration.
        Energy is computed later when finalize() is called.

        Note
        ----
        ane_mj holds CO2 equivalent emissions in grams (g CO2eq),
        as CodeCarbon has no Apple Neural Engine equivalent.
        """
        if not self._started:
            self._tracker.start()
            self._started = True

        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()

        self._durations.append(t1 - t0)
        return {}  # placeholder — real values filled by finalize()

    def finalize(self):
        """
        Stops the tracker and distributes total energy across iterations
        proportionally to each iteration's wall-clock duration.
        Must be called after all measure_once() calls are done.
        """
        if self.verbose:
            print("Finalizing energy profiler and computing per-iteration metrics...")

        if self._started:
            self._tracker.stop()
            self._started = False

        data = self._tracker.final_emissions_data
        total_cpu_mj = (data.cpu_energy or 0.0) * KWH_TO_MJ
        total_gpu_mj = (data.gpu_energy or 0.0) * KWH_TO_MJ
        total_ram_mj = (data.ram_energy or 0.0) * KWH_TO_MJ
        total_co2_mg = (data.emissions or 0.0) * G_TO_MG

        total_time = sum(self._durations)
        self.history = []

        for i, dt in enumerate(self._durations):
            ratio = dt / total_time if total_time > 0 else 1.0 / len(self._durations)
            self.history.append(
                {
                    "i": i,
                    "cpu_mj": total_cpu_mj * ratio,
                    "gpu_mj": total_gpu_mj * ratio,
                    "ane_mj": total_co2_mg * ratio,
                    "dram_mj": total_ram_mj * ratio,
                    "time_s": dt,
                }
            )
