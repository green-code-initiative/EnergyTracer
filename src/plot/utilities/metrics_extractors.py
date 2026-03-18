from typing import Mapping, Optional, Sequence


def extract_metrics(
    history: Sequence[Mapping[str, float]],
) -> tuple[list[float], list[float], list[float], list[float], list[Optional[float]]]:
    cpu_metrics = [entry["cpu_mj"] for entry in history]
    gpu_metrics = [entry["gpu_mj"] for entry in history]
    ane_metrics = [entry["ane_mj"] for entry in history]
    dram_metrics = [entry["dram_mj"] for entry in history]
    time_metrics = [entry.get("time_s", None) for entry in history]

    return cpu_metrics, gpu_metrics, ane_metrics, dram_metrics, time_metrics
