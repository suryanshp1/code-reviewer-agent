"""Comprehensive end-to-end tests for Code Reviewer CI Agent.

This module tests the complete application flow including:
- Service health and configuration
- API authentication and authorization
- Rate limiting
- Code review functionality with real LLM calls
- Guardrails and validation
- Error handling
"""

import json
import os
import time
from typing import Dict, Any

import pytest
from httpx import AsyncClient, ASGITransport
from app.api import app
from app.config import config
from tests.fixtures.test_diffs import TEST_DIFFS


# Test configuration
BASE_URL = "http://test"
VALID_API_KEY = config.review_api_key
INVALID_API_KEY = "invalid-key-12345"


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Get valid authorization headers."""
    return {
        "Authorization": f"Bearer {VALID_API_KEY}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def invalid_auth_headers() -> Dict[str, str]:
    """Get invalid authorization headers."""
    return {
        "Authorization": f"Bearer {INVALID_API_KEY}",
        "Content-Type": "application/json"
    }


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test that health check endpoint returns correct status."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "version" in data
    assert "llm_provider" in data
    assert data["llm_provider"] in ["openai", "groq"]
    assert "ray_serve_enabled" in data


@pytest.mark.asyncio
async def test_health_check_configuration(client: AsyncClient):
    """Test that health check exposes correct configuration."""
    response = await client.get("/health")
    data = response.json()
    
    # Verify LLM provider matches configuration
    assert data["llm_provider"] == config.llm_provider
    assert data["ray_serve_enabled"] == config.enable_ray_serve


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_review_with_valid_api_key(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test that valid API key is accepted."""
    request_data = {
        "diff": TEST_DIFFS["clean_code"],
        "language": "python",
        "context": {
            "repo": "test/repo",
            "commit_sha": "abc123",
            "pr_number": 1,
            "author": "testuser"
        }
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers)
    
    # Should not be unauthorized
    assert response.status_code != 401
    # May be 200 or timeout depending on LLM response
    assert response.status_code in [200, 504, 500]


@pytest.mark.asyncio
async def test_review_with_invalid_api_key(client: AsyncClient, invalid_auth_headers: Dict[str, str]):
    """Test that invalid API key is rejected."""
    request_data = {
        "diff": TEST_DIFFS["clean_code"],
        "language": "python",
        "context": {}
    }
    
    response = await client.post("/review", json=request_data, headers=invalid_auth_headers)
    
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "Invalid API key" in data["error"]


@pytest.mark.asyncio
async def test_review_without_auth_header(client: AsyncClient):
    """Test that missing authorization header is rejected."""
    request_data = {
        "diff": TEST_DIFFS["clean_code"],
        "language": "python",
        "context": {}
    }
    
    response = await client.post("/review", json=request_data)
    
    assert response.status_code == 403


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test that rate limiting is enforced."""
    request_data = {
        "diff": TEST_DIFFS["clean_code"],
        "language": "python",
        "context": {}
    }
    
    # Make requests up to the limit
    rate_limit = config.rate_limit_per_minute
    responses = []
    
    for i in range(rate_limit + 2):
        response = await client.post("/review", json=request_data, headers=auth_headers)
        responses.append(response.status_code)
        
        # Small delay to avoid overwhelming
        if i < rate_limit:
            await asyncio.sleep(0.1)
    
    # At least one request should be rate limited
    assert 429 in responses


# ============================================================================
# CODE REVIEW FUNCTIONALITY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_review_sql_injection_detection(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test that SQL injection vulnerability is detected."""
    request_data = {
        "diff": TEST_DIFFS["sql_injection"],
        "language": "python",
        "context": {
            "repo": "test/security",
            "commit_sha": "sec001",
            "pr_number": 100,
            "author": "developer"
        }
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers, timeout=180.0)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "findings" in data
    assert "summary" in data
    assert "score" in data
    assert "metadata" in data
    
    # Verify findings
    findings = data["findings"]
    assert len(findings) > 0
    
    # Check that security issue is detected
    security_findings = [f for f in findings if f["category"] == "security"]
    assert len(security_findings) > 0
    
    # Verify at least one finding mentions SQL or injection
    finding_texts = " ".join([f["message"] + " " + f.get("suggestion", "") for f in security_findings])
    assert any(keyword in finding_texts.lower() for keyword in ["sql", "injection", "parameterized", "query"])


@pytest.mark.asyncio
async def test_review_response_structure(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test that review response has the correct structure."""
    request_data = {
        "diff": TEST_DIFFS["clean_code"],
        "language": "python",
        "context": {}
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers, timeout=180.0)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify top-level fields
    assert "summary" in data
    assert "score" in data
    assert "findings" in data
    assert "metadata" in data
    
    # Verify score is in valid range
    assert 0 <= data["score"] <= 10
    
    # Verify metadata structure
    metadata = data["metadata"]
    assert "execution_time_ms" in metadata
    assert "tokens_used" in metadata
    assert "agent_count" in metadata
    assert "model" in metadata
    
    # Verify findings structure (if any)
    if data["findings"]:
        finding = data["findings"][0]
        assert "category" in finding
        assert "severity" in finding
        assert "message" in finding
        assert finding["category"] in ["security", "performance", "quality", "style"]
        assert finding["severity"] in ["low", "medium", "high", "critical"]


@pytest.mark.asyncio
async def test_review_multiple_issues_detection(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test detection of multiple issues in a single diff."""
    request_data = {
        "diff": TEST_DIFFS["multiple_issues"],
        "language": "python",
        "context": {}
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers, timeout=180.0)
    
    assert response.status_code == 200
    data = response.json()
    
    findings = data["findings"]
    
    # Should detect multiple issues
    assert len(findings) >= 2
    
    # Should have different categories
    categories = set(f["category"] for f in findings)
    assert len(categories) > 1


@pytest.mark.asyncio
async def test_review_performance_timing(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test that review completes within acceptable time."""
    request_data = {
        "diff": TEST_DIFFS["clean_code"],
        "language": "python",
        "context": {}
    }
    
    start_time = time.time()
    response = await client.post("/review", json=request_data, headers=auth_headers, timeout=180.0)
    duration = time.time() - start_time
    
    assert response.status_code == 200
    data = response.json()
    
    # Should complete within timeout (120s default + buffer)
    assert duration < 150
    
    # Metadata should reflect execution time
    reported_time_ms = data["metadata"]["execution_time_ms"]
    assert reported_time_ms > 0
    assert reported_time_ms < 150000  # 150 seconds in ms


# ============================================================================
# GUARDRAILS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_review_with_invalid_diff(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test handling of invalid diff format."""
    request_data = {
        "diff": "This is not a valid diff format",
        "language": "python",
        "context": {}
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers, timeout=180.0)
    
    # Should either accept it (agents will analyze) or return error
    assert response.status_code in [200, 400, 422, 500]


@pytest.mark.asyncio
async def test_review_with_empty_diff(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test handling of empty diff."""
    request_data = {
        "diff": "",
        "language": "python",
        "context": {}
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers, timeout=180.0)
    
    # Should handle gracefully
    assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_review_findings_limit(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test that findings are limited by guardrails."""
    request_data = {
        "diff": TEST_DIFFS["multiple_issues"],
        "language": "python",
        "context": {}
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers, timeout=180.0)
    
    if response.status_code == 200:
        data = response.json()
        findings = data["findings"]
        
        # Should not exceed max findings limit
        assert len(findings) <= config.max_findings_per_review


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_review_with_missing_fields(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test handling of request with missing required fields."""
    request_data = {
        "language": "python"
        # Missing 'diff' field
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers)
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_review_with_invalid_language(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test handling of unsupported language."""
    request_data = {
        "diff": TEST_DIFFS["clean_code"],
        "language": "invalid-language-xyz",
        "context": {}
    }
    
    response = await client.post("/review", json=request_data, headers=auth_headers, timeout=180.0)
    
    # Should either accept it or validate
    assert response.status_code in [200, 400, 422]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_full_review_workflow(client: AsyncClient, auth_headers: Dict[str, str]):
    """Test complete end-to-end review workflow."""
    # 1. Check health
    health_response = await client.get("/health")
    assert health_response.status_code == 200
    
    # 2. Submit review with security issue
    review_request = {
        "diff": TEST_DIFFS["sql_injection"],
        "language": "python",
        "context": {
            "repo": "test/integration",
            "commit_sha": "int001",
            "pr_number": 999,
            "author": "integration-test"
        }
    }
    
    review_response = await client.post(
        "/review", 
        json=review_request, 
        headers=auth_headers,
        timeout=180.0
    )
    
    assert review_response.status_code == 200
    review_data = review_response.json()
    
    # 3. Verify complete response
    assert "findings" in review_data
    assert "summary" in review_data
    assert "score" in review_data
    assert review_data["score"] >= 0
    
    # 4. Verify security findings present
    security_findings = [
        f for f in review_data["findings"] 
        if f["category"] == "security"
    ]
    assert len(security_findings) > 0
    
    print(f"\n✅ Full workflow test passed!")
    print(f"   - Findings: {len(review_data['findings'])}")
    print(f"   - Security issues: {len(security_findings)}")
    print(f"   - Quality score: {review_data['score']:.1f}/10")
    print(f"   - Execution time: {review_data['metadata']['execution_time_ms']}ms")


# Add asyncio support
import asyncio

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
