from zeus_apple_silicon import AppleEnergyMonitor
from measure.abstractEnergyProfiler import AbstractEnergyProfiler

class EnergyProfiler(AbstractEnergyProfiler):
    '''
    Energy Profiler for Apple Silicon, using the AppleEnergyMonitor from the zeus_apple_silicon library.

    Each call to measure_once wraps a single code execution in a measurement window,
    collecting energy metrics per iteration and storing them in a history list.
    '''

    def __init__(self):
        self.monitor = AppleEnergyMonitor()
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
        '''
        self.monitor.begin_window(label)
        fn()
        metrics = self.monitor.end_window(label)
        entry = {
            "i": len(self.history),
            "cpu_mj": metrics.cpu_total_mj,
            "gpu_mj": metrics.gpu_mj,
            "ane_mj": metrics.ane_mj,
            "dram_mj": metrics.dram_mj,
        }
        self.history.append(entry)
        return entry