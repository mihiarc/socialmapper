# SocialMapper - Claude Integration Guide

SocialMapper is a comprehensive platform for community accessibility analysis and demographic mapping. This guide focuses on the FastAPI backend and its Model Context Protocol (MCP) integration, which enables AI assistants like Claude to interact with SocialMapper's powerful analysis capabilities.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Setup](#docker-setup)
- [MCP (Model Context Protocol) Integration](#mcp-model-context-protocol-integration)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Census API key (free from https://api.census.gov/data/key_signup.html)
- Docker and Docker Compose (for containerized setup)

### Installation

```bash
# Clone the repository
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper/socialmapper-api

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your Census API key
```

### Basic Usage

Start the development server:

```bash
uv run python run_server.py
```

Access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker Setup

### Development Environment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Production Environment

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

## MCP (Model Context Protocol) Integration

The SocialMapper API includes comprehensive MCP integration, enabling AI assistants to seamlessly access community accessibility analysis capabilities through a standardized protocol.

### Overview

MCP (Model Context Protocol) is a standardized protocol that allows AI assistants to interact with external services and tools. SocialMapper's MCP integration provides:

**Key Benefits:**
- **Seamless AI Integration**: Enable Claude and other AI assistants to perform location-based analyses
- **Standardized Interface**: Use established protocols for reliable AI-to-service communication
- **Real-time Analysis**: Submit and monitor analysis jobs through AI conversations
- **Rich Metadata**: Access comprehensive POI types, census variables, and geographic data
- **Demo Scenarios**: Run pre-configured analysis scenarios for quick demonstrations

**Core Capabilities:**
- Location accessibility analysis with customizable parameters
- Points of Interest (POI) discovery and categorization
- US Census demographic data integration
- Multi-modal transportation analysis (walking, driving, transit)
- Batch processing for multiple locations
- Export functionality in multiple formats

### Quick Start

#### 1. Enable MCP Integration

Set the MCP enabled flag in your environment:

```bash
# In your .env file
SOCIALMAPPER_API_MCP_ENABLED=true
```

#### 2. Basic Testing with Example Client

Test the integration using the provided example client:

```bash
# Navigate to the API directory
cd socialmapper-api

# Run the example MCP client
uv run python examples/mcp_client_example.py
```

#### 3. Verify MCP is Working

Check MCP health status:

```bash
# Check MCP service health
curl http://localhost:8000/mcp/health

# List available tools
curl http://localhost:8000/mcp/tools

# Get comprehensive metrics
curl http://localhost:8000/mcp/metrics/summary
```

### Available MCP Tools

The SocialMapper MCP integration provides 8 registered tools organized by category:

#### Analysis Tools

**`analyze_location`**
- **Description**: Analyze accessibility for a specific location
- **Endpoint**: `POST /api/v1/analysis/`
- **Category**: Analysis
- **Authentication**: Required
- **Rate Limit**: 30 requests/minute
- **Timeout**: 60 seconds
- **Cache TTL**: 1 hour

**`get_analysis_status`**
- **Description**: Get the status of an analysis job
- **Endpoint**: `GET /api/v1/analysis/{job_id}/status`
- **Category**: Analysis
- **Authentication**: Not required
- **Rate Limit**: 60 requests/minute

#### Metadata Tools

**`get_poi_types`**
- **Description**: Get available POI types for analysis
- **Endpoint**: `GET /api/v1/metadata/poi-types`
- **Category**: Metadata
- **Authentication**: Not required
- **Cache TTL**: 24 hours

**`get_census_variables`**
- **Description**: Get available census variables
- **Endpoint**: `GET /api/v1/metadata/census-variables`
- **Category**: Metadata
- **Authentication**: Not required
- **Cache TTL**: 24 hours

#### Results Tools

**`get_results`**
- **Description**: Get analysis results by job ID
- **Endpoint**: `GET /api/v1/results/{job_id}`
- **Category**: Results
- **Authentication**: Not required
- **Cache TTL**: 1 hour

**`list_results`**
- **Description**: List all available results
- **Endpoint**: `GET /api/v1/results/`
- **Category**: Results
- **Authentication**: Not required

#### Demo Tools

**`get_demo_scenarios`**
- **Description**: Get available demo scenarios
- **Endpoint**: `GET /api/v1/demo/scenarios`
- **Category**: Demo
- **Authentication**: Not required
- **Cache TTL**: 24 hours

**`run_demo_scenario`**
- **Description**: Run a demo scenario
- **Endpoint**: `POST /api/v1/demo/run/{scenario_id}`
- **Category**: Demo
- **Authentication**: Not required
- **Rate Limit**: 10 requests/minute
- **Timeout**: 30 seconds

### Configuration

#### MCP Environment Variables

Add these variables to your `.env` file to configure MCP integration:

```bash
# ===========================
# MCP (Model Context Protocol) Configuration
# ===========================

# Enable MCP integration for AI assistant interactions
SOCIALMAPPER_API_MCP_ENABLED=true

# MCP server mount path (where MCP endpoints will be available)
SOCIALMAPPER_API_MCP_MOUNT_PATH=/mcp

# MCP authentication settings
SOCIALMAPPER_API_MCP_AUTH_ENABLED=false  # Set to true to require authentication
SOCIALMAPPER_API_MCP_AUTH_TOKEN=  # Authentication token (required if auth enabled)

# MCP rate limiting (requests per minute per client)
SOCIALMAPPER_API_MCP_RATE_LIMIT_PER_MINUTE=100

# MCP tool configuration
SOCIALMAPPER_API_MCP_ALLOWED_TOOLS=  # Comma-separated list (empty = all tools)
SOCIALMAPPER_API_MCP_TOOL_TIMEOUT=30  # Timeout for tool invocations in seconds
SOCIALMAPPER_API_MCP_MAX_CONCURRENT=10  # Maximum concurrent tool invocations

# MCP context middleware settings
SOCIALMAPPER_API_MCP_ENABLE_PERFORMANCE_LOGGING=true  # Log performance metrics
SOCIALMAPPER_API_MCP_ENABLE_REQUEST_LOGGING=true  # Log requests and responses
SOCIALMAPPER_API_MCP_PERFORMANCE_THRESHOLD_MS=1000  # Slow request threshold

# MCP metrics collection
SOCIALMAPPER_API_MCP_METRICS_ENABLED=true  # Enable detailed metrics collection
SOCIALMAPPER_API_MCP_METRICS_RETENTION_HOURS=24  # Metrics retention period
SOCIALMAPPER_API_MCP_METRICS_DETAILED_TRACKING=true  # Enable per-invocation tracking
```

#### Example .env Configuration

```bash
# Required Configuration
SOCIALMAPPER_API_CENSUS_API_KEY=your_census_api_key_here
SOCIALMAPPER_API_MCP_ENABLED=true

# Optional - Server Settings
SOCIALMAPPER_API_HOST=0.0.0.0
SOCIALMAPPER_API_PORT=8000
SOCIALMAPPER_API_CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# Optional - MCP Authentication (recommended for production)
SOCIALMAPPER_API_MCP_AUTH_ENABLED=true
SOCIALMAPPER_API_API_AUTH_ENABLED=true
SOCIALMAPPER_API_API_KEYS=your-secret-api-key,another-api-key

# Optional - Rate Limiting
SOCIALMAPPER_API_MCP_RATE_LIMIT_PER_MINUTE=100
SOCIALMAPPER_API_RATE_LIMIT_PER_MINUTE=60

# Optional - Performance Tuning
SOCIALMAPPER_API_MCP_MAX_CONCURRENT=10
SOCIALMAPPER_API_MAX_CONCURRENT_JOBS=20
```

#### Authentication Setup for MCP

For production deployments, enable authentication:

1. **Enable Authentication**:
   ```bash
   SOCIALMAPPER_API_MCP_AUTH_ENABLED=true
   SOCIALMAPPER_API_API_AUTH_ENABLED=true
   ```

2. **Set API Keys**:
   ```bash
   SOCIALMAPPER_API_API_KEYS=your-secret-key-1,your-secret-key-2
   ```

3. **Use Authentication in Requests**:
   ```bash
   # Using Bearer token
   curl -H "Authorization: Bearer your-secret-key-1" \
        http://localhost:8000/mcp/tools

   # Using X-API-Key header
   curl -H "X-API-Key: your-secret-key-1" \
        http://localhost:8000/api/v1/analysis/
   ```

### Testing MCP Integration

#### Using the Example Client

The `mcp_client_example.py` demonstrates complete MCP workflow:

```bash
# Run the comprehensive example
uv run python examples/mcp_client_example.py
```

**Example Output:**
```
SocialMapper MCP Client Example

Connecting to SocialMapper MCP server at http://localhost:8000...
✓ Server is healthy: healthy
Discovering available tools...
✓ Discovered 8 tools

Available MCP Tools:
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name           ┃ Description                                                         ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ analyze_location    │ Analyze accessibility for a specific location                      │
│ get_analysis_status │ Get the status of an analysis job                                  │
│ get_poi_types       │ Get available POI types for analysis                               │
│ get_census_variables│ Get available census variables                                     │
│ get_results         │ Get analysis results by job ID                                     │
│ list_results        │ List all available results                                         │
│ get_demo_scenarios  │ Get available demo scenarios                                       │
│ run_demo_scenario   │ Run a demo scenario                                                │
└─────────────────────┴─────────────────────────────────────────────────────────────────┘
```

#### Testing with cURL Commands

Test individual MCP endpoints:

```bash
# 1. Check MCP health
curl http://localhost:8000/mcp/health | jq

# 2. List available tools
curl http://localhost:8000/mcp/tools | jq

# 3. Get POI types (metadata tool)
curl http://localhost:8000/mcp/tools/get_poi_types/invoke \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"arguments": {}}'

# 4. Start an analysis (requires authentication if enabled)
curl http://localhost:8000/mcp/tools/analyze_location/invoke \
     -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-api-key" \
     -d '{
       "arguments": {
         "name": "Downtown Analysis",
         "latitude": 40.7128,
         "longitude": -74.0060,
         "travel_time_minutes": 15,
         "travel_mode": "walking",
         "poi_types": ["healthcare", "education"],
         "census_variables": ["B01003_001E", "B19013_001E"]
       }
     }'

# 5. Check analysis status
curl http://localhost:8000/mcp/tools/get_analysis_status/invoke \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"arguments": {"job_id": "your-job-id"}}'

# 6. Get results
curl http://localhost:8000/mcp/tools/get_results/invoke \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"arguments": {"job_id": "your-job-id"}}'
```

#### Monitoring MCP Metrics

Monitor MCP performance and usage:

```bash
# Get metrics summary
curl http://localhost:8000/mcp/metrics/summary | jq

# Get time-series data
curl http://localhost:8000/mcp/metrics/time-series?granularity=minute&hours=1 | jq

# Get tool-specific metrics
curl http://localhost:8000/mcp/metrics/tool/analyze_location | jq

# Get client-specific metrics
curl http://localhost:8000/mcp/metrics/client/your-client-id | jq

# Export Prometheus metrics
curl http://localhost:8000/mcp/metrics/prometheus
```

### Monitoring & Metrics

#### Available Metrics Endpoints

**Summary Metrics**: `GET /mcp/metrics/summary`
```json
{
  "aggregate": {
    "total_invocations": 1250,
    "current_rpm": 45,
    "error_rate": 0.02,
    "avg_response_time_ms": 650,
    "uptime_hours": 72.5
  },
  "by_tool": {
    "analyze_location": {
      "invocations": 450,
      "error_rate": 0.01,
      "avg_duration_ms": 1200
    }
  },
  "by_client": {
    "claude-assistant-1": {
      "requests": 200,
      "success_rate": 0.98
    }
  }
}
```

**Time Series Data**: `GET /mcp/metrics/time-series`
- Granularity: minute or hour
- Historical data up to 24 hours
- Request counts, errors, response times

**Prometheus Metrics**: `GET /mcp/metrics/prometheus`
- Standard Prometheus format
- Ready for scraping by Prometheus server
- Includes all MCP-specific metrics

#### Understanding the Metrics Dashboard

Key metrics to monitor:

1. **Request Rate (RPM)**: Current requests per minute
2. **Error Rate**: Percentage of failed requests
3. **Response Time**: Average and percentile response times
4. **Tool Usage**: Most popular tools and their performance
5. **Client Activity**: Usage patterns by client

#### Performance Monitoring

Set up alerts for:

```bash
# High error rate (>5%)
error_rate > 0.05

# Slow response times (>2 seconds average)
avg_response_time_ms > 2000

# High request volume (>100 RPM)
current_rpm > 100

# Tool failures
tool_error_count > 10 per hour
```

### Development with MCP

#### Adding New MCP Tools

To add new tools to the MCP integration:

1. **Register the Tool** in `MCPService._setup_default_tools()`:

```python
self.tool_registry.register_tool(MCPToolMetadata(
    name="your_new_tool",
    description="Description of what the tool does",
    endpoint="/api/v1/your-endpoint",
    method="POST",
    category="your_category",
    operation_id="your_operation_id",
    tag="your_tag",
    requires_auth=True,
    rate_limit=30,
    timeout=60,
    cache_ttl=3600
))
```

2. **Create the API Endpoint** with proper operation_id and tag:

```python
@router.post("/your-endpoint", operation_id="your_operation_id", tags=["your_tag"])
async def your_endpoint(request: YourRequest) -> YourResponse:
    # Your implementation
    pass
```

#### Using the @create_mcp_aware_endpoint Decorator

For automatic MCP integration with tracking:

```python
from api_server.services.mcp_service import create_mcp_aware_endpoint

@router.post("/custom-analysis")
@create_mcp_aware_endpoint(
    tool_name="custom_analysis",
    description="Perform custom analysis with special parameters",
    category="analysis",
    requires_auth=True,
    rate_limit=20,
    cache_ttl=1800
)
async def custom_analysis(
    request: CustomAnalysisRequest,
    http_request: Request
) -> CustomAnalysisResponse:
    # Your implementation
    # Tool usage is automatically tracked
    pass
```

#### Best Practices for MCP Tool Design

1. **Clear Descriptions**: Write descriptive tool names and descriptions
2. **Appropriate Categories**: Group related tools together
3. **Auth Requirements**: Only require auth when necessary
4. **Rate Limiting**: Set appropriate limits based on resource usage
5. **Caching**: Use caching for expensive or stable operations
6. **Error Handling**: Provide clear error messages
7. **Input Validation**: Validate all input parameters
8. **Documentation**: Document expected inputs and outputs

**Example Tool Implementation**:

```python
@router.post("/api/v1/advanced-analysis", operation_id="advanced_analysis")
@create_mcp_aware_endpoint(
    tool_name="advanced_analysis",
    description="Perform advanced multi-criteria accessibility analysis",
    category="analysis",
    requires_auth=True,
    rate_limit=15,  # Lower limit for resource-intensive operation
    cache_ttl=7200   # Cache for 2 hours
)
async def advanced_analysis(
    request: AdvancedAnalysisRequest,
    http_request: Request
) -> AdvancedAnalysisResponse:
    """Perform advanced accessibility analysis with multiple criteria."""
    
    # Input validation
    if not request.criteria or len(request.criteria) > 5:
        raise HTTPException(
            status_code=400,
            detail="Must provide 1-5 analysis criteria"
        )
    
    try:
        # Implementation
        result = await perform_advanced_analysis(request)
        return AdvancedAnalysisResponse(**result)
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Advanced analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Analysis processing failed"
        )
```

---

This comprehensive MCP integration makes SocialMapper's powerful community accessibility analysis capabilities seamlessly available to AI assistants, enabling natural language interactions for complex geospatial analyses and demographic insights.