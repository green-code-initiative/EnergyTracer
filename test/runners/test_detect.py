import pytest

from src.runners.detect import (
    get_language_for,
    runner_for,
)

# Fixtures for test files


@pytest.fixture
def java_file(tmp_path):
    file = tmp_path / "WithSmell.java"
    file.write_text("""public class WithSmell {}""")
    return str(file)


@pytest.fixture
def python_file(tmp_path):
    file = tmp_path / "with_smell.py"
    file.write_text("")
    return str(file)


@pytest.fixture
def invalid_file(tmp_path):
    file = tmp_path / "invalid.txt"
    file.write_text("This is not a valid source file.")
    return str(file)


# Test cases for detect.py


@pytest.mark.unit
@pytest.mark.parametrize(
    ("src_fixture", "expected_language"),
    [("java_file", "java"), ("python_file", "python")],
)
def test_runner_for_valid_files(src_fixture, expected_language, request):
    src_file = request.getfixturevalue(src_fixture)
    runner = runner_for(src_file)
    assert runner is not None
    assert runner.language == expected_language
    assert get_language_for(src_file) == expected_language


@pytest.mark.unit
@pytest.mark.parametrize("src_fixture", ["invalid_file"])
def test_runner_for_invalid_files(src_fixture, request):
    src_file = request.getfixturevalue(src_fixture)
    with pytest.raises(ValueError):
        runner_for(src_file)


@pytest.mark.unit
@pytest.mark.parametrize("src_fixture", ["invalid_file"])
def test_get_language_for_invalid_files(src_fixture, request):
    src_file = request.getfixturevalue(src_fixture)
    with pytest.raises(ValueError):
        get_language_for(src_file)
