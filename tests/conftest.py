import pytest
import os
import tempfile
from pathlib import Path

@pytest.fixture(scope="session")
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture(scope="session")
def test_data_dir():
    return Path(__file__).parent / "test_data"

@pytest.fixture(scope="session")
def sample_docx_path(test_data_dir):
    return test_data_dir / "sample.docx"

@pytest.fixture(scope="session")
def sample_pdf_path(test_data_dir):
    return test_data_dir / "sample.pdf"

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, temp_dir):
    # Set up test environment variables
    monkeypatch.setenv("CACHE_DIR", str(temp_dir / "tts_cache"))
    monkeypatch.setenv("UPLOAD_DIR", str(temp_dir / "uploads"))
    monkeypatch.setenv("MAX_WORKERS", "2")
    
    # Create necessary directories
    os.makedirs(temp_dir / "tts_cache", exist_ok=True)
    os.makedirs(temp_dir / "uploads", exist_ok=True)
    
    yield
    
    # Cleanup (handled by tempfile.TemporaryDirectory) 