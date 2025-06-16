"""Configuration for census services."""

from dataclasses import dataclass


@dataclass
class CensusConfig:
    """Configuration for census services."""

    api_key: str | None = None
    cache_enabled: bool = True
    cache_ttl: int = 86400  # 24 hours
    rate_limit: float = 10.0  # requests per second
    timeout: int = 60  # seconds
    max_retries: int = 3
