from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.analyzer import (
    classify_csv_files_by_group,
    cli,
    generate_statistical_reports,
    main,
    merge_and_save_csv_groups,
    process_csv_files,
)

# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("path", ["output", "non_existent_dir"])
@pytest.mark.parametrize("verbose", [False, True])
def test_analyzer_cli_with_args(path, verbose):
    with (
        patch("src.analyzer.parse_arguments") as mock_parse,
        patch("src.analyzer.main") as mock_main,
    ):
        mock_parse.return_value = MagicMock(path=path, verbose=verbose)
        cli()

    if not Path(path).exists():
        mock_main.assert_not_called()
    else:
        mock_main.assert_called_once()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("path", ["output", "non_existent_dir"])
@pytest.mark.parametrize("verbose", [False, True])
def test_analyzer_main_with_args(path, verbose):
    with patch("src.analyzer.process_csv_files") as mock_process:
        args = MagicMock(path=path, verbose=verbose)
        main(args)

    mock_process.assert_called_once_with(Path(path), verbose=verbose)


# ---------------------------------------------------------------------------
# classify_csv_files_by_group
# ---------------------------------------------------------------------------


@pytest.fixture
def mocked_csv_files(tmp_path):
    # Create a set of mock CSV files with various paths
    csv_files = [
        tmp_path / "output/profiler1/cleaned/with_smell_run1.csv",
        tmp_path / "output/profiler1/cleaned/without_smell_run1.csv",
        tmp_path / "output/profiler2/raw/with_smell_run1.csv",
        tmp_path / "output/profiler2/raw/without_smell_run1.csv",
        tmp_path / "invalid/path/file5.csv",  # Invalid file (no profiler segment)
    ]
    for file in csv_files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
    return csv_files


@pytest.mark.unit
def test_classify_csv_files_by_group_valid_files(mocked_csv_files):
    result = classify_csv_files_by_group(mocked_csv_files)

    assert ("profiler1", "cleaned", "with_smell") in result
    assert ("profiler1", "cleaned", "without_smell") in result
    assert ("profiler2", "raw", "with_smell") in result
    assert ("profiler2", "raw", "without_smell") in result
    assert len(result) == 4


@pytest.mark.unit
def test_classify_csv_files_by_group_skips_invalid_path(mocked_csv_files):
    # The fixture contains one file under "invalid/path/" — it must be skipped
    result = classify_csv_files_by_group(mocked_csv_files)

    all_files = [f for files in result.values() for f in files]
    assert not any("invalid" in str(f) for f in all_files)


@pytest.mark.unit
def test_classify_csv_files_by_group_empty_input():
    assert classify_csv_files_by_group([]) == {}


@pytest.mark.unit
def test_classify_csv_files_by_group_no_data_type_segment(tmp_path):
    # File under output/<profiler>/ but neither "cleaned" nor "raw" in path
    csv_file = tmp_path / "output" / "profiler1" / "with_smell_file.csv"
    csv_file.parent.mkdir(parents=True)
    csv_file.touch()

    result = classify_csv_files_by_group([csv_file])

    assert result == {}


@pytest.mark.unit
def test_classify_csv_files_by_group_no_smell_segment(tmp_path):
    # File has no "with_smell" or "without_smell" in its stem
    csv_file = tmp_path / "output" / "profiler1" / "cleaned" / "unknown.csv"
    csv_file.parent.mkdir(parents=True)
    csv_file.touch()

    result = classify_csv_files_by_group([csv_file])

    assert result == {}


# ---------------------------------------------------------------------------
# merge_and_save_csv_groups
# ---------------------------------------------------------------------------

_SAMPLE_DF = pd.DataFrame(
    {
        "cpu_mj": [1.0, 2.0],
        "gpu_mj": [3.0, 4.0],
        "ane_mj": [0.1, 0.2],
        "dram_mj": [0.5, 0.6],
    }
)


@pytest.fixture
def csv_groups_with_content(tmp_path):
    """Two groups, each with two CSV files that share the same schema."""
    groups: dict[tuple, list] = {}
    all_files: list[Path] = []
    for smell in ("with_smell", "without_smell"):
        group_dir = tmp_path / "output" / "profiler1" / "cleaned" / smell
        group_dir.mkdir(parents=True)
        files = []
        for i in range(2):
            f = group_dir / f"run_{i}.csv"
            _SAMPLE_DF.to_csv(f, index=False)
            files.append(f)
            all_files.append(f)
        groups[("profiler1", "cleaned", smell)] = files
    return all_files, groups


@pytest.mark.unit
@pytest.mark.parametrize("verbose", [False, True])
def test_merge_and_save_csv_groups_creates_merged_files(
    csv_groups_with_content, tmp_path, verbose
):
    all_files, groups = csv_groups_with_content

    with patch("src.analyzer.ANALYSIS_DIR", tmp_path / "results"):
        result = merge_and_save_csv_groups(all_files, groups, verbose=verbose)

    assert ("profiler1", "cleaned", "with_smell") in result
    assert ("profiler1", "cleaned", "without_smell") in result

    for path in result.values():
        assert path.exists()
        df = pd.read_csv(path)
        # Each group had 2 files of 2 rows each → 4 rows merged
        assert len(df) == 4


@pytest.mark.unit
def test_merge_and_save_csv_groups_empty_input():
    result = merge_and_save_csv_groups([], {})
    assert result == {}


# ---------------------------------------------------------------------------
# generate_statistical_reports
# ---------------------------------------------------------------------------


@pytest.fixture
def merged_paths(tmp_path):
    """Minimal merged CSVs for the report generator."""
    paths: dict[tuple, Path] = {}
    for smell in ("with_smell", "without_smell"):
        csv_path = tmp_path / "cleaned" / "profiler1" / f"{smell}.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        _SAMPLE_DF.to_csv(csv_path, index=False)
        paths[("profiler1", "cleaned", smell)] = csv_path
    return paths


@pytest.mark.unit
@pytest.mark.parametrize("verbose", [False, True])
def test_generate_statistical_reports_writes_report(merged_paths, tmp_path, verbose):
    with (
        patch("src.analyzer.ANALYSIS_DIR", tmp_path),
        patch(
            "src.analyzer.generate_pr_report", return_value="# report"
        ) as mock_report,
    ):
        generate_statistical_reports(merged_paths, verbose=verbose)

    mock_report.assert_called_once()
    report_file = tmp_path / "cleaned" / "profiler1" / "profiler1_report.md"
    assert report_file.exists()
    assert report_file.read_text() == "# report"


@pytest.mark.unit
def test_generate_statistical_reports_skips_missing_variant(tmp_path):
    # Only the with_smell variant is present
    csv_path = tmp_path / "cleaned" / "profiler1" / "with_smell.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    _SAMPLE_DF.to_csv(csv_path, index=False)
    incomplete_paths = {("profiler1", "cleaned", "with_smell"): csv_path}

    with (
        patch("src.analyzer.ANALYSIS_DIR", tmp_path),
        patch("src.analyzer.generate_pr_report") as mock_report,
    ):
        generate_statistical_reports(incomplete_paths)

    mock_report.assert_not_called()


# ---------------------------------------------------------------------------
# process_csv_files (integration — sub-functions mocked)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("verbose", [False, True])
def test_process_csv_files_calls_pipeline(tmp_path, verbose):
    # Create a dummy CSV so the early-return guard is not triggered
    dummy_csv = tmp_path / "dummy.csv"
    dummy_csv.touch()

    fake_group = {("p", "cleaned", "with_smell"): []}
    fake_merged = {("p", "cleaned", "with_smell"): tmp_path / "x.csv"}

    with (
        patch(
            "src.analyzer.classify_csv_files_by_group", return_value=fake_group
        ) as mock_classify,
        patch(
            "src.analyzer.merge_and_save_csv_groups", return_value=fake_merged
        ) as mock_merge,
        patch("src.analyzer.generate_statistical_reports") as mock_reports,
    ):
        process_csv_files(tmp_path, verbose=verbose)

    mock_classify.assert_called_once()
    mock_merge.assert_called_once_with(
        mock_classify.call_args[0][0], fake_group, verbose=verbose
    )
    mock_reports.assert_called_once_with(fake_merged, verbose=verbose)
