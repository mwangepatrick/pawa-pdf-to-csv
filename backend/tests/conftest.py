import asyncio
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory structure."""
    uploads = tmp_path / "uploads"
    outputs = tmp_path / "outputs"
    uploads.mkdir()
    outputs.mkdir()
    return tmp_path


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
