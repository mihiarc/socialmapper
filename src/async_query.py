"""Asynchronous Overpass API wrapper.

Provides a non-blocking alternative to `overpy` for faster queries when the
caller has dozens/hundreds of requests.

Currently uses HTTPX with Overpass API `interpreter` endpoint.
"""
from __future__ import annotations

import asyncio
import os
from typing import List, Dict

import httpx

OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

async def query_overpass_async(query: str, *, timeout: int = 120) -> Dict:
    """Submit a query and return the JSON response as dict."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(OVERPASS_URL, data={"data": query})
        response.raise_for_status()
        return response.json()

# Note: Post-processing (format_results) can remain synchronous because it's CPU-bound and
# negligible relative to network time.  Callers can `await query_overpass_async(...)` and
# then feed the result into existing `format_results`. 