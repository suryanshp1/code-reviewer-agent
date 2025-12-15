"""Deployment verification script for Hugging Face Space.

This script verifies that the deployed application is working correctly
by testing the health endpoint and optionally a sample review.
"""

import argparse
import json
import sys
import time
from typing import Optional

import httpx


def verify_health(base_url: str) -> bool:
    """Verify the health endpoint is responding correctly."""
    health_url = f"{base_url}/health"
    
    print(f"🔍 Checking health endpoint: {health_url}")
    
    try:
        response = httpx.get(health_url, timeout=10.0)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"✅ Health check passed!")
        print(f"   Status: {data.get('status')}")
        print(f"   Version: {data.get('version')}")
        print(f"   LLM Provider: {data.get('llm_provider')}")
        print(f"   Ray Serve: {data.get('ray_serve_enabled')}")
        
        return True
        
    except httpx.HTTPError as e:
        print(f"❌ Health check failed: {e}")
        return False


def verify_review(base_url: str, api_key: Optional[str] = None) -> bool:
    """Verify the review endpoint with a sample request."""
    if not api_key:
        print("⚠️  Skipping review test (no API key provided)")
        return True
    
    review_url = f"{base_url}/review"
    
    # Simple test diff
    sample_request = {
        "diff": """diff --git a/test.py b/test.py
+def example():
+    return "Hello, World!"
""",
        "language": "python",
        "context": {
            "repo": "test/deployment-verification",
            "commit_sha": "verify001",
            "pr_number": 0
        }
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 Testing review endpoint: {review_url}")
    print(f"⏳ This may take 15-45 seconds...")
    
    try:
        start_time = time.time()
        response = httpx.post(
            review_url,
            json=sample_request,
            headers=headers,
            timeout=120.0
        )
        duration = time.time() - start_time
        
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Review completed in {duration:.1f}s")
        print(f"   Findings: {len(data.get('findings', []))}")
        print(f"   Quality Score: {data.get('score', 0):.1f}/10")
        print(f"   Execution Time: {data.get('metadata', {}).get('execution_time_ms', 0)}ms")
        
        return True
        
    except httpx.HTTPError as e:
        print(f"❌ Review test failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"   Error details: {error_data.get('error', 'Unknown error')}")
            except:
                pass
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Verify Hugging Face Space deployment"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of the deployed Space (e.g., https://username-spacename.hf.space)"
    )
    parser.add_argument(
        "--api-key",
        help="API key for testing review endpoint (optional)"
    )
    parser.add_argument(
        "--skip-review",
        action="store_true",
        help="Skip review endpoint test"
    )
    
    args = parser.parse_args()
    
    base_url = args.url.rstrip('/')
    
    print("=" * 60)
    print("🚀 Hugging Face Deployment Verification")
    print("=" * 60)
    print(f"Target: {base_url}\n")
    
    # Test health endpoint
    health_ok = verify_health(base_url)
    
    if not health_ok:
        print("\n❌ Deployment verification failed!")
        sys.exit(1)
    
    # Test review endpoint if requested
    review_ok = True
    if not args.skip_review and args.api_key:
        review_ok = verify_review(base_url, args.api_key)
    
    print("\n" + "=" * 60)
    if health_ok and review_ok:
        print("✅ All verification checks passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Some verification checks failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
