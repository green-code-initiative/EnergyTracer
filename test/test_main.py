from unittest.mock import MagicMock, patch

import pytest

from src.main import cli, run_profiling


@pytest.fixture
def src_file_1(tmp_path):
    file = tmp_path / "with_smell.py"
    file.write_text("x = 10 ** 2")
    return str(file)


@pytest.fixture
def src_file_2(tmp_path):
    file = tmp_path / "without_smell.py"
    file.write_text("x = 10 * 10")
    return str(file)


@pytest.fixture
def invalid_file(tmp_path):
    file = tmp_path / "invalid.py"
    file.write_text("x = 1 +")
    return str(file)


@pytest.fixture
def mock_profiler_cls():
    mock_profiler = MagicMock()
    mock_cls = MagicMock(return_value=mock_profiler)
    return mock_cls, mock_profiler


@pytest.mark.unit
@pytest.mark.parametrize("n_iter", [1, 2, 5, 10])
@pytest.mark.parametrize("verbose", [False, True])
def test_run_profiling(src_file_1, mock_profiler_cls, n_iter, verbose):

    # Mock profiler class
    mock_cls, mock_profiler = mock_profiler_cls

    history = run_profiling(
        mock_cls, src_file_1, "test label", n_iter=n_iter, verbose=verbose
    )

    mock_cls.assert_called_once_with(verbose=verbose)
    assert mock_profiler.measure_once.call_count == n_iter
    mock_profiler.finalize.assert_called_once()
    assert history == mock_profiler.history


@pytest.mark.unit
@pytest.mark.parametrize("n_iter", [1, 2, 5, 10])
@pytest.mark.parametrize("verbose", [False, True])
def test_run_profiling_with_keyboard_interrupt(
    src_file_1, mock_profiler_cls, n_iter, verbose
):

    mock_cls, mock_profiler = mock_profiler_cls

    def side_effect(label, func):
        if label == "iter_1":
            raise KeyboardInterrupt()
        return

    mock_profiler.measure_once.side_effect = side_effect

    history = run_profiling(
        mock_cls, src_file_1, "test label", n_iter=n_iter, verbose=verbose
    )

    mock_cls.assert_called_once_with(verbose=verbose)
    assert mock_profiler.measure_once.call_count == 1 if n_iter < 2 else 2
    mock_profiler.finalize.assert_called_once()
    assert history == mock_profiler.history


@pytest.mark.unit
@pytest.mark.parametrize("profiler", ["mac-silicon", "carbon"])
@patch("src.main.parse_arguments")
def test_cli_with_profilers_on_darwin(mock_parse, monkeypatch, profiler):
    mock_parse.return_value = MagicMock(profiler=profiler)
    monkeypatch.setattr("sys.platform", "darwin")

    mock_mac_module = MagicMock()
    with (
        patch.dict(
            "sys.modules",
            {
                "zeus.device.gpu.apple": MagicMock(),
                "src.measure.mac_energy_profiler": mock_mac_module,
            },
        ),
        patch("src.main.main") as mock_main,
    ):
        cli()

    mock_main.assert_called_once()
    _, energy_profiler_cls = mock_main.call_args.args
    assert energy_profiler_cls is not None


@pytest.mark.unit
@pytest.mark.parametrize("platform", ["win32", "linux"])
@patch("src.main.parse_arguments")
def test_cli_with_mac_profiler_on_non_darwin(mock_parse, monkeypatch, platform):
    mock_parse.return_value = MagicMock(profiler="mac-silicon")
    monkeypatch.setattr("sys.platform", platform)

    with pytest.raises(SystemExit) as exc_info:
        cli()

    assert exc_info.value.code == 1


@pytest.mark.unit
@pytest.mark.parametrize("platform", ["win32", "linux"])
@patch("src.main.parse_arguments")
def test_cli_with_carbon_profiler_on_non_darwin(mock_parse, monkeypatch, platform):
    mock_parse.return_value = MagicMock(profiler="carbon")
    monkeypatch.setattr("sys.platform", platform)

    with patch("src.main.main") as mock_main:
        cli()

    mock_main.assert_called_once()
    _, energy_profiler_cls = mock_main.call_args.args
    assert energy_profiler_cls is not None


@pytest.mark.unit
@pytest.mark.parametrize("profiler", ["mac-silicon", "carbon"])
@pytest.mark.parametrize(
    "shuffle, verbose", [(False, False), (False, True), (True, False), (True, True)]
)
@patch("src.main.analyse_histories")
@patch("src.main.save_history")
@patch("src.main.compare_histories")
def test_main_with_valid_arguments(
    mock_compare_histories,
    mock_save_history,
    mock_analyse_histories,
    mock_profiler_cls,
    src_file_1,
    src_file_2,
    profiler,
    verbose,
    shuffle,
):
    from src.main import main

    mock_cls, mock_profiler = mock_profiler_cls

    mock_analyse_histories.return_value = {
        "raw_sizes": {"a": 2, "b": 2},
        "cleaned_sizes": {"a": 2, "b": 2},
        "outliers_removed": {"a": 0, "b": 0},
        "cleaned_a": [{"i": 0, "cpu_mj": 1, "gpu_mj": 1, "ane_mj": 1, "dram_mj": 1}],
        "cleaned_b": [{"i": 0, "cpu_mj": 1, "gpu_mj": 1, "ane_mj": 1, "dram_mj": 1}],
        "metrics": {},
    }

    mock_args = MagicMock(
        profiler=profiler,
        src_file_1=src_file_1,
        src_file_2=src_file_2,
        iter=2,
        shuffle=shuffle,
        verbose=verbose,
        output_dir="test_output",
    )

    main(mock_args, mock_cls)

    assert mock_profiler.measure_once.call_count == 4
    assert mock_profiler.finalize.call_count == 2

    assert mock_save_history.call_count == 4
    assert mock_compare_histories.call_count == 2

    mock_analyse_histories.assert_called_once()
