from abc import ABC, abstractmethod

class AbstractEnergyProfiler(ABC):
    '''
    Energy Profiler for Apple Silicon, using the AppleEnergyMonitor from the zeus_apple_silicon library.

    Each call to measure_once wraps a single code execution in a measurement window,
    collecting energy metrics per iteration and storing them in a history list.
    '''

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def measure_once(self, label: str, fn) -> dict:
        pass