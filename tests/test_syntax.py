#!/usr/bin/env python3
"""Test that the main script has valid Python syntax."""

import os
import py_compile

import pytest


def test_main_script_syntax():
    """Test that dbus-virtual-battery.py can be compiled without syntax errors."""
    script_path = os.path.join(
        os.path.dirname(__file__), "..", "dbus-virtual-battery.py"
    )
    try:
        py_compile.compile(script_path, doraise=True)
    except py_compile.PyCompileError as e:
        pytest.fail(f"Syntax error in {script_path}: {e}")


if __name__ == "__main__":
    test_main_script_syntax()
    print("All tests passed!")
