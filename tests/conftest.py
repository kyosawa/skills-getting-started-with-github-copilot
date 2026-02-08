"""Test configuration and fixtures for FastAPI app tests"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        key: {"participants": list(value["participants"])} 
        for key, value in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for key, value in activities.items():
        value["participants"] = original_activities[key]["participants"]
