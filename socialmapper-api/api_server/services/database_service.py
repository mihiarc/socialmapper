"""Database service with connection pooling and query optimization."""

import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, UTC

import asyncpg
from asyncpg import Pool, Connection, Record

from ..config import get_settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """PostgreSQL database service with connection pooling and optimizations."""
    
    def __init__(
        self,
        dsn: Optional[str] = None,
        host: str = "localhost",
        port: int = 5432,
        database: str = "socialmapper",
        user: str = "postgres",
        password: Optional[str] = None,
        min_pool_size: int = 10,
        max_pool_size: int = 50,
        command_timeout: float = 10.0,
        max_inactive_connection_lifetime: float = 300.0
    ):
        """Initialize database service with connection pool.
        
        Args:
            dsn: Database connection string (overrides other params)
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_pool_size: Minimum connections in pool
            max_pool_size: Maximum connections in pool
            command_timeout: Command timeout in seconds
            max_inactive_connection_lifetime: Max idle time for connections
        """
        self.dsn = dsn
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.command_timeout = command_timeout
        self.max_inactive_connection_lifetime = max_inactive_connection_lifetime
        
        self.pool: Optional[Pool] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection pool and create tables."""
        if self._initialized:
            return
        
        try:
            # Create connection pool
            if self.dsn:
                self.pool = await asyncpg.create_pool(
                    self.dsn,
                    min_size=self.min_pool_size,
                    max_size=self.max_pool_size,
                    command_timeout=self.command_timeout,
                    max_inactive_connection_lifetime=self.max_inactive_connection_lifetime
                )
            else:
                self.pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    min_size=self.min_pool_size,
                    max_size=self.max_pool_size,
                    command_timeout=self.command_timeout,
                    max_inactive_connection_lifetime=self.max_inactive_connection_lifetime
                )
            
            # Create tables and indexes
            await self._create_tables()
            await self._create_indexes()
            
            self._initialized = True
            logger.info(f"Database service initialized with pool size {self.min_pool_size}-{self.max_pool_size}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database service not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        async with self.acquire() as conn:
            # Jobs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id VARCHAR(36) PRIMARY KEY,
                    status VARCHAR(20) NOT NULL,
                    priority INTEGER DEFAULT 10,
                    session_id VARCHAR(36),
                    location VARCHAR(255) NOT NULL,
                    poi_type VARCHAR(100) NOT NULL,
                    poi_name VARCHAR(100) NOT NULL,
                    travel_time INTEGER NOT NULL,
                    geographic_level VARCHAR(50) NOT NULL,
                    census_variables TEXT[],
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    started_at TIMESTAMPTZ,
                    completed_at TIMESTAMPTZ,
                    processing_time_seconds FLOAT,
                    progress FLOAT DEFAULT 0.0,
                    message TEXT,
                    error TEXT,
                    error_details JSONB,
                    result JSONB,
                    is_demo BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    job_count INTEGER DEFAULT 0,
                    total_processing_time FLOAT DEFAULT 0.0,
                    is_demo BOOLEAN DEFAULT FALSE,
                    metadata JSONB
                )
            """)
            
            # Cache entries table (backup for Redis)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key VARCHAR(255) PRIMARY KEY,
                    value JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    category VARCHAR(50) NOT NULL
                )
            """)
            
            # Performance metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    metric_type VARCHAR(50) NOT NULL,
                    value FLOAT NOT NULL,
                    metadata JSONB
                )
            """)
            
            # Feedback table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    job_id VARCHAR(36),
                    session_id VARCHAR(36),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    metadata JSONB
                )
            """)
            
            logger.info("Database tables created successfully")
    
    async def _create_indexes(self):
        """Create database indexes for optimal query performance."""
        async with self.acquire() as conn:
            # Jobs indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status 
                ON jobs(status)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_session_id 
                ON jobs(session_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_created_at 
                ON jobs(created_at DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_location_poi 
                ON jobs(location, poi_type, poi_name)
            """)
            
            # Sessions indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_last_activity 
                ON sessions(last_activity DESC)
            """)
            
            # Cache indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires_at 
                ON cache_entries(expires_at)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_category 
                ON cache_entries(category)
            """)
            
            # Performance metrics indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON performance_metrics(timestamp DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_type 
                ON performance_metrics(metric_type)
            """)
            
            logger.info("Database indexes created successfully")
    
    async def save_job(self, job: Dict[str, Any]) -> bool:
        """Save or update a job in the database.
        
        Args:
            job: Job data dictionary
            
        Returns:
            True if successful
        """
        try:
            async with self.acquire() as conn:
                await conn.execute("""
                    INSERT INTO jobs (
                        id, status, priority, session_id, location,
                        poi_type, poi_name, travel_time, geographic_level,
                        census_variables, created_at, started_at, completed_at,
                        processing_time_seconds, progress, message, error,
                        error_details, result, is_demo
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                             $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    ON CONFLICT (id) DO UPDATE SET
                        status = $2,
                        started_at = $12,
                        completed_at = $13,
                        processing_time_seconds = $14,
                        progress = $15,
                        message = $16,
                        error = $17,
                        error_details = $18,
                        result = $19
                """,
                    job["id"],
                    job["status"],
                    job.get("priority", 10),
                    job.get("session_id"),
                    job["location"],
                    job["poi_type"],
                    job["poi_name"],
                    job["travel_time"],
                    job["geographic_level"],
                    job.get("census_variables", []),
                    job["created_at"],
                    job.get("started_at"),
                    job.get("completed_at"),
                    job.get("processing_time_seconds"),
                    job.get("progress", 0.0),
                    job.get("message"),
                    job.get("error"),
                    job.get("error_details"),
                    job.get("result"),
                    job.get("is_demo", False)
                )
                return True
                
        except Exception as e:
            logger.error(f"Failed to save job: {e}")
            return False
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job from the database.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data or None
        """
        try:
            async with self.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM jobs WHERE id = $1
                """, job_id)
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    async def get_recent_jobs(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent jobs with optional filtering.
        
        Args:
            limit: Maximum number of jobs to return
            status: Filter by job status
            session_id: Filter by session ID
            
        Returns:
            List of job data dictionaries
        """
        try:
            async with self.acquire() as conn:
                query = "SELECT * FROM jobs WHERE 1=1"
                params = []
                param_count = 0
                
                if status:
                    param_count += 1
                    query += f" AND status = ${param_count}"
                    params.append(status)
                
                if session_id:
                    param_count += 1
                    query += f" AND session_id = ${param_count}"
                    params.append(session_id)
                
                query += " ORDER BY created_at DESC"
                
                param_count += 1
                query += f" LIMIT ${param_count}"
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get recent jobs: {e}")
            return []
    
    async def save_performance_metric(
        self,
        metric_type: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save a performance metric.
        
        Args:
            metric_type: Type of metric (e.g., "response_time", "cache_hit_rate")
            value: Metric value
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            async with self.acquire() as conn:
                await conn.execute("""
                    INSERT INTO performance_metrics (metric_type, value, metadata)
                    VALUES ($1, $2, $3)
                """, metric_type, value, metadata)
                return True
                
        except Exception as e:
            logger.error(f"Failed to save performance metric: {e}")
            return False
    
    async def get_performance_stats(
        self,
        metric_type: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance statistics for a metric.
        
        Args:
            metric_type: Type of metric
            hours: Hours of history to analyze
            
        Returns:
            Statistics dictionary
        """
        try:
            async with self.acquire() as conn:
                cutoff = datetime.now(UTC) - timedelta(hours=hours)
                
                # Get aggregated stats
                row = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as count,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95,
                        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY value) as p99
                    FROM performance_metrics
                    WHERE metric_type = $1 AND timestamp > $2
                """, metric_type, cutoff)
                
                if row:
                    return dict(row)
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days: int = 7) -> Dict[str, int]:
        """Clean up old data from tables.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Dictionary with counts of deleted records
        """
        try:
            async with self.acquire() as conn:
                cutoff = datetime.now(UTC) - timedelta(days=days)
                deleted = {}
                
                # Clean old jobs
                result = await conn.execute("""
                    DELETE FROM jobs 
                    WHERE created_at < $1 AND status IN ('completed', 'failed')
                """, cutoff)
                deleted["jobs"] = int(result.split()[-1])
                
                # Clean expired cache entries
                result = await conn.execute("""
                    DELETE FROM cache_entries WHERE expires_at < NOW()
                """)
                deleted["cache_entries"] = int(result.split()[-1])
                
                # Clean old metrics
                result = await conn.execute("""
                    DELETE FROM performance_metrics WHERE timestamp < $1
                """, cutoff)
                deleted["metrics"] = int(result.split()[-1])
                
                logger.info(f"Cleaned up old data: {deleted}")
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {}


class DatabaseServiceSingleton:
    """Singleton manager for DatabaseService."""
    
    _instance: Optional[DatabaseService] = None
    
    @classmethod
    async def get_instance(cls) -> DatabaseService:
        """Get the singleton database service instance."""
        if cls._instance is None:
            settings = get_settings()
            cls._instance = DatabaseService(
                dsn=getattr(settings, "database_url", None),
                host=getattr(settings, "db_host", "localhost"),
                port=getattr(settings, "db_port", 5432),
                database=getattr(settings, "db_name", "socialmapper"),
                user=getattr(settings, "db_user", "postgres"),
                password=getattr(settings, "db_password", None),
            )
            await cls._instance.initialize()
        return cls._instance
    
    @classmethod
    async def close_instance(cls):
        """Close and clear the singleton instance."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


async def get_database_service() -> DatabaseService:
    """Get the global database service instance."""
    return await DatabaseServiceSingleton.get_instance()