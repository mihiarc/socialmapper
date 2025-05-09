"""Asynchronous helpers for retrieving Census data.

These functions mirror parts of `src.census_data` but leverage `httpx` + `asyncio`
for parallelism, which speeds up multi-state queries.
"""

from __future__ import annotations

import asyncio
import os
from typing import List, Dict, Any, Optional

import httpx
import pandas as pd

from src.util import normalize_census_variable, state_fips_to_abbreviation, STATE_NAMES_TO_ABBR

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
    response = await client.get(base_url, params=params, timeout=30)
    response.raise_for_status()
    json_data = response.json()
    header, *rows = json_data
    df = pd.DataFrame(rows, columns=header)

    # Helpful human-readable state name
    state_name = get_state_name_from_fips(state_code)
    df["STATE_NAME"] = state_name
    return df


def get_state_name_from_fips(fips_code: str) -> str:
    """Utility replicated from census_data to avoid circular import."""
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

    return pd.concat(results, ignore_index=True) 