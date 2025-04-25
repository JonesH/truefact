import os
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_availability_endpoint():
    """Test the availability endpoint."""
    response = client.get("/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert "agentIdentifier" in data
    assert "message" in data

def test_input_schema_endpoint():
    """Test the input schema endpoint."""
    response = client.get("/input_schema")
    assert response.status_code == 200
    data = response.json()
    assert "input_data" in data
    assert len(data["input_data"]) > 0
    assert "id" in data["input_data"][0]
    assert "type" in data["input_data"][0]
    assert "name" in data["input_data"][0]
    assert "data" in data["input_data"][0]

def test_start_job_endpoint():
    """Test the start job endpoint."""
    request_data = {
        "identifier_from_purchaser": "test_purchaser_123",
        "input_data": {
            "text": "Generate a test summary"
        }
    }
    
    response = client.post("/start_job", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "job_id" in data
    assert "blockchainIdentifier" in data
    assert "submitResultTime" in data
    assert "unlockTime" in data
    assert "externalDisputeUnlockTime" in data
    assert "agentIdentifier" in data
    
    # Test status endpoint with the job_id
    job_id = data["job_id"]
    status_response = client.get(f"/status?job_id={job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["awaiting_payment", "running", "completed"]
    
def test_status_endpoint_not_found():
    """Test the status endpoint with a non-existent job ID."""
    response = client.get("/status?job_id=non_existent_id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
