# pruebas/test_api.py
"""
Pruebas para la API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.api.principal import app

client = TestClient(app)

class TestAPI:
    def test_health(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_predict(self):
        data = {
            "id_cliente": "CL001",
            "consumo_promedio": 150.5,
            "total_alarmas": 3
        }
        response = client.post("/api/v1/predict", json=data)
        assert response.status_code == 200
        assert "probabilidad" in response.json()