from pathlib import Path

import pytest

from src.runners.java_runner import JavaRunner


@pytest.mark.unit
def test_language_property():
    runner = JavaRunner()
    assert runner.language == "java"


@pytest.mark.unit
def test_prepare_and_run_prepared_with_package(tmp_path, monkeypatch):
    calls = []

    class FakeTempDir:
        def __init__(self, name: str):
            self.name = name

        def cleanup(self):
            return None

    monkeypatch.setattr(
        "src.runners.java_runner.tempfile.TemporaryDirectory",
        lambda: FakeTempDir(str(tmp_path)),
    )

    def fake_which(binary: str):
        if binary == "javac":
            return "/usr/bin/javac"
        if binary == "java":
            return "/usr/bin/java"
        return None

    monkeypatch.setattr("src.runners.java_runner.shutil.which", fake_which)

    def fake_run(cmd, cwd=None, check=None):
        calls.append((cmd, cwd, check))

    monkeypatch.setattr("src.runners.java_runner.subprocess.run", fake_run)

    code = """package examples.java;

public class MySample {
	public static void main(String[] args) {}
}
"""

    runner = JavaRunner()
    runner.prepare(code)

    expected_src = tmp_path / "examples" / "java" / "MySample.java"
    assert expected_src.exists()
    assert expected_src.read_text() == code

    assert calls[0][0][0] == "/usr/bin/javac"
    assert calls[0][0][1] == str(expected_src)
    assert Path(calls[0][1]) == tmp_path
    assert calls[0][2] is True

    runner.run_prepared()
    assert calls[1][0] == [
        "/usr/bin/java",
        "-cp",
        str(tmp_path),
        "examples.java.MySample",
    ]
    assert calls[1][1] == str(tmp_path)
    assert calls[1][2] is True


@pytest.mark.unit
def test_prepare_requires_public_class():
    runner = JavaRunner()
    code = "class MissingPublicClass {}"
    with pytest.raises(ValueError, match="public class"):
        runner.prepare(code)


@pytest.mark.unit
def test_prepare_requires_java_toolchain(monkeypatch):
    monkeypatch.setattr("src.runners.java_runner.shutil.which", lambda _name: None)
    runner = JavaRunner()
    code = "public class Main {}"
    with pytest.raises(RuntimeError, match="Java toolchain"):
        runner.prepare(code)


@pytest.mark.unit
def test_run_prepared_without_prepare_raises():
    runner = JavaRunner()
    with pytest.raises(RuntimeError, match="prepared"):
        runner.run_prepared()


@pytest.mark.unit
def test_cleanup_resets_internal_state(tmp_path, monkeypatch):
    class FakeTempDir:
        def __init__(self, name: str):
            self.name = name
            self.cleaned = False

        def cleanup(self):
            self.cleaned = True

    fake_tmp = FakeTempDir(str(tmp_path))
    monkeypatch.setattr(
        "src.runners.java_runner.tempfile.TemporaryDirectory",
        lambda: fake_tmp,
    )
    monkeypatch.setattr(
        "src.runners.java_runner.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )
    monkeypatch.setattr(
        "src.runners.java_runner.subprocess.run", lambda *args, **kwargs: None
    )

    runner = JavaRunner()
    runner.prepare("public class Main {}")
    assert runner._tmpdir is not None

    runner.cleanup()
    assert fake_tmp.cleaned is True
    assert runner._tmpdir is None
    assert runner._java_path is None
    assert runner._qualified_class_name_cache is None
