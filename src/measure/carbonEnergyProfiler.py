from codecarbon import EmissionsTracker
from measure.abstractEnergyProfiler import AbstractEnergyProfiler

KWH_TO_MJ = 3_600_000_000 # 1 kWh = 3.6 MJ = 3.6e9 mJ

class EnergyProfiler(AbstractEnergyProfiler):
    '''
    Energy Profiler using the CodeCarbon library.

    Each call to measure_once wraps a single code execution in a measurement window,
    collecting energy metrics per iteration and storing them in a history list.
    '''

    def __init__(self):
        self.history = []

    def measure_once(self, label: str, fn) -> dict:
        '''
        Measures energy consumed during a single execution of fn.

        Inputs
        ------
            label: A unique string label for the measurement window.
            fn: A callable to execute and measure.

        Returns
        -------
            A dict with keys: i, cpu_mj, gpu_mj, ane_mj, dram_mj.
        
        Note
        ----
        ane_mj holds CO2 equivalent emissions in grams (g CO2eq),
        as CodeCarbon has no Apple Neural Engine equivalent.
        '''
        tracker = EmissionsTracker(
            project_name=label,
            save_to_file=False,
            log_level="error",
        )
        tracker.start()
        fn()
        tracker.stop()

        data = tracker.final_emissions_data
        entry = {
            "i": len(self.history),
            "cpu_mj": (data.cpu_energy or 0.0) * KWH_TO_MJ,
            "gpu_mj": (data.gpu_energy or 0.0) * KWH_TO_MJ,
            "ane_mj": (data.emissions or 0.0) * 1_000,
            "dram_mj": (data.ram_energy or 0.0) * KWH_TO_MJ,
        }
        self.history.append(entry)
        return entry
