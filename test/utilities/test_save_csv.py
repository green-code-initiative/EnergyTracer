from pathlib import Path

import pytest

from src.utilities.save_csv import save_history


@pytest.mark.integration
def test_save_history(tmp_path):
    history = [
        {"i": 0, "cpu_mj": 10.5, "gpu_mj": 5.2, "ane_mj": 3.1, "dram_mj": 1.0},
        {"i": 1, "cpu_mj": 11.0, "gpu_mj": 5.5, "ane_mj": 3.3, "dram_mj": 1.2},
    ]
    filename = "test_history.csv"
    save_history(history, filename, directory=tmp_path)

    output_dir = tmp_path / "csv"
    assert output_dir.exists() and output_dir.is_dir()

    csv_file = output_dir / filename
    assert csv_file.exists() and csv_file.is_file()

    with Path.open(csv_file) as f:
        lines = f.read().strip().split("\n")
        assert lines[0] == "i,cpu_mj,gpu_mj,ane_mj,dram_mj"
        assert lines[1] == "0,10.5,5.2,3.1,1.0"
        assert lines[2] == "1,11.0,5.5,3.3,1.2"


@pytest.mark.integration
def test_save_history_empty(tmp_path):
    history = []
    filename = "empty_history.csv"
    save_history(history, filename, directory=tmp_path)

    output_dir = tmp_path / "csv"
    assert not output_dir.exists()


@pytest.mark.integration
def test_save_history_missing_fields(tmp_path):
    history = [
        {"i": 0, "cpu_mj": 10.5},
        {"i": 1, "gpu_mj": 5.5},
    ]
    filename = "missing_fields_history.csv"
    save_history(history, filename, directory=tmp_path)

    output_dir = tmp_path / "csv"
    assert output_dir.exists() and output_dir.is_dir()

    csv_file = output_dir / filename
    assert csv_file.exists() and csv_file.is_file()

    with Path.open(csv_file) as f:
        lines = f.read().strip().split("\n")
        assert lines[0] == "i,cpu_mj,gpu_mj,ane_mj,dram_mj"
        assert lines[1] == "0,10.5,,,"
        assert lines[2] == "1,,5.5,,"


@pytest.mark.integration
def test_save_history_nonexistent_directory(tmp_path):
    history = [
        {"i": 0, "cpu_mj": 10.5, "gpu_mj": 5.2, "ane_mj": 3.1, "dram_mj": 1.0},
    ]
    filename = "test_history.csv"
    non_existent_dir = tmp_path / "non_existent_dir"
    save_history(history, filename, directory=non_existent_dir)

    output_dir = non_existent_dir / "csv"
    assert output_dir.exists() and output_dir.is_dir()

    csv_file = output_dir / filename
    assert csv_file.exists() and csv_file.is_file()

    with Path.open(csv_file) as f:
        lines = f.read().strip().split("\n")
        assert lines[0] == "i,cpu_mj,gpu_mj,ane_mj,dram_mj"
        assert lines[1] == "0,10.5,5.2,3.1,1.0"


@pytest.mark.integration
def test_save_history_overwrite(tmp_path):
    history1 = [
        {"i": 0, "cpu_mj": 10.5, "gpu_mj": 5.2, "ane_mj": 3.1, "dram_mj": 1.0},
    ]
    history2 = [
        {"i": 0, "cpu_mj": 20.5, "gpu_mj": 10.2, "ane_mj": 6.1, "dram_mj": 2.0},
    ]
    filename = "test_history.csv"
    save_history(history1, filename, directory=tmp_path)
    save_history(history2, filename, directory=tmp_path)

    output_dir = tmp_path / "csv"
    assert output_dir.exists() and output_dir.is_dir()

    csv_file = output_dir / filename
    assert csv_file.exists() and csv_file.is_file()

    with Path.open(csv_file) as f:
        lines = f.read().strip().split("\n")
        assert lines[0] == "i,cpu_mj,gpu_mj,ane_mj,dram_mj"
        assert lines[1] == "0,20.5,10.2,6.1,2.0"


def test_save_history_invalid_filename(tmp_path):
    history = [
        {"i": 0, "cpu_mj": 10.5, "gpu_mj": 5.2, "ane_mj": 3.1, "dram_mj": 1.0},
    ]
    invalid_filename = 'invalid:/\\*?"<>|.csv'
    try:
        save_history(history, invalid_filename, directory=tmp_path)
        AssertionError("Expected an exception due to invalid filename")
    except Exception as e:
        assert isinstance(e, (OSError, ValueError)), (
            f"Expected OSError or ValueError, got {type(e)}"
        )


def test_save_history_large_history(tmp_path):
    history = [
        {
            "i": i,
            "cpu_mj": i * 1.0,
            "gpu_mj": i * 0.5,
            "ane_mj": i * 0.2,
            "dram_mj": i * 0.1,
        }
        for i in range(1000)
    ]
    filename = "large_history.csv"
    save_history(history, filename, directory=tmp_path)

    output_dir = tmp_path / "csv"
    assert output_dir.exists() and output_dir.is_dir()

    csv_file = output_dir / filename
    assert csv_file.exists() and csv_file.is_file()

    with Path.open(csv_file) as f:
        lines = f.read().strip().split("\n")
        assert lines[0] == "i,cpu_mj,gpu_mj,ane_mj,dram_mj"
        assert len(lines) == 1001
        for i in range(1, 1001):
            expected_line = f"{i - 1},{(i - 1) * 1.0},{(i - 1) * 0.5},{(i - 1) * 0.2},{(i - 1) * 0.1}"
            assert lines[i] == expected_line
