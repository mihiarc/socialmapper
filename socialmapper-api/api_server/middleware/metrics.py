"""Comprehensive metrics middleware for FastAPI using Prometheus."""

import time
from typing import Callable, Dict, Optional
from urllib.parse import unquote

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)
import redis
import logging

logger = logging.getLogger(__name__)

# Create a custom registry for application metrics
METRICS_REGISTRY = CollectorRegistry()

# HTTP Metrics
http_requests_total = Counter(
    'fastapi_requests_total',
    'Total number of HTTP requests',
    ['method', 'path', 'status', 'version'],
    registry=METRICS_REGISTRY
)

http_request_duration_seconds = Histogram(
    'fastapi_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=METRICS_REGISTRY
)

http_request_size_bytes = Histogram(
    'fastapi_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'path'],
    buckets=(1, 10, 100, 1000, 10000, 100000, 1000000),
    registry=METRICS_REGISTRY
)

http_response_size_bytes = Histogram(
    'fastapi_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'path', 'status'],
    buckets=(1, 10, 100, 1000, 10000, 100000, 1000000, 10000000),
    registry=METRICS_REGISTRY
)

# Application-specific metrics
active_requests = Gauge(
    'fastapi_active_requests',
    'Number of active HTTP requests',
    ['method', 'path'],
    registry=METRICS_REGISTRY
)

# Business metrics for SocialMapper
analysis_requests_total = Counter(
    'socialmapper_analysis_requests_total',
    'Total number of analysis requests',
    ['analysis_type', 'status'],
    registry=METRICS_REGISTRY
)

analysis_duration_seconds = Histogram(
    'socialmapper_analysis_duration_seconds',
    'Analysis processing duration in seconds',
    ['analysis_type'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800),
    registry=METRICS_REGISTRY
)

analysis_queue_depth = Gauge(
    'socialmapper_analysis_queue_depth',
    'Number of analyses in the processing queue',
    registry=METRICS_REGISTRY
)

analysis_completed_total = Counter(
    'socialmapper_analysis_completed_total',
    'Total number of completed analyses',
    ['status', 'analysis_type'],
    registry=METRICS_REGISTRY
)

# User engagement metrics
active_users_total = Gauge(
    'socialmapper_active_users_total',
    'Number of active users in the last 24 hours',
    registry=METRICS_REGISTRY
)

feedback_submissions_total = Counter(
    'socialmapper_feedback_submissions_total',
    'Total number of feedback submissions',
    ['feedback_type', 'rating'],
    registry=METRICS_REGISTRY
)

# Resource utilization
redis_operations_total = Counter(
    'socialmapper_redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],
    registry=METRICS_REGISTRY
)

redis_connection_pool_size = Gauge(
    'socialmapper_redis_connection_pool_size',
    'Current Redis connection pool size',
    registry=METRICS_REGISTRY
)

# Error tracking
application_errors_total = Counter(
    'socialmapper_application_errors_total',
    'Total application errors',
    ['error_type', 'endpoint'],
    registry=METRICS_REGISTRY
)

# Cache metrics
cache_operations_total = Counter(
    'socialmapper_cache_operations_total',
    'Total cache operations',
    ['operation', 'cache_type', 'result'],
    registry=METRICS_REGISTRY
)

cache_hit_ratio = Gauge(
    'socialmapper_cache_hit_ratio',
    'Cache hit ratio as a percentage',
    ['cache_type'],
    registry=METRICS_REGISTRY
)


class MetricsMiddleware:
    """Comprehensive metrics collection middleware."""
    
    def __init__(self, app: FastAPI, redis_client: Optional[redis.Redis] = None):
        self.app = app
        self.redis_client = redis_client
        self.path_templates: Dict[str, str] = {}
        
        # Extract path templates from FastAPI routes
        self._extract_path_templates()
    
    def _extract_path_templates(self):
        """Extract path templates from FastAPI routes for consistent labeling."""
        for route in self.app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                # Store the template path for each route
                self.path_templates[route.path] = route.path
    
    def _get_path_template(self, path: str) -> str:
        """Get the path template for a given path."""
        # Try to match against known templates
        for template_path in self.path_templates:
            if self._path_matches_template(path, template_path):
                return template_path
        
        # Fallback to simplified path
        return self._simplify_path(path)
    
    def _path_matches_template(self, path: str, template: str) -> bool:
        """Check if a path matches a template."""
        # Simple template matching - can be enhanced
        path_parts = path.strip('/').split('/')
        template_parts = template.strip('/').split('/')
        
        if len(path_parts) != len(template_parts):
            return False
        
        for path_part, template_part in zip(path_parts, template_parts):
            if template_part.startswith('{') and template_part.endswith('}'):
                # This is a path parameter, skip matching
                continue
            elif path_part != template_part:
                return False
        
        return True
    
    def _simplify_path(self, path: str) -> str:
        """Simplify path for metrics to avoid high cardinality."""
        # Replace UUIDs and IDs with placeholders
        import re
        
        # Replace UUID patterns
        path = re.sub(r'/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '/{uuid}', path)
        # Replace numeric IDs
        path = re.sub(r'/\d+(?=/|$)', '/{id}', path)
        # Replace any remaining long alphanumeric strings (likely IDs)
        path = re.sub(r'/[a-zA-Z0-9]{10,}(?=/|$)', '/{id}', path)
        
        return path
    
    def _get_request_size(self, request: Request) -> int:
        """Get request size in bytes."""
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return 0
    
    def _get_response_size(self, response: Response) -> int:
        """Get response size in bytes."""
        if hasattr(response, 'body') and response.body:
            return len(response.body)
        
        # Try to get from headers
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return 0
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Extract request information
        method = request.method
        path = unquote(request.url.path)
        path_template = self._get_path_template(path)
        
        # Track active requests
        active_requests.labels(method=method, path=path_template).inc()
        
        # Track request size
        request_size = self._get_request_size(request)
        http_request_size_bytes.labels(method=method, path=path_template).observe(request_size)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            status = str(response.status_code)
            
            # Track successful request
            duration = time.time() - start_time
            
        except Exception as e:
            # Track failed request
            status = "500"
            duration = time.time() - start_time
            
            # Track application errors
            error_type = type(e).__name__
            application_errors_total.labels(
                error_type=error_type,
                endpoint=path_template
            ).inc()
            
            # Re-raise the exception
            raise
        
        finally:
            # Decrease active requests
            active_requests.labels(method=method, path=path_template).dec()
        
        # Record metrics
        http_requests_total.labels(
            method=method,
            path=path_template,
            status=status,
            version="v1"
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            path=path_template,
            status=status
        ).observe(duration)
        
        # Track response size
        response_size = self._get_response_size(response)
        http_response_size_bytes.labels(
            method=method,
            path=path_template,
            status=status
        ).observe(response_size)
        
        return response


class BusinessMetricsCollector:
    """Collector for SocialMapper business metrics."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
    
    def record_analysis_request(self, analysis_type: str):
        """Record an analysis request."""
        analysis_requests_total.labels(
            analysis_type=analysis_type,
            status="requested"
        ).inc()
    
    def record_analysis_completion(self, analysis_type: str, status: str, duration: float):
        """Record analysis completion."""
        analysis_completed_total.labels(
            status=status,
            analysis_type=analysis_type
        ).inc()
        
        analysis_duration_seconds.labels(
            analysis_type=analysis_type
        ).observe(duration)
    
    def update_queue_depth(self, depth: int):
        """Update analysis queue depth."""
        analysis_queue_depth.set(depth)
    
    def record_feedback(self, feedback_type: str, rating: Optional[str] = None):
        """Record feedback submission."""
        feedback_submissions_total.labels(
            feedback_type=feedback_type,
            rating=rating or "none"
        ).inc()
    
    def record_cache_operation(self, operation: str, cache_type: str, result: str):
        """Record cache operation."""
        cache_operations_total.labels(
            operation=operation,
            cache_type=cache_type,
            result=result
        ).inc()
    
    def update_cache_hit_ratio(self, cache_type: str, ratio: float):
        """Update cache hit ratio."""
        cache_hit_ratio.labels(cache_type=cache_type).set(ratio * 100)
    
    def record_redis_operation(self, operation: str, status: str):
        """Record Redis operation."""
        redis_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
    
    def update_active_users(self, count: int):
        """Update active users count."""
        active_users_total.set(count)
    
    async def collect_redis_metrics(self):
        """Collect Redis-specific metrics."""
        if not self.redis_client:
            return
        
        try:
            # Get connection pool information
            pool = self.redis_client.connection_pool
            if hasattr(pool, 'created_connections'):
                redis_connection_pool_size.set(pool.created_connections)
            
            # Record successful operation
            self.record_redis_operation("info", "success")
            
        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")
            self.record_redis_operation("info", "error")


# Global metrics collector instance
business_metrics = BusinessMetricsCollector()


def setup_metrics(app: FastAPI, redis_client: Optional[redis.Redis] = None):
    """Setup comprehensive metrics for FastAPI application."""
    # Add metrics middleware
    metrics_middleware = MetricsMiddleware(app, redis_client)
    app.middleware("http")(metrics_middleware)
    
    # Initialize business metrics collector
    if redis_client:
        business_metrics.redis_client = redis_client
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        # Collect additional Redis metrics
        if redis_client:
            await business_metrics.collect_redis_metrics()
        
        # Generate metrics output
        return Response(
            content=generate_latest(METRICS_REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Add business metrics endpoint
    @app.get("/api/v1/metrics/business")
    async def business_metrics_endpoint():
        """Business-specific metrics endpoint."""
        # This could return custom business metrics in JSON format
        # For now, it returns the same Prometheus format
        return Response(
            content=generate_latest(METRICS_REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
    
    logger.info("Metrics collection setup completed")


def get_business_metrics() -> BusinessMetricsCollector:
    """Get the global business metrics collector."""
    return business_metrics