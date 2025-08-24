"""Tests for MCP integration components."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from api_server.middleware.mcp_context import MCPContextMiddleware, MCPRequestContext
from api_server.services.mcp_metrics import MCPMetricsCollector, ToolInvocation


class TestMCPContextMiddleware:
    """Test MCP context middleware functionality."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/mcp/test")
        async def mcp_endpoint(request: Request):
            context = getattr(request.state, "mcp_context", None)
            if context:
                return {"request_id": context.request_id}
            return {"error": "No MCP context"}
        
        return app
    
    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return MCPContextMiddleware(
            app=app,
            enable_performance_logging=True,
            enable_request_logging=False
        )
    
    def test_extract_mcp_context(self, middleware):
        """Test MCP context extraction from headers."""
        # Create mock request
        request = MagicMock()
        request.headers = {
            "x-mcp-request-id": "test-123",
            "x-mcp-client-id": "client-456",
            "x-mcp-tool": "analyze_location",
            "x-mcp-session-id": "session-789",
            "user-agent": "MCP-Client/1.0"
        }
        request.client = MagicMock(host="127.0.0.1")
        request.url = MagicMock(path="/mcp/tools/analyze")
        
        # Extract context
        context = middleware.extract_mcp_context(request)
        
        # Verify context
        assert context.request_id == "test-123"
        assert context.client_id == "client-456"
        assert context.tool_name == "analyze_location"
        assert context.session_id == "session-789"
        assert context.source_ip == "127.0.0.1"
        assert context.user_agent == "MCP-Client/1.0"
    
    def test_performance_tracking(self, middleware):
        """Test performance metrics tracking."""
        # Create context
        context = MCPRequestContext(
            request_id="perf-test-1",
            client_id="client-1",
            tool_name="test_tool"
        )
        
        # Start tracking
        metrics = middleware.track_performance_start(context)
        assert metrics.request_id == "perf-test-1"
        assert metrics.start_time is not None
        assert "perf-test-1" in middleware.active_requests
        
        # Simulate some processing
        import time
        time.sleep(0.1)
        
        # End tracking
        completed = middleware.track_performance_end(
            context,
            status_code=200,
            response_size=1024
        )
        
        # Verify metrics
        assert completed is not None
        assert completed.duration_ms > 100  # At least 100ms
        assert completed.status_code == 200
        assert completed.response_size == 1024
        assert "perf-test-1" not in middleware.active_requests
        assert "perf-test-1" in middleware.request_history
    
    def test_slow_request_detection(self, middleware):
        """Test slow request detection."""
        middleware.performance_threshold_ms = 50  # Low threshold for testing
        
        context = MCPRequestContext(
            request_id="slow-test-1",
            tool_name="slow_tool"
        )
        
        # Start tracking
        middleware.track_performance_start(context)
        
        # Simulate slow processing
        import time
        time.sleep(0.1)
        
        # End tracking
        middleware.track_performance_end(context, status_code=200)
        
        # Check slow requests
        assert len(middleware.slow_requests) > 0
        slow_req = middleware.slow_requests[0]
        assert slow_req.request_id == "slow-test-1"
        assert slow_req.duration_ms > 50
    
    def test_statistics(self, middleware):
        """Test statistics collection."""
        # Generate some test requests
        for i in range(5):
            context = MCPRequestContext(
                request_id=f"stat-test-{i}",
                tool_name="test_tool" if i < 3 else "another_tool"
            )
            middleware.track_performance_start(context)
            middleware.track_performance_end(
                context,
                status_code=200 if i < 4 else 500,
                response_size=100 * (i + 1)
            )
        
        # Get statistics
        stats = middleware.get_statistics()
        
        # Verify statistics
        assert stats["total_requests"] == 5
        assert stats["total_errors"] == 1
        assert stats["error_rate"] == 0.2
        assert "test_tool" in stats["tool_statistics"]
        assert stats["tool_statistics"]["test_tool"]["requests"] == 3
        assert stats["tool_statistics"]["another_tool"]["requests"] == 2


class TestMCPMetricsCollector:
    """Test MCP metrics collector functionality."""
    
    @pytest.fixture
    def collector(self):
        """Create metrics collector instance."""
        return MCPMetricsCollector(
            retention_hours=1,
            sample_size=10,
            enable_detailed_tracking=True
        )
    
    def test_record_invocation(self, collector):
        """Test recording tool invocations."""
        # Record successful invocation
        collector.record_invocation(
            tool_name="analyze_location",
            client_id="client-1",
            request_id="req-1",
            duration_ms=150.5,
            success=True,
            input_size=512,
            output_size=2048
        )
        
        # Verify metrics
        assert collector.aggregate_metrics.total_invocations == 1
        assert collector.aggregate_metrics.successful_invocations == 1
        assert "analyze_location" in collector.tool_metrics
        
        tool_metrics = collector.tool_metrics["analyze_location"]
        assert tool_metrics.total_invocations == 1
        assert tool_metrics.successful_invocations == 1
        assert tool_metrics.min_duration_ms == 150.5
        assert tool_metrics.max_duration_ms == 150.5
        
        # Record failed invocation
        collector.record_invocation(
            tool_name="analyze_location",
            client_id="client-2",
            request_id="req-2",
            duration_ms=50.0,
            success=False,
            error_type="ValidationError"
        )
        
        # Verify updated metrics
        assert collector.aggregate_metrics.total_invocations == 2
        assert collector.aggregate_metrics.failed_invocations == 1
        assert tool_metrics.failed_invocations == 1
        assert tool_metrics.error_types["ValidationError"] == 1
    
    def test_client_statistics(self, collector):
        """Test client usage statistics."""
        # Record multiple invocations from same client
        for i in range(3):
            collector.record_invocation(
                tool_name=f"tool_{i}",
                client_id="client-1",
                request_id=f"req-{i}",
                duration_ms=100.0 * (i + 1),
                success=i < 2  # Last one fails
            )
        
        # Get client stats
        client_stats = collector.get_client_stats("client-1")
        assert client_stats is not None
        assert client_stats.total_requests == 3
        assert client_stats.successful_requests == 2
        assert client_stats.failed_requests == 1
        assert len(client_stats.tools_used) == 3
    
    def test_percentile_calculations(self, collector):
        """Test percentile calculations for tool metrics."""
        # Record multiple invocations with different durations
        durations = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        for i, duration in enumerate(durations):
            collector.record_invocation(
                tool_name="test_tool",
                client_id=f"client-{i}",
                request_id=f"req-{i}",
                duration_ms=float(duration),
                success=True
            )
        
        # Get tool metrics
        tool_metrics = collector.tool_metrics["test_tool"]
        
        # Verify percentiles
        assert tool_metrics.median_duration_ms == 55.0  # Middle value
        assert tool_metrics.p95_duration_ms >= 90.0  # 95th percentile
        assert tool_metrics.p99_duration_ms >= 95.0  # 99th percentile
        assert tool_metrics.avg_duration_ms == 55.0  # Average
    
    def test_time_series_data(self, collector):
        """Test time-series data collection."""
        # Record invocations at different times
        base_time = datetime.utcnow()
        
        for i in range(5):
            collector.record_invocation(
                tool_name="test_tool",
                client_id=f"client-{i}",
                request_id=f"req-{i}",
                duration_ms=100.0,
                success=i < 4  # One failure
            )
        
        # Get time series data
        time_series = collector.get_time_series(granularity="minute", hours=1)
        
        # Should have at least one data point
        assert len(time_series) > 0
        
        # Verify data structure
        first_point = time_series[0]
        assert "timestamp" in first_point
        assert "requests" in first_point
        assert "errors" in first_point
        assert "error_rate" in first_point
        assert "avg_duration_ms" in first_point
    
    def test_summary_generation(self, collector):
        """Test summary generation."""
        # Generate some test data
        tools = ["analyze", "geocode", "route"]
        clients = ["client-a", "client-b", "client-c"]
        
        for i in range(10):
            collector.record_invocation(
                tool_name=tools[i % 3],
                client_id=clients[i % 3],
                request_id=f"req-{i}",
                duration_ms=50.0 + (i * 10),
                success=i < 8  # 80% success rate
            )
        
        # Get summary
        summary = collector.get_summary()
        
        # Verify aggregate metrics
        agg = summary["aggregate"]
        assert agg["total_invocations"] == 10
        assert agg["successful_invocations"] == 8
        assert agg["failed_invocations"] == 2
        assert agg["unique_tools"] == 3
        assert agg["unique_clients"] == 3
        assert agg["error_rate"] == 0.2
        
        # Verify top tools
        assert len(summary["top_tools"]) > 0
        top_tool = summary["top_tools"][0]
        assert "name" in top_tool
        assert "invocations" in top_tool
        assert "success_rate" in top_tool
        
        # Verify top clients
        assert len(summary["top_clients"]) > 0
        top_client = summary["top_clients"][0]
        assert "client_id" in top_client
        assert "total_requests" in top_client
    
    def test_prometheus_export(self, collector):
        """Test Prometheus format export."""
        # Record some metrics
        collector.record_invocation(
            tool_name="test_tool",
            client_id="client-1",
            request_id="req-1",
            duration_ms=100.0,
            success=True
        )
        
        # Export in Prometheus format
        prometheus_output = collector.export_metrics(format="prometheus")
        
        # Verify output format
        assert "# HELP" in prometheus_output
        assert "# TYPE" in prometheus_output
        assert "mcp_invocations_total 1" in prometheus_output
        assert "mcp_invocations_success_total 1" in prometheus_output
        assert 'tool="test_tool"' in prometheus_output
    
    @pytest.mark.asyncio
    async def test_cleanup_task(self, collector):
        """Test background cleanup task."""
        # Start collector
        await collector.start()
        
        # Verify cleanup task is running
        assert collector._cleanup_task is not None
        assert not collector._cleanup_task.done()
        
        # Stop collector
        await collector.stop()
        
        # Verify cleanup task is stopped
        assert collector._cleanup_task is None


class TestMCPClientExample:
    """Test the MCP client example."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test MCP client initialization."""
        from examples.mcp_client_example import SocialMapperMCPClient
        
        client = SocialMapperMCPClient(
            base_url="http://localhost:8000",
            api_key="test-key",
            client_id="test-client"
        )
        
        assert client.base_url == "http://localhost:8000"
        assert client.api_key == "test-key"
        assert client.client_id == "test-client"
        assert client.timeout == 30.0
        
        # Check headers
        assert client.client.headers["x-mcp-client-id"] == "test-client"
        assert client.client.headers["Authorization"] == "Bearer test-key"
        
        await client.client.aclose()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])