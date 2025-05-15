"""Asynchronous helpers for retrieving Census data.

These functions mirror parts of `socialmapper.census` but leverage `httpx` + `asyncio`
for parallelism, which speeds up multi-state queries.
"""

from __future__ import annotations

import asyncio
import os
import logging
from typing import List, Optional, Dict, Any

import httpx
import pandas as pd

from socialmapper.util import AsyncRateLimitedClient
from socialmapper.util import rate_limiter
from socialmapper.util import normalize_census_variable, state_fips_to_abbreviation, STATE_NAMES_TO_ABBR
from socialmapper.util import get_census_api_key

# Configure logger
logger = logging.getLogger(__name__)

BASE_URL_TEMPLATE = "https://api.census.gov/data/{year}/{dataset}"


async def _fetch_state(
    client: httpx.AsyncClient,
    state_code: str,
    api_variables: List[str],
    base_url: str,
    api_key: str,
) -> pd.DataFrame:
    """Fetch census data for a single state asynchronously."""
    params = {
        "get": ",".join(api_variables),
        "for": "block group:*",
        "in": f"state:{state_code} county:* tract:*",
        "key": api_key,
    }
    
    try:
        # Apply rate limiting for Census API
        rate_limiter.wait_if_needed("census")
        
        response = await client.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        json_data = response.json()
        header, *rows = json_data
        df = pd.DataFrame(rows, columns=header)

        # Helpful human-readable state name
        state_name = get_state_name_from_fips(state_code)
        df["STATE_NAME"] = state_name
        return df
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning(f"Rate limit exceeded for Census API. Consider reducing request frequency.")
        logger.error(f"HTTP error {e.response.status_code} for state {state_code}: {str(e)}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error for state {state_code}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error for state {state_code}: {str(e)}")
        raise


def get_state_name_from_fips(fips_code: str) -> str:
    """Utility replicated from census to avoid circular import."""
    state_abbr = state_fips_to_abbreviation(fips_code)
    if not state_abbr:
        return fips_code
    for name, abbr in STATE_NAMES_TO_ABBR.items():
        if abbr == state_abbr:
            return name
    return state_abbr


async def fetch_census_data_for_states_async(
    state_fips_list: List[str],
    variables: List[str],
    *,
    year: int = 2021,
    dataset: str = "acs/acs5",
    api_key: Optional[str] = None,
    concurrency: int = 5,  # Reduced default concurrency to avoid rate limits
) -> pd.DataFrame:
    """Asynchronously fetch census data for many states.

    This is a drop-in async alternative to
    `census.fetch_census_data_for_states`.
    """

    if api_key is None:
        api_key = get_census_api_key()
        if not api_key:
            raise ValueError("Census API key missing; set env var or pass api_key.")

    api_variables = [normalize_census_variable(v) for v in variables]
    if "NAME" not in api_variables:
        api_variables.append("NAME")

    base_url = f"{BASE_URL_TEMPLATE.format(year=year, dataset=dataset)}"

    # Use RateLimitedClient with retries and rate limiting to avoid hitting API limits
    async with AsyncRateLimitedClient(
        service="census",
        max_retries=3,
        timeout=30,
        transport=httpx.AsyncHTTPTransport(retries=3)
    ) as client:
        semaphore = asyncio.Semaphore(concurrency)

        async def sem_task(code: str) -> pd.DataFrame:
            async with semaphore:
                try:
                    return await _fetch_state(client, code, api_variables, base_url, api_key)
                except Exception as e:
                    logger.error(f"Failed to fetch census data for state {code}: {str(e)}")
                    # Return empty DataFrame with same structure to avoid breaking the concat
                    return pd.DataFrame(columns=api_variables + ["state", "county", "tract", "block group", "STATE_NAME"])

        tasks = [sem_task(code) for code in state_fips_list]
        results = await asyncio.gather(*tasks)

    # Filter out empty DataFrames
    valid_results = [df for df in results if not df.empty]
    
    if not valid_results:
        logger.error("No valid census data retrieved for any state.")
        # Return an empty DataFrame with the expected columns
        return pd.DataFrame(columns=api_variables + ["state", "county", "tract", "block group", "STATE_NAME"])
        
    return pd.concat(valid_results, ignore_index=True) 