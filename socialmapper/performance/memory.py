"""Memory optimization utilities for SocialMapper.

Provides tools to reduce memory usage in data processing pipelines,
including DataFrame optimization, lazy loading, and memory profiling.
"""

import gc
import logging
from typing import Any, Iterator

import pandas as pd
import psutil

logger = logging.getLogger(__name__)


def get_memory_stats() -> dict[str, float]:
    """Get current memory usage statistics.

    Returns
    -------
    dict
        Dictionary with memory statistics:
        - 'used_mb': Current memory used by process in MB
        - 'available_mb': Available system memory in MB
        - 'percent': Memory usage percentage
        - 'total_mb': Total system memory in MB

    Examples
    --------
    >>> from socialmapper.performance import get_memory_stats
    >>> stats = get_memory_stats()
    >>> print(f"Memory used: {stats['used_mb']:.1f} MB")
    >>> print(f"Memory available: {stats['available_mb']:.1f} MB")
    >>> print(f"Usage: {stats['percent']:.1f}%")
    """
    process = psutil.Process()
    memory_info = process.memory_info()
    system_memory = psutil.virtual_memory()

    return {
        "used_mb": memory_info.rss / (1024 * 1024),
        "available_mb": system_memory.available / (1024 * 1024),
        "percent": system_memory.percent,
        "total_mb": system_memory.total / (1024 * 1024)
    }


def clear_memory_cache():
    """Clear Python memory cache and trigger garbage collection.

    Forces immediate garbage collection to free up memory.
    Useful after processing large datasets.

    Examples
    --------
    >>> from socialmapper.performance import clear_memory_cache
    >>> # After processing large dataset
    >>> result = process_large_dataset(data)
    >>> clear_memory_cache()  # Free memory
    """
    gc.collect()
    logger.debug("Triggered garbage collection")


def optimize_dataframe_memory(
    df: pd.DataFrame,
    categorical_threshold: int = 50
) -> pd.DataFrame:
    """Optimize DataFrame memory usage by downcasting dtypes.

    Reduces memory footprint by converting columns to more
    efficient data types without losing information.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to optimize.
    categorical_threshold : int, optional
        Convert string columns to categorical if they have fewer
        than this many unique values, by default 50.

    Returns
    -------
    pd.DataFrame
        Optimized DataFrame with reduced memory usage.

    Examples
    --------
    >>> import pandas as pd
    >>> from socialmapper.performance import optimize_dataframe_memory
    >>>
    >>> # Large DataFrame with inefficient dtypes
    >>> df = pd.DataFrame({
    ...     'id': range(10000),
    ...     'value': [1.0] * 10000,
    ...     'category': ['A'] * 5000 + ['B'] * 5000
    ... })
    >>> print(f"Before: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    >>> df_optimized = optimize_dataframe_memory(df)
    >>> print(f"After: {df_optimized.memory_usage(deep=True).sum() / 1024:.1f} KB")
    """
    df = df.copy()
    initial_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)

    # Optimize numeric columns
    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')

    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')

    # Convert string columns to categorical if beneficial
    for col in df.select_dtypes(include=['object']).columns:
        num_unique = df[col].nunique()
        num_total = len(df[col])

        # Convert to categorical if less than threshold unique values
        if num_unique < categorical_threshold and num_unique / num_total < 0.5:
            df[col] = df[col].astype('category')

    final_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
    reduction = ((initial_memory - final_memory) / initial_memory) * 100

    logger.info(
        f"Optimized DataFrame memory: {initial_memory:.2f} MB -> "
        f"{final_memory:.2f} MB ({reduction:.1f}% reduction)"
    )

    return df


def memory_efficient_iterator(
    data: list[Any],
    chunk_size: int = 1000
) -> Iterator[list[Any]]:
    """Create memory-efficient iterator for large datasets.

    Processes data in chunks to avoid loading entire dataset
    into memory at once.

    Parameters
    ----------
    data : list
        List of items to iterate over.
    chunk_size : int, optional
        Number of items per chunk, by default 1000.

    Yields
    ------
    list
        Chunk of items.

    Examples
    --------
    >>> from socialmapper.performance import memory_efficient_iterator
    >>>
    >>> # Process large list in chunks
    >>> large_list = range(100000)
    >>> for chunk in memory_efficient_iterator(large_list, chunk_size=1000):
    ...     result = process_chunk(chunk)
    ...     # Each chunk has max 1000 items
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


class MemoryMonitor:
    """Context manager to monitor memory usage.

    Tracks memory usage before and after a code block,
    reporting the difference.

    Parameters
    ----------
    operation_name : str, optional
        Name of operation being monitored, by default "operation".
    log_level : int, optional
        Logging level for output, by default logging.INFO.

    Examples
    --------
    >>> from socialmapper.performance import MemoryMonitor
    >>>
    >>> with MemoryMonitor("processing large dataset"):
    ...     result = process_large_dataset(data)
    ... # Logs: "processing large dataset: +123.45 MB"
    """

    def __init__(
        self,
        operation_name: str = "operation",
        log_level: int = logging.INFO
    ):
        """Initialize memory monitor.

        Parameters
        ----------
        operation_name : str
            Name of operation being monitored.
        log_level : int
            Logging level for output.
        """
        self.operation_name = operation_name
        self.log_level = log_level
        self.start_memory = 0.0
        self.end_memory = 0.0

    def __enter__(self):
        """Start monitoring memory usage.

        Returns
        -------
        MemoryMonitor
            Self for use in with statements.
        """
        stats = get_memory_stats()
        self.start_memory = stats['used_mb']
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring and report memory usage.

        Parameters
        ----------
        exc_type : type
            Exception type if an exception occurred.
        exc_val : Exception
            Exception value if an exception occurred.
        exc_tb : traceback
            Exception traceback if an exception occurred.

        Returns
        -------
        bool
            False to propagate any exception.
        """
        stats = get_memory_stats()
        self.end_memory = stats['used_mb']
        memory_delta = self.end_memory - self.start_memory

        if memory_delta > 0:
            logger.log(
                self.log_level,
                f"{self.operation_name}: +{memory_delta:.2f} MB memory used"
            )
        else:
            logger.log(
                self.log_level,
                f"{self.operation_name}: {abs(memory_delta):.2f} MB memory freed"
            )

        return False

    @property
    def memory_delta_mb(self) -> float:
        """Get memory usage delta in MB.

        Returns
        -------
        float
            Memory change in MB (positive = increase, negative = decrease).

        Examples
        --------
        >>> with MemoryMonitor("test") as monitor:
        ...     # Do something
        ...     pass
        >>> print(f"Memory change: {monitor.memory_delta_mb:.2f} MB")
        """
        return self.end_memory - self.start_memory


def batch_process_with_memory_limit(
    items: list[Any],
    processor_func: callable,
    memory_limit_mb: float = 1000.0,
    initial_batch_size: int = 100
) -> list[Any]:
    """Process items in batches with automatic memory management.

    Dynamically adjusts batch size to stay within memory limit.
    Monitors memory usage and reduces batch size if limit is exceeded.

    Parameters
    ----------
    items : list
        Items to process.
    processor_func : callable
        Function to process each batch. Should accept a list
        and return a list of results.
    memory_limit_mb : float, optional
        Maximum memory increase allowed in MB, by default 1000.0.
    initial_batch_size : int, optional
        Initial batch size, by default 100.

    Returns
    -------
    list
        Combined results from all batches.

    Examples
    --------
    >>> from socialmapper.performance import batch_process_with_memory_limit
    >>>
    >>> def process_batch(items):
    ...     # Process batch of items
    ...     return [expensive_operation(item) for item in items]
    >>>
    >>> items = range(10000)
    >>> results = batch_process_with_memory_limit(
    ...     items,
    ...     process_batch,
    ...     memory_limit_mb=500.0
    ... )
    """
    results = []
    batch_size = initial_batch_size
    current_idx = 0

    while current_idx < len(items):
        # Get memory before processing
        start_stats = get_memory_stats()
        start_memory = start_stats['used_mb']

        # Process batch
        batch = items[current_idx:current_idx + batch_size]
        batch_results = processor_func(batch)
        results.extend(batch_results)

        # Check memory after processing
        end_stats = get_memory_stats()
        end_memory = end_stats['used_mb']
        memory_increase = end_memory - start_memory

        # Adjust batch size based on memory usage
        if memory_increase > memory_limit_mb * 0.8:
            # Approaching limit - reduce batch size
            old_batch_size = batch_size
            batch_size = max(1, batch_size // 2)
            logger.info(
                f"Reducing batch size: {old_batch_size} -> {batch_size} "
                f"(memory increase: {memory_increase:.1f} MB)"
            )
            # Trigger garbage collection
            clear_memory_cache()
        elif memory_increase < memory_limit_mb * 0.2 and batch_size < initial_batch_size * 2:
            # Well below limit - can increase batch size
            batch_size = min(initial_batch_size * 2, batch_size * 2)
            logger.debug(f"Increasing batch size to {batch_size}")

        current_idx += len(batch)

    return results
