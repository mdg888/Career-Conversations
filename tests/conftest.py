"""
Pytest configuration and fixtures for test suite
"""
import os
import pytest

# Set environment variables before any imports
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
os.environ.setdefault("PUSHOVER_TOKEN", "test-pushover-token")
os.environ.setdefault("PUSHOVER_USER", "test-pushover-user")


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Automatically set up environment variables for all tests"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("PUSHOVER_TOKEN", "test-pushover-token")
    monkeypatch.setenv("PUSHOVER_USER", "test-pushover-user")
