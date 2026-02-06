"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check"""
    
    def test_health_check(self, client):
        """Test health endpoint returns healthy status"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "tools_available" in data


class TestArticlesEndpoints:
    """Tests for articles API"""
    
    def test_get_articles_empty(self, client):
        """Test getting articles when none exist"""
        response = client.get("/api/v1/articles")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["articles"] == []
    
    def test_get_article_not_found(self, client):
        """Test getting non-existent article"""
        response = client.get("/api/v1/articles/999")
        
        assert response.status_code == 404


class TestSourcesEndpoints:
    """Tests for sources API"""
    
    def test_get_sources_empty(self, client):
        """Test getting sources when none exist"""
        response = client.get("/api/v1/sources")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_create_source_invalid_url(self, client):
        """Test creating source with invalid URL"""
        response = client.post("/api/v1/sources", json={
            "name": "Test",
            "url": "not-a-url",
            "category": "Test"
        })
        
        # Should validate URL format
        assert response.status_code == 422  # Validation error


class TestPipelineEndpoints:
    """Tests for pipeline API"""
    
    def test_run_pipeline_invalid_type(self, client):
        """Test running pipeline with invalid type"""
        response = client.post("/api/v1/pipeline/invalid_type")
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestConfigEndpoint:
    """Tests for config API"""
    
    def test_get_config(self, client):
        """Test getting configuration"""
        response = client.get("/api/v1/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "llm_provider" in data
