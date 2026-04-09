import pytest

from src.runners.python_runner import PythonRunner


@pytest.mark.unit
def test_language_property():
    runner = PythonRunner()
    assert runner.language == "python"


@pytest.mark.unit
def test_run_prepared_without_prepare_raises():
    runner = PythonRunner()
    with pytest.raises(RuntimeError, match="prepared"):
        runner.run_prepared()


@pytest.mark.unit
def test_prepare_then_run_prepared_executes_code(capsys):
    runner = PythonRunner()
    runner.prepare("print('python_runner_ok')")

    runner.run_prepared()

    captured = capsys.readouterr()
    assert "python_runner_ok" in captured.out


@pytest.mark.unit
def test_cleanup_clears_prepared_code():
    runner = PythonRunner()
    runner.prepare("print('ignored')")

    runner.cleanup()

    with pytest.raises(RuntimeError, match="prepared"):
        runner.run_prepared()


@pytest.mark.unit
def test_prepare_overwrites_previous_code(capsys):
    runner = PythonRunner()
    runner.prepare("print('first')")
    runner.prepare("print('second')")

    runner.run_prepared()

    captured = capsys.readouterr()
    assert "second" in captured.out
    assert "first" not in captured.out
