from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from src.plot.generate_plots import (
    compare_histories,
    plot_all_metrics,
    plot_moustache,
    plot_specific_metrics,
    prepare_dataframe,
)


@pytest.fixture
def valid_histories():
    history1 = [
        {"cpu_mj": 10, "gpu_mj": 5, "ane_mj": 2, "dram_mj": 3},
        {"cpu_mj": 12, "gpu_mj": 6, "ane_mj": 3, "dram_mj": 4},
    ]
    history2 = [
        {"cpu_mj": 8, "gpu_mj": 4, "ane_mj": 1, "dram_mj": 2},
        {"cpu_mj": 9, "gpu_mj": 5, "ane_mj": 2, "dram_mj": 3},
    ]
    return history1, history2


@pytest.fixture
def expected_name_in_dataframe():
    def _factory(ane_label="ANE"):
        return [
            "Iteration",
            "CPU with code smell",
            "GPU with code smell",
            f"{ane_label} with code smell",
            "DRAM with code smell",
            "CPU without code smell",
            "GPU without code smell",
            f"{ane_label} without code smell",
            "DRAM without code smell",
        ]

    return _factory


@pytest.mark.unit
@pytest.mark.parametrize("ane_label", ["ANE", "CO2"])
def test_prepare_dataframe_with_valid_histories(
    valid_histories, expected_name_in_dataframe, ane_label
):
    history1, history2 = valid_histories

    df = prepare_dataframe(history1, history2, ane_label)

    assert not df.empty
    assert len(df) == 2
    for column in expected_name_in_dataframe(ane_label):
        assert column in df.columns

    assert df["CPU with code smell"].tolist() == [10, 12]
    assert df["GPU with code smell"].tolist() == [5, 6]
    assert df[f"{ane_label} with code smell"].tolist() == [2, 3]
    assert df["DRAM with code smell"].tolist() == [3, 4]
    assert df["CPU without code smell"].tolist() == [8, 9]
    assert df["GPU without code smell"].tolist() == [4, 5]
    assert df[f"{ane_label} without code smell"].tolist() == [1, 2]
    assert df["DRAM without code smell"].tolist() == [2, 3]


@pytest.mark.unit
@pytest.mark.parametrize("ane_label", ["ANE", "CO2"])
def test_prepare_dataframe_with_empty_histories(expected_name_in_dataframe, ane_label):
    history1 = []
    history2 = []

    df = prepare_dataframe(history1, history2, ane_label)

    assert df.empty
    assert len(df) == 0

    for column in expected_name_in_dataframe(ane_label=ane_label):
        assert column in df.columns
        assert df[column].empty


@pytest.mark.unit
@pytest.mark.parametrize("ane_label", ["ANE", "CO2"])
def test_prepare_dataframe_with_unequal_histories(
    expected_name_in_dataframe, ane_label
):
    history1 = [
        {"cpu_mj": 10, "gpu_mj": 5, "ane_mj": 2, "dram_mj": 3},
        {"cpu_mj": 12, "gpu_mj": 6, "ane_mj": 3, "dram_mj": 4},
    ]
    history2 = [
        {"cpu_mj": 8, "gpu_mj": 4, "ane_mj": 1, "dram_mj": 2},
    ]

    df = prepare_dataframe(history1, history2, ane_label)

    assert not df.empty
    assert len(df) == 2

    for column in expected_name_in_dataframe(ane_label=ane_label):
        assert column in df.columns

    assert df["CPU with code smell"].tolist() == [10, 12]
    assert df["GPU with code smell"].tolist() == [5, 6]
    assert df[f"{ane_label} with code smell"].tolist() == [2, 3]
    assert df["DRAM with code smell"].tolist() == [3, 4]

    assert (
        df["CPU without code smell"].tolist().count(8) == 1
        and df["CPU without code smell"].isna().sum() == 1
    )
    assert (
        df["GPU without code smell"].tolist().count(4) == 1
        and df["GPU without code smell"].isna().sum() == 1
    )
    assert (
        df[f"{ane_label} without code smell"].tolist().count(1) == 1
        and df[f"{ane_label} without code smell"].isna().sum() == 1
    )
    assert (
        df["DRAM without code smell"].tolist().count(2) == 1
        and df["DRAM without code smell"].isna().sum() == 1
    )


@pytest.mark.integration
@pytest.mark.parametrize("ane_label", ["ANE", "CO2"])
def test_plot_all_metrics_with_valid_histories(valid_histories, tmp_path, ane_label):
    history1, history2 = valid_histories
    df = prepare_dataframe(history1, history2, ane_label)
    output_path = Path(tmp_path) / "all_energy_comparison.png"

    plot_all_metrics(df, output_path, ane_label=ane_label)

    assert output_path.exists()
    assert output_path.is_file()
    assert output_path.stat().st_size > 0
    assert output_path.read_bytes().startswith(b"\x89PNG")
    assert plt.get_fignums() == []


@pytest.mark.integration
def test_plot_all_metrics_with_empty_dataframe(tmp_path):
    df = prepare_dataframe([], [], "ANE")
    output_path = Path(tmp_path) / "all_energy_comparison.png"

    plot_all_metrics(df, output_path, ane_label="ANE")

    assert not output_path.exists()
    assert plt.get_fignums() == []


@pytest.mark.integration
def test_plot_all_metrics_with_unequal_histories(tmp_path):
    history1 = [
        {"cpu_mj": 10, "gpu_mj": 5, "ane_mj": 2, "dram_mj": 3},
        {"cpu_mj": 12, "gpu_mj": 6, "ane_mj": 3, "dram_mj": 4},
    ]
    history2 = [
        {"cpu_mj": 8, "gpu_mj": 4, "ane_mj": 1, "dram_mj": 2},
    ]
    df = prepare_dataframe(history1, history2, "ANE")
    output_path = Path(tmp_path) / "all_energy_comparison.png"

    plot_all_metrics(df, output_path, ane_label="ANE")

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"\x89PNG")
    assert plt.get_fignums() == []


def _assert_valid_png_output(output_path, tmp_path, metric, is_moustache=False):
    assert output_path.exists()
    assert output_path.is_file()
    assert output_path.stat().st_size > 0
    assert (
        output_path.name
        == f"{metric}_{'moustache.png' if is_moustache else 'energy_comparison.png'}"
    )
    assert output_path.parent == tmp_path
    assert output_path.read_bytes().startswith(b"\x89PNG")
    assert plt.get_fignums() == []


@pytest.mark.integration
@pytest.mark.parametrize(
    "metric,ane_label",
    [
        ("cpu", "ANE"),
        ("gpu", "ANE"),
        ("dram", "ANE"),
        ("ANE", "ANE"),
        ("CO2", "CO2"),
    ],
)
def test_plot_specific_metric_with_valid_histories(
    valid_histories, tmp_path, metric, ane_label
):
    history1, history2 = valid_histories
    df = prepare_dataframe(history1, history2, ane_label)
    output_path = Path(tmp_path) / f"{metric}_energy_comparison.png"

    plot_specific_metrics(df, metric, output_path, unit="mJ")

    _assert_valid_png_output(output_path, tmp_path, metric)


@pytest.mark.integration
@pytest.mark.parametrize(
    "metric,ane_label",
    [
        ("cpu", "ANE"),
        ("gpu", "ANE"),
        ("dram", "ANE"),
        ("ANE", "ANE"),
        ("CO2", "CO2"),
    ],
)
def test_plot_specific_metric_with_unequal_histories(tmp_path, metric, ane_label):
    history1 = [
        {"cpu_mj": 10, "gpu_mj": 5, "ane_mj": 2, "dram_mj": 3},
        {"cpu_mj": 12, "gpu_mj": 6, "ane_mj": 3, "dram_mj": 4},
    ]
    history2 = [
        {"cpu_mj": 8, "gpu_mj": 4, "ane_mj": 1, "dram_mj": 2},
    ]
    df = prepare_dataframe(history1, history2, ane_label)
    output_path = Path(tmp_path) / f"{metric}_energy_comparison.png"

    plot_specific_metrics(df, metric, output_path, unit="mJ")

    _assert_valid_png_output(output_path, tmp_path, metric)


@pytest.mark.integration
@pytest.mark.parametrize(
    "metric,ane_label",
    [
        ("cpu", "ANE"),
        ("gpu", "ANE"),
        ("dram", "ANE"),
        ("ANE", "ANE"),
        ("CO2", "CO2"),
    ],
)
def test_plot_specific_metric_with_empty_dataframe(tmp_path, metric, ane_label):
    df = prepare_dataframe([], [], ane_label)
    output_path = Path(tmp_path) / f"{metric}_energy_comparison.png"

    plot_specific_metrics(df, metric, output_path, unit="mJ")

    assert not output_path.exists()
    assert plt.get_fignums() == []


@pytest.mark.integration
@pytest.mark.parametrize(
    "metric,ane_label",
    [
        ("cpu", "ANE"),
        ("gpu", "ANE"),
        ("dram", "ANE"),
        ("ANE", "ANE"),
        ("CO2", "CO2"),
    ],
)
def test_plot_moustache_with_valid_histories(
    valid_histories, tmp_path, metric, ane_label
):
    history1, history2 = valid_histories
    df = prepare_dataframe(history1, history2, ane_label)
    output_path = Path(tmp_path) / f"{metric}_moustache.png"

    plot_moustache(df, metric, output_path, unit="mJ")

    _assert_valid_png_output(output_path, tmp_path, metric, is_moustache=True)


@pytest.mark.integration
@pytest.mark.parametrize(
    "metric,ane_label",
    [
        ("cpu", "ANE"),
        ("gpu", "ANE"),
        ("dram", "ANE"),
        ("ANE", "ANE"),
        ("CO2", "CO2"),
    ],
)
def test_plot_moustache_with_unequal_histories(tmp_path, metric, ane_label):
    history1 = [
        {"cpu_mj": 10, "gpu_mj": 5, "ane_mj": 2, "dram_mj": 3},
        {"cpu_mj": 12, "gpu_mj": 6, "ane_mj": 3, "dram_mj": 4},
    ]
    history2 = [
        {"cpu_mj": 8, "gpu_mj": 4, "ane_mj": 1, "dram_mj": 2},
    ]
    df = prepare_dataframe(history1, history2, ane_label)
    output_path = Path(tmp_path) / f"{metric}_moustache.png"

    plot_moustache(df, metric, output_path, unit="mJ")

    _assert_valid_png_output(output_path, tmp_path, metric, is_moustache=True)


@pytest.mark.integration
@pytest.mark.parametrize(
    "metric,ane_label",
    [
        ("cpu", "ANE"),
        ("gpu", "ANE"),
        ("dram", "ANE"),
        ("ANE", "ANE"),
        ("CO2", "CO2"),
    ],
)
def test_plot_moustache_with_empty_dataframe(tmp_path, metric, ane_label):
    df = prepare_dataframe([], [], ane_label)
    output_path = Path(tmp_path) / f"{metric}_moustache.png"

    plot_moustache(df, metric, output_path, unit="mJ")

    assert not output_path.exists()
    assert plt.get_fignums() == []


@pytest.mark.integration
@pytest.mark.parametrize("ane_label", ["ANE", "CO2"])
def test_compare_histories_with_valid_histories(valid_histories, tmp_path, ane_label):
    history1, history2 = valid_histories
    output_dir = Path(tmp_path)
    compare_histories(
        history1,
        history2,
        profiler="mac" if ane_label == "ANE" else "carbon",
        directory=output_dir,
    )

    # Check that all expected plots are generated
    expected_plots = (
        [
            f"{metric}_energy_comparison.png"
            for metric in ["cpu", "gpu", "dram", ane_label.lower()]
        ]
        + [
            f"{metric}_moustache.png"
            for metric in ["cpu", "gpu", "dram", ane_label.lower()]
        ]
        + [
            f"{metric}_violin.png"
            for metric in ["cpu", "gpu", "dram", ane_label.lower()]
        ]
    )

    for plot_name in expected_plots:
        if "energy_comparison" in plot_name:
            subdir = "comparisons"
        elif "moustache" in plot_name:
            subdir = "moustaches"
        else:
            subdir = "violins"
        plot_path = Path(output_dir / "plots" / subdir / plot_name)
        assert plot_path.exists()
        assert plot_path.is_file()
        assert plot_path.stat().st_size > 0
        assert plot_path.read_bytes().startswith(b"\x89PNG")
        assert plt.get_fignums() == []  # Ensure no open figures remain after plotting
