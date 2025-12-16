"""HTTP connection pooling for SocialMapper API requests.

Provides connection pooling to improve performance of repeated
HTTP requests to Census API, Overpass API, and other services.
"""

import logging
import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import PerformanceConfig

logger = logging.getLogger(__name__)

# Global session instance with thread-safe initialization
_http_session: requests.Session | None = None
_http_session_lock = threading.Lock()


class ConnectionPoolManager:
    """Manages HTTP connection pools for API requests.

    Uses requests.Session with connection pooling to reduce
    overhead of creating new connections for each request.

    Parameters
    ----------
    config : PerformanceConfig
        Performance configuration with pool settings.

    Examples
    --------
    >>> from socialmapper.performance import get_performance_config
    >>> config = get_performance_config(preset='fast')
    >>> pool = ConnectionPoolManager(config)
    >>> session = pool.get_session()
    >>> response = session.get('https://api.example.com/data')
    """

    def __init__(self, config: PerformanceConfig | None = None):
        """Initialize connection pool manager.

        Parameters
        ----------
        config : PerformanceConfig, optional
            Performance configuration. Creates balanced config if None.
        """
        if config is None:
            from .config import get_performance_config
            config = get_performance_config(preset='balanced')

        self.config = config
        self._session = self._create_session()

        logger.info(
            f"Initialized ConnectionPoolManager with "
            f"pool_connections={config.http_pool_connections}, "
            f"pool_maxsize={config.http_pool_maxsize}, "
            f"timeout={config.http_timeout_seconds}s"
        )

    def _create_session(self) -> requests.Session:
        """Create a configured requests session.

        Returns
        -------
        requests.Session
            Configured session with connection pooling and retries.
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )

        # Create HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=self.config.http_pool_connections,
            pool_maxsize=self.config.http_pool_maxsize,
            max_retries=retry_strategy,
            pool_block=False
        )

        # Mount adapter for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default timeout
        session.request = self._add_timeout(session.request)

        return session

    def _add_timeout(self, request_method):
        """Add default timeout to requests.

        Parameters
        ----------
        request_method : Callable
            Original request method.

        Returns
        -------
        Callable
            Wrapped request method with timeout.
        """
        def wrapper(*args, **kwargs):
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.config.http_timeout_seconds
            return request_method(*args, **kwargs)
        return wrapper

    def get_session(self) -> requests.Session:
        """Get the configured session.

        Returns
        -------
        requests.Session
            Session with connection pooling enabled.

        Examples
        --------
        >>> pool = ConnectionPoolManager()
        >>> session = pool.get_session()
        >>> response = session.get('https://api.census.gov/data')
        """
        return self._session

    def get(self, url: str, **kwargs) -> requests.Response:
        """Send a GET request using the connection pool.

        Parameters
        ----------
        url : str
            URL to request.
        **kwargs
            Additional arguments passed to requests.get().

        Returns
        -------
        requests.Response
            Response object.

        Examples
        --------
        >>> pool = ConnectionPoolManager()
        >>> response = pool.get('https://api.census.gov/data')
        >>> data = response.json()
        """
        return self._session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Send a POST request using the connection pool.

        Parameters
        ----------
        url : str
            URL to request.
        **kwargs
            Additional arguments passed to requests.post().

        Returns
        -------
        requests.Response
            Response object.

        Examples
        --------
        >>> pool = ConnectionPoolManager()
        >>> response = pool.post('https://overpass-api.de/api/interpreter',
        ...                      data={'data': query})
        >>> data = response.json()
        """
        return self._session.post(url, **kwargs)

    def close(self):
        """Close session and release connections.

        Examples
        --------
        >>> pool = ConnectionPoolManager()
        >>> # ... use pool ...
        >>> pool.close()
        """
        if self._session is not None:
            self._session.close()
            logger.debug("Closed HTTP connection pool")

    def __enter__(self):
        """Context manager entry.

        Returns
        -------
        ConnectionPoolManager
            Self for use in with statements.

        Examples
        --------
        >>> with ConnectionPoolManager() as pool:
        ...     response = pool.get('https://api.example.com')
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def init_connection_pool(config: PerformanceConfig | None = None) -> ConnectionPoolManager:
    """Initialize global connection pool.

    Thread-safe initialization of the global HTTP session.

    Parameters
    ----------
    config : PerformanceConfig, optional
        Performance configuration. Creates balanced config if None.

    Returns
    -------
    ConnectionPoolManager
        Initialized connection pool manager.

    Examples
    --------
    >>> from socialmapper.performance import init_connection_pool
    >>> pool = init_connection_pool()
    >>> session = pool.get_session()
    """
    global _http_session

    pool = ConnectionPoolManager(config)

    with _http_session_lock:
        _http_session = pool.get_session()

    return pool


def get_http_session() -> requests.Session:
    """Get global HTTP session with connection pooling.

    Creates a global session on first call. Subsequent calls
    return the same session instance for connection reuse.

    Thread-safe using double-checked locking pattern for efficiency.

    Returns
    -------
    requests.Session
        Session with connection pooling enabled.

    Examples
    --------
    >>> from socialmapper.performance import get_http_session
    >>> session = get_http_session()
    >>> response = session.get('https://api.census.gov/data')
    """
    global _http_session

    # Fast path: session already exists (no lock needed)
    if _http_session is not None:
        return _http_session

    # Slow path: need to create session (with lock)
    with _http_session_lock:
        # Double-check after acquiring lock
        if _http_session is None:
            pool = ConnectionPoolManager()
            _http_session = pool.get_session()

    return _http_session


def reset_connection_pool():
    """Reset global connection pool.

    Thread-safe reset of the global HTTP session.
    Useful for testing or when connection pool needs to be
    reconfigured with different settings.

    Examples
    --------
    >>> from socialmapper.performance import reset_connection_pool
    >>> reset_connection_pool()
    >>> # Connection pool will be recreated on next use
    """
    global _http_session

    with _http_session_lock:
        if _http_session is not None:
            _http_session.close()
            _http_session = None
            logger.info("Reset global connection pool")
