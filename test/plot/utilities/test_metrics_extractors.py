import pytest

from src.plot.utilities.metrics_extractors import extract_metrics


@pytest.mark.unit
def test_extract_metrics():
    history = [
        {"cpu_mj": 10, "gpu_mj": 20, "ane_mj": 30, "dram_mj": 40, "time_s": 1},
        {"cpu_mj": 15, "gpu_mj": 25, "ane_mj": 35, "dram_mj": 45, "time_s": 2},
    ]

    cpu_metrics, gpu_metrics, ane_metrics, dram_metrics, time_metrics = extract_metrics(
        history
    )

    assert cpu_metrics == [10, 15]
    assert gpu_metrics == [20, 25]
    assert ane_metrics == [30, 35]
    assert dram_metrics == [40, 45]
    assert time_metrics == [1, 2]


@pytest.mark.unit
def test_extract_metrics_with_empty_history():
    history = []
    cpu_metrics, gpu_metrics, ane_metrics, dram_metrics, time_metrics = extract_metrics(
        history
    )

    assert cpu_metrics == []
    assert gpu_metrics == []
    assert ane_metrics == []
    assert dram_metrics == []
    assert time_metrics == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "history",
    [
        pytest.param(
            [
                {"cpu_mj": 10, "gpu_mj": 20, "ane_mj": 30},
                {"cpu_mj": 15, "gpu_mj": 25, "dram_mj": 45},
            ],
            id="missing_keys",
        ),
        pytest.param(
            [
                {"cpu_mj": 10, "gpu_mj": 20, "ane_mj": 30, "dram_mj": 40},
                {"cpu_mj": 15, "gpu_mj": 25},
            ],
            id="inconsistent_keys",
        ),
    ],
)
def test_extract_metrics_with_invalid_keys(history):
    with pytest.raises(KeyError):
        extract_metrics(history)
