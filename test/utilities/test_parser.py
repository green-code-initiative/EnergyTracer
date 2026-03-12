import pytest

from src.utilities.parser import (
    DEFAULT_ITERATIONS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PROFILER,
    DEFAULT_SRC_FILE_1,
    DEFAULT_SRC_FILE_2,
    parse_arguments,
)


@pytest.mark.unit
def test_parse_arguments_defaults(monkeypatch):
    monkeypatch.setattr("sys.argv", ["ET"])
    args = parse_arguments("main")
    assert args.profiler == DEFAULT_PROFILER
    assert args.iter == DEFAULT_ITERATIONS
    assert args.src_file_1 == DEFAULT_SRC_FILE_1
    assert args.src_file_2 == DEFAULT_SRC_FILE_2
    assert args.output_dir == DEFAULT_OUTPUT_DIR
    assert not args.shuffle
    assert not args.verbose


@pytest.mark.unit
@pytest.mark.parametrize("profiler", ["mac", "carbon"])
def test_parse_profiler_argument(monkeypatch, profiler):
    monkeypatch.setattr("sys.argv", ["ET", "-p", profiler])
    assert parse_arguments("main").profiler == profiler


@pytest.mark.unit
def test_parse_iterations_argument(monkeypatch):
    iteration = 500
    monkeypatch.setattr("sys.argv", ["ET", "-n", str(iteration)])
    assert parse_arguments("main").iter == iteration


@pytest.mark.unit
def test_parse_src_file_arguments(monkeypatch):
    src_file_1 = "custom_path_with_smell.py"
    src_file_2 = "custom_path_without_smell.py"
    monkeypatch.setattr("sys.argv", ["ET", "-f1", src_file_1, "-f2", src_file_2])
    args = parse_arguments("main")
    assert args.src_file_1 == src_file_1
    assert args.src_file_2 == src_file_2


@pytest.mark.unit
def test_parse_output_dir_argument(monkeypatch):
    output_dir = "custom_output"
    monkeypatch.setattr("sys.argv", ["ET", "-o", output_dir])
    assert parse_arguments("main").output_dir == output_dir


@pytest.mark.unit
@pytest.mark.parametrize(
    "flag,attr", [("--shuffle", "shuffle"), ("--verbose", "verbose")]
)
def test_parse_flag(monkeypatch, flag, attr):
    monkeypatch.setattr("sys.argv", ["ET", flag])
    assert getattr(parse_arguments("main"), attr)


@pytest.mark.unit
def test_parse_all_arguments(monkeypatch):
    profiler = "carbon"
    iteration = 200
    src_file_1 = "custom_with_smell.py"
    src_file_2 = "custom_without_smell.py"
    output_dir = "custom_output_dir"
    shuffle = True
    verbose = True

    monkeypatch.setattr(
        "sys.argv",
        [
            "ET",
            "-p",
            profiler,
            "-n",
            str(iteration),
            "-f1",
            src_file_1,
            "-f2",
            src_file_2,
            "-o",
            output_dir,
            "--shuffle",
            "--verbose",
        ],
    )

    args = parse_arguments("main")
    assert args.profiler == profiler
    assert args.iter == iteration
    assert args.src_file_1 == src_file_1
    assert args.src_file_2 == src_file_2
    assert args.output_dir == output_dir
    assert args.shuffle == shuffle
    assert args.verbose == verbose


@pytest.mark.unit
@pytest.mark.parametrize("origin", ["main", "analyzer"])
def test_parse_arguments(origin, monkeypatch):
    monkeypatch.setattr("sys.argv", ["ET"])
    with pytest.raises(ValueError):
        parse_arguments(origin="invalid_origin")
    args = parse_arguments(origin=origin)
    assert args is not None


@pytest.mark.unit
def test_parse_arguments_analyzer(monkeypatch):
    path = "output"
    verbose = True
    monkeypatch.setattr("sys.argv", ["ET", "-p", path, "--verbose"])
    args = parse_arguments("analyzer")
    assert args.path == path
    assert args.verbose == verbose
