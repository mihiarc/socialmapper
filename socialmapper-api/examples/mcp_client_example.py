"""Example MCP client for interacting with the SocialMapper API.

This module demonstrates how to use the MCP protocol to interact with
the SocialMapper API, including tool discovery, analysis submission,
and status checking.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


class MCPTool(BaseModel):
    """MCP tool definition."""
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Dict[str, Any] = Field(..., description="Input schema")


class MCPResponse(BaseModel):
    """MCP response wrapper."""
    
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class AnalysisRequest(BaseModel):
    """Analysis request parameters."""
    
    location: str = Field(..., description="Location name or address")
    radius_miles: float = Field(default=1.0, description="Analysis radius in miles")
    poi_types: List[str] = Field(
        default_factory=lambda: ["healthcare", "education", "grocery"],
        description="POI types to analyze"
    )
    include_demographics: bool = Field(default=True, description="Include demographic data")
    include_walkability: bool = Field(default=True, description="Include walkability analysis")


class SocialMapperMCPClient:
    """MCP client for interacting with the SocialMapper API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        timeout: float = 30.0
    ):
        """Initialize the MCP client.
        
        Args:
            base_url: Base URL of the SocialMapper API
            api_key: API key for authentication
            client_id: Client identifier for tracking
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client_id = client_id or f"mcp-client-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.timeout = timeout
        
        # Setup HTTP client
        headers = {
            "x-mcp-client-id": self.client_id,
            "x-mcp-version": "1.0",
            "User-Agent": "SocialMapper-MCP-Client/1.0"
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            headers["x-api-key"] = api_key
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True
        )
        
        self.tools: Dict[str, MCPTool] = {}
        self.session_id: Optional[str] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect to the MCP server and discover tools."""
        console.print(f"[cyan]Connecting to SocialMapper MCP server at {self.base_url}...[/cyan]")
        
        try:
            # Check health
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            response.raise_for_status()
            health_data = response.json()
            console.print(f"[green]✓ Server is healthy: {health_data.get('status', 'unknown')}[/green]")
            
            # Discover tools
            await self.discover_tools()
            
            # Initialize session
            self.session_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.client.headers["x-mcp-session-id"] = self.session_id
            
            console.print(f"[green]✓ Connected with session ID: {self.session_id}[/green]")
            
        except httpx.HTTPError as e:
            console.print(f"[red]✗ Failed to connect: {e}[/red]")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        console.print("[cyan]Disconnecting from MCP server...[/cyan]")
        await self.client.aclose()
        console.print("[green]✓ Disconnected[/green]")
    
    async def discover_tools(self) -> Dict[str, MCPTool]:
        """Discover available MCP tools.
        
        Returns:
            Dictionary of available tools
        """
        console.print("[cyan]Discovering available tools...[/cyan]")
        
        try:
            # Try MCP tools endpoint
            response = await self.client.get(f"{self.base_url}/mcp/tools")
            
            if response.status_code == 200:
                tools_data = response.json()
                
                # Parse tools
                for tool_data in tools_data.get("tools", []):
                    tool = MCPTool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        inputSchema=tool_data.get("inputSchema", {})
                    )
                    self.tools[tool.name] = tool
                
                # Display discovered tools
                self._display_tools()
                
            else:
                # Fallback to OpenAPI schema
                console.print("[yellow]MCP tools endpoint not available, using OpenAPI schema[/yellow]")
                await self._discover_from_openapi()
            
            console.print(f"[green]✓ Discovered {len(self.tools)} tools[/green]")
            return self.tools
            
        except httpx.HTTPError as e:
            console.print(f"[red]✗ Failed to discover tools: {e}[/red]")
            return {}
    
    async def _discover_from_openapi(self) -> None:
        """Discover tools from OpenAPI schema."""
        try:
            response = await self.client.get(f"{self.base_url}/openapi.json")
            response.raise_for_status()
            schema = response.json()
            
            # Extract operations as tools
            for path, methods in schema.get("paths", {}).items():
                for method, operation in methods.items():
                    if method in ["get", "post", "put", "delete"]:
                        operation_id = operation.get("operationId", f"{method}_{path}")
                        tool = MCPTool(
                            name=operation_id,
                            description=operation.get("summary", operation.get("description", "")),
                            inputSchema=operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
                        )
                        self.tools[tool.name] = tool
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get OpenAPI schema: {e}")
    
    def _display_tools(self) -> None:
        """Display discovered tools in a table."""
        if not self.tools:
            console.print("[yellow]No tools discovered[/yellow]")
            return
        
        table = Table(title="Available MCP Tools", show_header=True)
        table.add_column("Tool Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Input Schema", style="dim")
        
        for tool in self.tools.values():
            schema_str = json.dumps(tool.inputSchema, indent=2)[:100] + "..." if len(json.dumps(tool.inputSchema)) > 100 else json.dumps(tool.inputSchema, indent=2)
            table.add_row(
                tool.name,
                tool.description[:80] + "..." if len(tool.description) > 80 else tool.description,
                schema_str
            )
        
        console.print(table)
    
    async def invoke_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> MCPResponse:
        """Invoke an MCP tool.
        
        Args:
            tool_name: Name of the tool to invoke
            arguments: Tool arguments
            request_id: Optional request ID for tracking
            
        Returns:
            MCP response
        """
        if tool_name not in self.tools:
            return MCPResponse(
                success=False,
                error=f"Tool '{tool_name}' not found"
            )
        
        request_id = request_id or f"req-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        try:
            # Add request ID to headers
            headers = {"x-mcp-request-id": request_id}
            
            # Invoke tool via MCP endpoint
            response = await self.client.post(
                f"{self.base_url}/mcp/tools/{tool_name}/invoke",
                json={"arguments": arguments},
                headers=headers
            )
            
            if response.status_code == 200:
                return MCPResponse(
                    success=True,
                    data=response.json(),
                    request_id=request_id
                )
            else:
                return MCPResponse(
                    success=False,
                    error=f"Tool invocation failed: {response.status_code} - {response.text}",
                    request_id=request_id
                )
            
        except httpx.HTTPError as e:
            return MCPResponse(
                success=False,
                error=f"HTTP error: {e}",
                request_id=request_id
            )
    
    async def submit_analysis(self, request: AnalysisRequest) -> MCPResponse:
        """Submit an analysis request.
        
        Args:
            request: Analysis request parameters
            
        Returns:
            MCP response with job ID
        """
        console.print(f"[cyan]Submitting analysis for {request.location}...[/cyan]")
        
        # Use direct API endpoint for analysis
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/analysis/",
                json=request.dict()
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                job_id = data.get("job_id")
                console.print(f"[green]✓ Analysis submitted successfully. Job ID: {job_id}[/green]")
                return MCPResponse(
                    success=True,
                    data=data,
                    request_id=response.headers.get("x-mcp-request-id")
                )
            else:
                error_msg = f"Failed to submit analysis: {response.status_code} - {response.text}"
                console.print(f"[red]✗ {error_msg}[/red]")
                return MCPResponse(
                    success=False,
                    error=error_msg
                )
            
        except httpx.HTTPError as e:
            error_msg = f"HTTP error: {e}"
            console.print(f"[red]✗ {error_msg}[/red]")
            return MCPResponse(
                success=False,
                error=error_msg
            )
    
    async def check_status(self, job_id: str) -> MCPResponse:
        """Check the status of an analysis job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            MCP response with status information
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/analysis/{job_id}/status"
            )
            
            if response.status_code == 200:
                return MCPResponse(
                    success=True,
                    data=response.json(),
                    request_id=response.headers.get("x-mcp-request-id")
                )
            else:
                return MCPResponse(
                    success=False,
                    error=f"Failed to get status: {response.status_code} - {response.text}"
                )
            
        except httpx.HTTPError as e:
            return MCPResponse(
                success=False,
                error=f"HTTP error: {e}"
            )
    
    async def get_results(self, job_id: str) -> MCPResponse:
        """Get analysis results.
        
        Args:
            job_id: Job identifier
            
        Returns:
            MCP response with analysis results
        """
        console.print(f"[cyan]Fetching results for job {job_id}...[/cyan]")
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/results/{job_id}"
            )
            
            if response.status_code == 200:
                console.print(f"[green]✓ Results retrieved successfully[/green]")
                return MCPResponse(
                    success=True,
                    data=response.json(),
                    request_id=response.headers.get("x-mcp-request-id")
                )
            else:
                error_msg = f"Failed to get results: {response.status_code} - {response.text}"
                console.print(f"[red]✗ {error_msg}[/red]")
                return MCPResponse(
                    success=False,
                    error=error_msg
                )
            
        except httpx.HTTPError as e:
            error_msg = f"HTTP error: {e}"
            console.print(f"[red]✗ {error_msg}[/red]")
            return MCPResponse(
                success=False,
                error=error_msg
            )
    
    async def wait_for_completion(
        self,
        job_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 5
    ) -> MCPResponse:
        """Wait for an analysis job to complete.
        
        Args:
            job_id: Job identifier
            max_wait_seconds: Maximum time to wait
            poll_interval: Polling interval in seconds
            
        Returns:
            MCP response with final status
        """
        start_time = asyncio.get_event_loop().time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Waiting for job {job_id} to complete...",
                total=max_wait_seconds
            )
            
            while asyncio.get_event_loop().time() - start_time < max_wait_seconds:
                # Check status
                status_response = await self.check_status(job_id)
                
                if status_response.success and status_response.data:
                    status = status_response.data.get("status")
                    
                    if status == "completed":
                        progress.update(task, completed=max_wait_seconds)
                        console.print(f"[green]✓ Job {job_id} completed successfully[/green]")
                        return status_response
                    
                    elif status == "failed":
                        console.print(f"[red]✗ Job {job_id} failed[/red]")
                        return status_response
                    
                    elif status in ["pending", "processing"]:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        progress.update(
                            task,
                            completed=min(elapsed, max_wait_seconds),
                            description=f"[cyan]Status: {status}..."
                        )
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
        
        # Timeout
        console.print(f"[yellow]⚠ Timeout waiting for job {job_id}[/yellow]")
        return MCPResponse(
            success=False,
            error=f"Timeout after {max_wait_seconds} seconds"
        )
    
    async def run_demo_scenario(self, scenario_id: str = "urban_equity") -> None:
        """Run a demo scenario.
        
        Args:
            scenario_id: Demo scenario identifier
        """
        console.print(f"\n[bold cyan]Running Demo Scenario: {scenario_id}[/bold cyan]\n")
        
        try:
            # Run demo scenario
            response = await self.client.post(
                f"{self.base_url}/api/v1/demo/run/{scenario_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                
                console.print(f"[green]✓ Demo scenario started. Job ID: {job_id}[/green]")
                
                # Wait for completion
                status_response = await self.wait_for_completion(job_id)
                
                if status_response.success:
                    # Get results
                    results_response = await self.get_results(job_id)
                    
                    if results_response.success and results_response.data:
                        self._display_results(results_response.data)
                
            else:
                console.print(f"[red]✗ Failed to run demo: {response.status_code}[/red]")
                
        except httpx.HTTPError as e:
            console.print(f"[red]✗ HTTP error: {e}[/red]")
    
    def _display_results(self, results: Dict[str, Any]) -> None:
        """Display analysis results."""
        console.print("\n[bold green]Analysis Results[/bold green]\n")
        
        # Basic information
        info_table = Table(show_header=False)
        info_table.add_column("Field", style="cyan")
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Location", results.get("location", "Unknown"))
        info_table.add_row("Analysis Type", results.get("analysis_type", "Unknown"))
        info_table.add_row("Status", results.get("status", "Unknown"))
        
        if "timestamp" in results:
            info_table.add_row("Timestamp", results["timestamp"])
        
        console.print(info_table)
        
        # Accessibility scores
        if "accessibility_scores" in results:
            console.print("\n[bold]Accessibility Scores:[/bold]")
            scores_table = Table(show_header=True)
            scores_table.add_column("POI Type", style="cyan")
            scores_table.add_column("Score", style="yellow")
            scores_table.add_column("Count", style="green")
            
            for poi_type, data in results["accessibility_scores"].items():
                scores_table.add_row(
                    poi_type,
                    f"{data.get('score', 0):.2f}",
                    str(data.get('count', 0))
                )
            
            console.print(scores_table)
        
        # Demographics
        if "demographics" in results:
            console.print("\n[bold]Demographics:[/bold]")
            demo_table = Table(show_header=True)
            demo_table.add_column("Metric", style="cyan")
            demo_table.add_column("Value", style="white")
            
            demographics = results["demographics"]
            demo_table.add_row("Total Population", f"{demographics.get('total_population', 0):,}")
            demo_table.add_row("Median Income", f"${demographics.get('median_income', 0):,}")
            
            if "age_distribution" in demographics:
                for age_group, count in demographics["age_distribution"].items():
                    demo_table.add_row(f"Age {age_group}", f"{count:,}")
            
            console.print(demo_table)


async def main():
    """Main example demonstrating MCP client usage."""
    console.print("[bold cyan]SocialMapper MCP Client Example[/bold cyan]\n")
    
    # Configuration
    base_url = "http://localhost:8000"
    api_key = None  # Set if authentication is required
    
    try:
        # Create and connect client
        async with SocialMapperMCPClient(base_url=base_url, api_key=api_key) as client:
            
            # Example 1: Submit a custom analysis
            console.print("\n[bold]Example 1: Custom Analysis Request[/bold]\n")
            
            analysis_request = AnalysisRequest(
                location="Times Square, New York, NY",
                radius_miles=0.5,
                poi_types=["healthcare", "education", "grocery", "transit"],
                include_demographics=True,
                include_walkability=True
            )
            
            response = await client.submit_analysis(analysis_request)
            
            if response.success and response.data:
                job_id = response.data.get("job_id")
                
                # Wait for completion
                status_response = await client.wait_for_completion(job_id, max_wait_seconds=120)
                
                if status_response.success:
                    # Get and display results
                    results_response = await client.get_results(job_id)
                    if results_response.success and results_response.data:
                        client._display_results(results_response.data)
            
            # Example 2: Run a demo scenario
            console.print("\n[bold]Example 2: Demo Scenario[/bold]\n")
            await client.run_demo_scenario("urban_equity")
            
            # Example 3: Direct tool invocation
            console.print("\n[bold]Example 3: Direct Tool Invocation[/bold]\n")
            
            if "get_poi_types" in client.tools:
                poi_response = await client.invoke_tool("get_poi_types", {})
                if poi_response.success:
                    console.print("[green]Available POI types:[/green]")
                    console.print(poi_response.data)
            
            # Display final statistics
            console.print("\n[bold]Session Statistics[/bold]\n")
            console.print(f"Session ID: {client.session_id}")
            console.print(f"Tools discovered: {len(client.tools)}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Example failed")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())