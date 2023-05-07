from .. import get_compatible


def test_runtimes():
    assert get_compatible.get_compatible_runtimes("p3.8") == ["python3.8"]
    assert get_compatible.get_compatible_runtimes("p3.10") == ["python3.10"]
    assert get_compatible.get_compatible_runtimes("p3.10-arm64") == ["python3.10"]
    assert get_compatible.get_compatible_runtimes("p3.10-x86") == ["python3.10"]


def test_architecture():
    assert get_compatible.get_compatible_architectures("p3.8") == ["x86_64"]
    assert get_compatible.get_compatible_architectures("p3.10") == ["x86_64"]
    assert get_compatible.get_compatible_architectures("p3.10-arm64") == ["arm64"]
    assert get_compatible.get_compatible_architectures("p3.10-x86") == ["x86_64"]
