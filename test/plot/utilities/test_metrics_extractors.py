from src.plot.utilities.metrics_extractors import extract_metrics


def test_extract_metrics():
    history = [
        {"cpu_mj": 10, "gpu_mj": 20, "ane_mj": 30, "dram_mj": 40},
        {"cpu_mj": 15, "gpu_mj": 25, "ane_mj": 35, "dram_mj": 45},
    ]

    cpu_metrics, gpu_metrics, ane_metrics, dram_metrics = extract_metrics(history)

    assert cpu_metrics == [10, 15]
    assert gpu_metrics == [20, 25]
    assert ane_metrics == [30, 35]
    assert dram_metrics == [40, 45]


def test_extract_metrics_with_empty_history():
    history = []
    cpu_metrics, gpu_metrics, ane_metrics, dram_metrics = extract_metrics(history)

    assert cpu_metrics == []
    assert gpu_metrics == []
    assert ane_metrics == []
    assert dram_metrics == []


def test_extract_metrics_with_missing_keys():
    history = [
        {"cpu_mj": 10, "gpu_mj": 20, "ane_mj": 30},  # dram_mj missing
        {"cpu_mj": 15, "gpu_mj": 25, "dram_mj": 45},  # ane_mj missing
    ]

    try:
        extract_metrics(history)
        AssertionError("Expected KeyError due to missing keys")
    except KeyError:
        pass


def test_extract_metrics_with_inconsistent_keys():
    history = [
        {"cpu_mj": 10, "gpu_mj": 20, "ane_mj": 30, "dram_mj": 40},
        {"cpu_mj": 15, "gpu_mj": 25},  # ane_mj and dram_mj missing
    ]

    try:
        extract_metrics(history)
        AssertionError("Expected KeyError due to inconsistent keys")
    except KeyError:
        pass  # Expected
