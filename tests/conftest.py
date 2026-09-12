"""Fresh production runtime per test, without any device connections."""

import pytest

from tests.runtime_loader import load_runtime


@pytest.fixture
def runtime():
    """Reset fake drivers while exercising the unmodified production classes."""
    return load_runtime()
