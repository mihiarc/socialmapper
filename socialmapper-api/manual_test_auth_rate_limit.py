#!/usr/bin/env python3
"""Test API authentication and rate limiting functionality.
"""

import asyncio
from datetime import datetime

import httpx

API_BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"


async def test_no_auth():
    """Test API without authentication."""
    print("\n=== Testing API without authentication ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/health")
        print(f"Health check (no auth): {response.status_code}")

        response = await client.get(f"{API_BASE_URL}/api/v1/census/variables")
        print(f"Census variables (no auth): {response.status_code}")

        if response.status_code == 401:
            print(f"Auth error: {response.json()}")


async def test_with_auth():
    """Test API with authentication."""
    print("\n=== Testing API with authentication ===")
    headers = {"X-API-Key": API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/census/variables", headers=headers)
        print(f"Census variables (with auth): {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Successfully retrieved {len(data.get('variables', []))} census variables")
        else:
            print(f"Error: {response.json()}")


async def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n=== Testing rate limiting ===")
    print("Making rapid requests to trigger rate limit...")

    async with httpx.AsyncClient() as client:
        requests_made = 0
        rate_limited = False

        for i in range(70):  # Default limit is 60 per minute
            try:
                response = await client.get(f"{API_BASE_URL}/api/v1/census/variables")
                requests_made += 1

                # Check rate limit headers
                if i == 0:
                    print("\nRate limit headers:")
                    print(f"  X-RateLimit-Limit: {response.headers.get('X-RateLimit-Limit')}")
                    print(f"  X-RateLimit-Remaining: {response.headers.get('X-RateLimit-Remaining')}")

                if response.status_code == 429:
                    rate_limited = True
                    print(f"\nRate limited after {requests_made} requests!")
                    print(f"Status: {response.status_code}")
                    print(f"Retry-After: {response.headers.get('Retry-After')} seconds")
                    print(f"Response: {response.json()}")
                    break

            except Exception as e:
                print(f"Error on request {i+1}: {e}")
                break

        if not rate_limited:
            print(f"\nCompleted {requests_made} requests without rate limiting")


async def test_rate_limit_with_api_key():
    """Test if API key provides higher rate limits."""
    print("\n=== Testing rate limiting with API key ===")
    headers = {"X-API-Key": API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/census/variables", headers=headers)

        if response.status_code == 200:
            print("Rate limit headers with API key:")
            print(f"  X-RateLimit-Limit: {response.headers.get('X-RateLimit-Limit')}")
            print(f"  X-RateLimit-Remaining: {response.headers.get('X-RateLimit-Remaining')}")
            print("Note: In production, API keys could have higher rate limits")


def main():
    """Run all tests."""
    print("SocialMapper API Authentication and Rate Limiting Tests")
    print("=" * 50)
    print(f"API URL: {API_BASE_URL}")
    print(f"Test started at: {datetime.now()}")

    # Run tests
    asyncio.run(test_no_auth())
    asyncio.run(test_with_auth())
    asyncio.run(test_rate_limiting())
    asyncio.run(test_rate_limit_with_api_key())

    print("\n" + "=" * 50)
    print("Tests completed!")
    print("\nNote: To enable authentication, set SOCIALMAPPER_API_AUTH_ENABLED=true")
    print("and SOCIALMAPPER_API_KEYS=test-api-key-123 in your environment")


if __name__ == "__main__":
    main()
