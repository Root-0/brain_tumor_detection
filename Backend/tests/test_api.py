import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import io
import pytest
from fastapi.testclient import TestClient
from brain_tumor_detection.Backend.api.main import app

client = TestClient(app)

# Fixtures for test user credentials
def test_user():
    return {"username": "testuser", "email": "testuser@example.com", "password": "testpass123"}

@pytest.fixture
def auth_token():
    test_user_data = test_user()
    # Register user (ignore if already exists)
    client.post("/api/auth/register", json=test_user_data)
    # Login and get token
    response = client.post("/api/auth/token", data={"username": test_user_data["username"], "password": test_user_data["password"]})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_register_and_login():
    test_user_data = test_user()
    # Register
    reg_resp = client.post("/api/auth/register", json=test_user_data)
    assert reg_resp.status_code in [200, 400]  # 400 if already registered
    # Login
    login_resp = client.post("/api/auth/token", data={"username": test_user_data["username"], "password": test_user_data["password"]})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

def test_upload_scan(auth_token):
    # Simulate file upload (use a small dummy file)
    file_content = b"dummy mri data"
    files = {"file": ("test.nii", io.BytesIO(file_content), "application/octet-stream")}
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/predict", files=files, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "scan_id" in data
    assert data["status"] == "processing"

def test_scan_history(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/users/scans", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_scan_result_polling(auth_token):
    # Upload a scan first
    file_content = b"dummy mri data"
    files = {"file": ("test2.nii", io.BytesIO(file_content), "application/octet-stream")}
    headers = {"Authorization": f"Bearer {auth_token}"}
    upload_resp = client.post("/api/predict", files=files, headers=headers)
    assert upload_resp.status_code == 200
    scan_id = upload_resp.json()["scan_id"]
    # Poll result
    result_resp = client.get(f"/api/predict/{scan_id}", headers=headers)
    assert result_resp.status_code == 200
    assert "status" in result_resp.json()
    assert result_resp.json()["scan_id"] == scan_id
