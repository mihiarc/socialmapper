"""MCP (Model Context Protocol) service integration for SocialMapper API.

This module provides comprehensive MCP integration, enabling AI assistants to interact
with the SocialMapper API through a standardized protocol. It includes server management,
authentication, tool registry, and monitoring capabilities.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_mcp import FastApiMCP, AuthConfig
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console
from rich.table import Table
import httpx

from ..config import Settings, get_settings

# Initialize rich console for formatted output
console = Console()
logger = logging.getLogger(__name__)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


class MCPToolStatus(str, Enum):
    """Status of MCP tools."""
    
    AVAILABLE = "available"
    DISABLED = "disabled"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class MCPToolMetadata(BaseModel):
    """Metadata for MCP tools."""
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(default="POST", description="HTTP method")
    category: str = Field(default="general", description="Tool category")
    operation_id: Optional[str] = Field(None, description="FastAPI operation ID")
    tag: Optional[str] = Field(None, description="FastAPI route tag")
    requires_auth: bool = Field(default=False, description="Whether authentication is required")
    rate_limit: Optional[int] = Field(None, description="Custom rate limit for this tool")
    timeout: Optional[int] = Field(None, description="Custom timeout in seconds")
    cache_ttl: Optional[int] = Field(None, description="Cache TTL in seconds")
    status: MCPToolStatus = Field(default=MCPToolStatus.AVAILABLE, description="Tool status")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(default=0, description="Total usage count")
    error_count: int = Field(default=0, description="Total error count")
    avg_response_time: Optional[float] = Field(None, description="Average response time in ms")


class MCPAuthProvider:
    """Authentication provider for MCP endpoints."""
    
    def __init__(self, settings: Settings):
        """Initialize the authentication provider.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.security = HTTPBearer(auto_error=False)
        self.auth_cache: Dict[str, datetime] = {}
        self.failed_attempts: Dict[str, int] = {}
        
    async def verify_token(self, credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
        """Verify the authentication token.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            True if authentication is successful, False otherwise
        """
        if not self.settings.mcp_auth_enabled:
            return True
            
        if not credentials:
            return False
            
        token = credentials.credentials
        
        # Check cache
        if token in self.auth_cache:
            if self.auth_cache[token] > datetime.utcnow():
                return True
            else:
                del self.auth_cache[token]
        
        # Validate token against configured keys
        valid_keys = [k.strip() for k in self.settings.api_keys.split(",") if k.strip()]
        if token in valid_keys:
            # Cache for 1 hour
            self.auth_cache[token] = datetime.utcnow() + timedelta(hours=1)
            return True
            
        # Track failed attempts
        self.failed_attempts[token] = self.failed_attempts.get(token, 0) + 1
        return False
        
    def get_auth_dependency(self) -> Callable:
        """Get FastAPI dependency for authentication.
        
        Returns:
            Dependency function for FastAPI
        """
        async def auth_dependency(
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            if not await self.verify_token(credentials):
                logger.warning(f"MCP authentication failed for {request.client.host}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return True
            
        return auth_dependency


class MCPToolRegistry:
    """Registry for managing MCP tools and their metadata."""
    
    def __init__(self, settings: Settings):
        """Initialize the tool registry.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.tools: Dict[str, MCPToolMetadata] = {}
        self.categories: Dict[str, Set[str]] = {}
        self.endpoint_mapping: Dict[str, str] = {}
        self.operation_id_mapping: Dict[str, str] = {}
        self.tag_mapping: Dict[str, Set[str]] = {}
        self._usage_stats: Dict[str, List[float]] = {}  # Store response times
        
    def register_tool(self, metadata: MCPToolMetadata) -> None:
        """Register a new tool.
        
        Args:
            metadata: Tool metadata
        """
        self.tools[metadata.name] = metadata
        
        # Update category mapping
        if metadata.category not in self.categories:
            self.categories[metadata.category] = set()
        self.categories[metadata.category].add(metadata.name)
        
        # Update endpoint mapping
        self.endpoint_mapping[metadata.endpoint] = metadata.name
        
        # Update operation ID mapping
        if metadata.operation_id:
            self.operation_id_mapping[metadata.operation_id] = metadata.name
            
        # Update tag mapping
        if metadata.tag:
            if metadata.tag not in self.tag_mapping:
                self.tag_mapping[metadata.tag] = set()
            self.tag_mapping[metadata.tag].add(metadata.name)
        
        logger.info(f"Registered MCP tool: {metadata.name} ({metadata.endpoint})")
        
    def get_tool(self, name: str) -> Optional[MCPToolMetadata]:
        """Get tool metadata by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool metadata if found, None otherwise
        """
        return self.tools.get(name)
        
    def get_available_tools(self) -> List[MCPToolMetadata]:
        """Get all available tools.
        
        Returns:
            List of available tools
        """
        return [
            tool for tool in self.tools.values()
            if tool.status == MCPToolStatus.AVAILABLE
        ]
        
    def get_operation_ids(self) -> List[str]:
        """Get list of operation IDs for available tools.
        
        Returns:
            List of operation IDs
        """
        return [
            tool.operation_id for tool in self.get_available_tools()
            if tool.operation_id
        ]
        
    def get_tags(self) -> List[str]:
        """Get list of unique tags from available tools.
        
        Returns:
            List of tags
        """
        tags = set()
        for tool in self.get_available_tools():
            if tool.tag:
                tags.add(tool.tag)
        return list(tags)
        
    def update_tool_stats(self, name: str, response_time: float, success: bool) -> None:
        """Update tool usage statistics.
        
        Args:
            name: Tool name
            response_time: Response time in milliseconds
            success: Whether the request was successful
        """
        if name not in self.tools:
            return
            
        tool = self.tools[name]
        tool.usage_count += 1
        tool.last_used = datetime.utcnow()
        
        if not success:
            tool.error_count += 1
            
        # Update average response time
        if name not in self._usage_stats:
            self._usage_stats[name] = []
        
        self._usage_stats[name].append(response_time)
        
        # Keep only last 100 measurements
        if len(self._usage_stats[name]) > 100:
            self._usage_stats[name] = self._usage_stats[name][-100:]
            
        tool.avg_response_time = sum(self._usage_stats[name]) / len(self._usage_stats[name])
        
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get comprehensive tool statistics.
        
        Returns:
            Dictionary of tool statistics
        """
        total_requests = sum(tool.usage_count for tool in self.tools.values())
        total_errors = sum(tool.error_count for tool in self.tools.values())
        
        return {
            "total_tools": len(self.tools),
            "available_tools": len(self.get_available_tools()),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "categories": {
                category: len(tools) for category, tools in self.categories.items()
            },
            "top_used_tools": sorted(
                [
                    {
                        "name": tool.name,
                        "usage_count": tool.usage_count,
                        "avg_response_time": tool.avg_response_time
                    }
                    for tool in self.tools.values()
                ],
                key=lambda x: x["usage_count"],
                reverse=True
            )[:5]
        }
        
    def display_tool_stats(self) -> None:
        """Display tool statistics in a formatted table."""
        table = Table(title="MCP Tool Statistics", show_header=True)
        table.add_column("Tool Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Usage", style="yellow")
        table.add_column("Errors", style="red")
        table.add_column("Avg Response (ms)", style="blue")
        table.add_column("Last Used", style="magenta")
        
        for tool in sorted(self.tools.values(), key=lambda x: x.usage_count, reverse=True):
            status_style = "green" if tool.status == MCPToolStatus.AVAILABLE else "red"
            table.add_row(
                tool.name,
                f"[{status_style}]{tool.status.value}[/{status_style}]",
                str(tool.usage_count),
                str(tool.error_count),
                f"{tool.avg_response_time:.2f}" if tool.avg_response_time else "N/A",
                tool.last_used.strftime("%Y-%m-%d %H:%M:%S") if tool.last_used else "Never"
            )
            
        console.print(table)


class MCPRateLimiter:
    """Rate limiter for MCP endpoints."""
    
    def __init__(self, settings: Settings):
        """Initialize the rate limiter.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.request_counts: Dict[str, List[datetime]] = {}
        self.blocked_until: Dict[str, datetime] = {}
        
    async def check_rate_limit(self, client_id: str, tool_name: Optional[str] = None) -> bool:
        """Check if the client has exceeded the rate limit.
        
        Args:
            client_id: Client identifier
            tool_name: Optional tool name for tool-specific limits
            
        Returns:
            True if within rate limit, False otherwise
        """
        now = datetime.utcnow()
        
        # Check if client is temporarily blocked
        if client_id in self.blocked_until:
            if self.blocked_until[client_id] > now:
                return False
            else:
                del self.blocked_until[client_id]
        
        # Get rate limit
        rate_limit = self.settings.mcp_rate_limit_per_minute
        if tool_name:
            tool = MCPToolRegistry(self.settings).get_tool(tool_name)
            if tool and tool.rate_limit:
                rate_limit = tool.rate_limit
        
        # Clean old requests
        if client_id in self.request_counts:
            self.request_counts[client_id] = [
                dt for dt in self.request_counts[client_id]
                if dt > now - timedelta(minutes=1)
            ]
        else:
            self.request_counts[client_id] = []
        
        # Check limit
        if len(self.request_counts[client_id]) >= rate_limit:
            # Block for 1 minute
            self.blocked_until[client_id] = now + timedelta(minutes=1)
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return False
        
        # Record request
        self.request_counts[client_id].append(now)
        return True


class MCPService:
    """Main MCP service for managing the MCP server and tools."""
    
    def __init__(self, app: FastAPI, settings: Settings):
        """Initialize the MCP service.
        
        Args:
            app: FastAPI application instance
            settings: Application settings
        """
        self.app = app
        self.settings = settings
        self.mcp_server: Optional[FastApiMCP] = None
        self.auth_provider = MCPAuthProvider(settings)
        self.tool_registry = MCPToolRegistry(settings)
        self.rate_limiter = MCPRateLimiter(settings)
        self.is_initialized = False
        self._setup_default_tools()
        
    def _setup_default_tools(self) -> None:
        """Set up default MCP tools based on existing API endpoints."""
        # Analysis tools
        self.tool_registry.register_tool(MCPToolMetadata(
            name="analyze_location",
            description="Analyze accessibility for a specific location",
            endpoint="/api/v1/analysis/",
            method="POST",
            category="analysis",
            operation_id="create_analysis_analysis__post",
            tag="analysis",
            requires_auth=True,
            rate_limit=30,
            timeout=60,
            cache_ttl=3600
        ))
        
        self.tool_registry.register_tool(MCPToolMetadata(
            name="get_analysis_status",
            description="Get the status of an analysis job",
            endpoint="/api/v1/analysis/{job_id}/status",
            method="GET",
            category="analysis",
            operation_id="get_analysis_status_analysis__job_id__status_get",
            tag="analysis",
            requires_auth=False,
            rate_limit=60
        ))
        
        # Metadata tools
        self.tool_registry.register_tool(MCPToolMetadata(
            name="get_poi_types",
            description="Get available POI types for analysis",
            endpoint="/api/v1/metadata/poi-types",
            method="GET",
            category="metadata",
            operation_id="get_poi_types_metadata_poi_types_get",
            tag="metadata",
            requires_auth=False,
            cache_ttl=86400  # Cache for 24 hours
        ))
        
        self.tool_registry.register_tool(MCPToolMetadata(
            name="get_census_variables",
            description="Get available census variables",
            endpoint="/api/v1/metadata/census-variables",
            method="GET",
            category="metadata",
            operation_id="get_census_variables_metadata_census_variables_get",
            tag="metadata",
            requires_auth=False,
            cache_ttl=86400
        ))
        
        # Results tools
        self.tool_registry.register_tool(MCPToolMetadata(
            name="get_results",
            description="Get analysis results by job ID",
            endpoint="/api/v1/results/{job_id}",
            method="GET",
            category="results",
            operation_id="get_results_results__job_id__get",
            tag="results",
            requires_auth=False,
            cache_ttl=3600
        ))
        
        self.tool_registry.register_tool(MCPToolMetadata(
            name="list_results",
            description="List all available results",
            endpoint="/api/v1/results/",
            method="GET",
            category="results",
            operation_id="list_results_results__get",
            tag="results",
            requires_auth=False
        ))
        
        # Demo tools
        self.tool_registry.register_tool(MCPToolMetadata(
            name="get_demo_scenarios",
            description="Get available demo scenarios",
            endpoint="/api/v1/demo/scenarios",
            method="GET",
            category="demo",
            operation_id="get_scenarios_demo_scenarios_get",
            tag="demo",
            requires_auth=False,
            cache_ttl=86400
        ))
        
        self.tool_registry.register_tool(MCPToolMetadata(
            name="run_demo_scenario",
            description="Run a demo scenario",
            endpoint="/api/v1/demo/run/{scenario_id}",
            method="POST",
            category="demo",
            operation_id="run_scenario_demo_run__scenario_id__post",
            tag="demo",
            requires_auth=False,
            rate_limit=10,
            timeout=30
        ))
        
    async def initialize(self) -> None:
        """Initialize the MCP server and register tools."""
        if self.is_initialized:
            logger.warning("MCP service already initialized")
            return
            
        try:
            # Prepare auth config if needed
            auth_config = None
            if self.settings.mcp_auth_enabled and self.settings.api_keys:
                # Create auth config using API keys
                valid_keys = [k.strip() for k in self.settings.api_keys.split(",") if k.strip()]
                if valid_keys:
                    # For now, we'll use a simple bearer token approach
                    # In production, you might want to use OAuth2 or other auth methods
                    auth_config = AuthConfig(
                        oauth_callback_url=f"http://localhost:{self.settings.port}/mcp/oauth/callback"
                    )
            
            # Determine which tools to include
            include_operations = None
            include_tags = None
            
            if self.settings.mcp_allowed_tools:
                # If specific tools are configured, use operation IDs
                allowed_tool_names = set(self.settings.mcp_allowed_tools)
                include_operations = []
                for tool in self.tool_registry.get_available_tools():
                    if tool.name in allowed_tool_names and tool.operation_id:
                        include_operations.append(tool.operation_id)
            else:
                # Include all tools by tags
                include_tags = self.tool_registry.get_tags()
            
            # Create custom HTTP client with timeout
            http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.mcp_tool_timeout),
                limits=httpx.Limits(
                    max_connections=self.settings.mcp_max_concurrent,
                    max_keepalive_connections=5
                )
            )
            
            # Create FastAPI MCP server instance
            self.mcp_server = FastApiMCP(
                fastapi=self.app,
                name="socialmapper-mcp",
                description="MCP integration for SocialMapper API - Community accessibility analysis",
                describe_all_responses=False,
                describe_full_response_schema=False,
                http_client=http_client,
                include_operations=include_operations,
                include_tags=include_tags,
                auth_config=auth_config,
                headers=["authorization", "x-api-key"] if self.settings.mcp_auth_enabled else []
            )
            
            # Mount MCP server with HTTP transport (recommended)
            self.mcp_server.mount_http(
                router=self.app,
                mount_path=self.settings.mcp_mount_path
            )
            
            self.is_initialized = True
            logger.info(f"MCP service initialized successfully at {self.settings.mcp_mount_path}")
            
            # Display initial stats
            self.tool_registry.display_tool_stats()
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP service: {e}")
            raise
            
    async def shutdown(self) -> None:
        """Shut down the MCP service."""
        if self.mcp_server:
            logger.info("Shutting down MCP service...")
            # Display final statistics
            self.tool_registry.display_tool_stats()
            
            # Clean up HTTP client if it exists
            if hasattr(self.mcp_server, "_http_client") and self.mcp_server._http_client:
                await self.mcp_server._http_client.aclose()
                
            self.mcp_server = None
            self.is_initialized = False
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the MCP service.
        
        Returns:
            Health status information
        """
        return {
            "enabled": self.settings.mcp_enabled,
            "initialized": self.is_initialized,
            "mount_path": self.settings.mcp_mount_path,
            "total_tools": len(self.tool_registry.tools),
            "available_tools": len(self.tool_registry.get_available_tools()),
            "auth_enabled": self.settings.mcp_auth_enabled,
            "rate_limit": self.settings.mcp_rate_limit_per_minute,
            "stats": self.tool_registry.get_tool_stats()
        }


def create_mcp_aware_endpoint(
    tool_name: str,
    description: str,
    category: str = "general",
    requires_auth: bool = False,
    rate_limit: Optional[int] = None,
    cache_ttl: Optional[int] = None
) -> Callable[[F], F]:
    """Decorator to create MCP-aware endpoints.
    
    This decorator automatically registers endpoints with the MCP tool registry
    and adds MCP-specific metadata and handling.
    
    Args:
        tool_name: Name of the tool in MCP
        description: Tool description
        category: Tool category
        requires_auth: Whether authentication is required
        rate_limit: Custom rate limit for this tool
        cache_ttl: Cache TTL in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Add MCP context to the request if available
            request = kwargs.get("request")
            if request and hasattr(request.app.state, "mcp_service"):
                mcp_service = request.app.state.mcp_service
                
                # Track tool usage
                import time
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    response_time = (time.time() - start_time) * 1000
                    mcp_service.tool_registry.update_tool_stats(tool_name, response_time, True)
                    return result
                    
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    mcp_service.tool_registry.update_tool_stats(tool_name, response_time, False)
                    raise
            else:
                # No MCP service, run normally
                return await func(*args, **kwargs)
                
        # Store MCP metadata on the function
        wrapper.mcp_metadata = MCPToolMetadata(
            name=tool_name,
            description=description,
            endpoint="",  # Will be set during registration
            category=category,
            requires_auth=requires_auth,
            rate_limit=rate_limit,
            cache_ttl=cache_ttl
        )
        
        return wrapper
        
    return decorator


# Singleton instance management
_mcp_service_instance: Optional[MCPService] = None


async def init_mcp_service(app: FastAPI, settings: Settings) -> MCPService:
    """Initialize the MCP service singleton.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
        
    Returns:
        MCP service instance
    """
    global _mcp_service_instance
    
    if _mcp_service_instance is None:
        _mcp_service_instance = MCPService(app, settings)
        await _mcp_service_instance.initialize()
        
    return _mcp_service_instance


def get_mcp_service() -> Optional[MCPService]:
    """Get the MCP service singleton instance.
    
    Returns:
        MCP service instance if initialized, None otherwise
    """
    return _mcp_service_instance


async def shutdown_mcp_service() -> None:
    """Shut down the MCP service singleton."""
    global _mcp_service_instance
    
    if _mcp_service_instance:
        await _mcp_service_instance.shutdown()
        _mcp_service_instance = None