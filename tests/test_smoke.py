def test_python_version():
    import sys
    assert sys.version_info >= (3, 12)


def test_jac_mcp_available():
    import shutil
    assert shutil.which("jac") is not None, "jac CLI must be on PATH"
