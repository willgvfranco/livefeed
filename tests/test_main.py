from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestMain:
    def test_read_root_status_code(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "LiveFeed Backend is running"}

    def test_read_root_content_type(self):
        response = client.get("/")
        assert response.headers["Content-Type"] == "application/json"
