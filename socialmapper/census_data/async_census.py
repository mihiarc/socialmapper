"""Asynchronous helpers for retrieving Census data.

These functions mirror parts of `src.census_data` but leverage `httpx` + `asyncio`
for parallelism, which speeds up multi-state queries.
"""

from __future__ import annotations

import asyncio
import os
import logging
from typing import List, Optional

import httpx
import pandas as pd

from socialmapper.util import normalize_census_variable
from socialmapper.states import state_fips_to_name, STATE_NAMES_TO_ABBR

# Add a logger for this module
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
    
    # Log the request at DEBUG level so it won't show in normal INFO mode
    state_name = get_state_name_from_fips(state_code)
    logger.debug(f"Fetching census data for {state_name} (FIPS: {state_code})")
    
    response = await client.get(base_url, params=params, timeout=30)
    response.raise_for_status()
    json_data = response.json()
    header, *rows = json_data
    df = pd.DataFrame(rows, columns=header)

    # Helpful human-readable state name
    df["STATE_NAME"] = state_name
    logger.debug(f"Retrieved {len(df)} block groups for {state_name}")
    return df


def get_state_name_from_fips(fips_code: str) -> str:
    """Utility replicated from census_data to avoid circular import."""
    state_name = state_fips_to_name(fips_code)
    if not state_name:
        return fips_code
    return state_name


async def fetch_census_data_for_states_async(
    state_fips_list: List[str],
    variables: List[str],
    *,
    year: int = 2021,
    dataset: str = "acs/acs5",
    api_key: Optional[str] = None,
    concurrency: int = 10,
) -> pd.DataFrame:
    """Asynchronously fetch census data for many states.

    This is a drop-in async alternative to
    `census_data.fetch_census_data_for_states`.
    """

    if api_key is None:
        api_key = os.getenv("CENSUS_API_KEY")
        if not api_key:
            raise ValueError("Census API key missing; set env var or pass api_key.")

    api_variables = [normalize_census_variable(v) for v in variables]
    if "NAME" not in api_variables:
        api_variables.append("NAME")

    base_url = f"{BASE_URL_TEMPLATE.format(year=year, dataset=dataset)}"

    connector = httpx.AsyncHTTPTransport(retries=3)
    async with httpx.AsyncClient(transport=connector, timeout=30) as client:
        semaphore = asyncio.Semaphore(concurrency)

        async def sem_task(code: str):
            async with semaphore:
                return await _fetch_state(client, code, api_variables, base_url, api_key)

        results = await asyncio.gather(*(sem_task(code) for code in state_fips_list))

    # Combine results into a single DataFrame
    if not results:
        # Return empty DataFrame with correct columns if no results
        return pd.DataFrame(columns=api_variables + ['state', 'county', 'tract', 'block group'])

    final_df = pd.concat(results, ignore_index=True)
    
    # Create a GEOID column to match with GeoJSON - ensure proper formatting with leading zeros
    final_df['GEOID'] = (
        final_df['state'].str.zfill(2) + 
        final_df['county'].str.zfill(3) + 
        final_df['tract'].str.zfill(6) + 
        final_df['block group']
    )
    
    return final_df 