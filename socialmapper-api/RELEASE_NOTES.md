# SocialMapper API Server Release Notes

## Version 0.2.0 - Major Cleanup Release

🧹 **Major Cleanup: Removed Experimental Features**

This release focuses on code simplification and maintainability by removing experimental features that were not ready for production.

### Key Changes

#### Removed Features
- **MCP Integration**: Removed experimental Model Context Protocol support
- **Duplicate Job Managers**: Consolidated job management into single implementation
- **Redundant Analysis Routers**: Merged analysis endpoints into single router
- **Experimental Middleware**: Removed MCP-specific middleware and context handlers

#### Code Quality Improvements
- **Reduced Codebase**: Removed ~2,000 lines of experimental/duplicate code
- **Simplified Configuration**: Removed 25+ MCP-related environment variables
- **Better Test Coverage**: Focused testing on core functionality (56% → target 75%)
- **Cleaner Dependencies**: Removed fastapi-mcp and related dependencies

#### Architecture Simplification
- **Single Job Manager**: Enhanced job manager with prioritization and caching
- **Unified Error Handling**: Consolidated error handling middleware
- **Streamlined Middleware**: Reduced from 10+ to 6 essential middleware components
- **Core API Focus**: Concentrated on REST API functionality

### Breaking Changes

⚠️ **Configuration Changes**:
- All `SOCIALMAPPER_API_MCP_*` environment variables removed
- MCP endpoints (`/api/v1/mcp/*`) no longer available
- MCP health endpoint (`/mcp/status`) removed

⚠️ **Import Changes**:
- `api_server.services.mcp_service` module removed
- `api_server.services.mcp_metrics` module removed
- `api_server.middleware.mcp_context` module removed
- `api_server.routers.mcp` module removed

### Migration Guide

If you were using MCP functionality:

1. **Remove MCP Configuration**:
   ```bash
   # Remove these from your .env file:
   # SOCIALMAPPER_API_MCP_ENABLED=true
   # SOCIALMAPPER_API_MCP_*=...
   ```

2. **Update Dependencies**:
   ```bash
   uv pip install -r requirements.txt  # Will remove fastapi-mcp
   ```

3. **Use REST API Instead**:
   ```bash
   # Instead of MCP tools, use direct HTTP calls:
   curl -X POST "http://localhost:8000/api/v1/analysis/location" \
     -H "Content-Type: application/json" \
     -d '{"location": "Chapel Hill, NC", ...}'
   ```

### Core API Endpoints (Unchanged)

All main functionality remains available through REST endpoints:

- **Analysis**: `POST /api/v1/analysis/location`
- **Job Status**: `GET /api/v1/analysis/{job_id}/status`
- **Results**: `GET /api/v1/analysis/{job_id}/result`
- **Metadata**: `GET /api/v1/metadata/poi-types`
- **Demo**: `POST /api/v1/demo/run/{scenario_id}`

### Performance Improvements

- **Faster Startup**: Removed complex MCP initialization
- **Lower Memory**: Eliminated duplicate services and caching layers
- **Cleaner Logs**: Removed verbose MCP performance logging
- **Better Error Handling**: Simplified error propagation

### Development Benefits

- **Easier Testing**: Focused test suite on core functionality
- **Simpler Debugging**: Removed complex middleware chains
- **Better Documentation**: Clear focus on REST API capabilities
- **Reduced Complexity**: Single job manager, unified routing

---

## Version 0.1.0 - Initial API Release

🚀 **Initial Release: SocialMapper API Server**

### Features

#### Core Functionality
- **RESTful API**: FastAPI-based spatial analysis service
- **Job Management**: Background processing with status tracking
- **POI Analysis**: Points of Interest discovery and analysis
- **Census Integration**: US Census demographic data access
- **Demo Scenarios**: Pre-built analysis examples

#### API Endpoints
- Analysis submission and tracking
- Metadata discovery (POI types, census variables)
- Results management and export
- Health monitoring and status

#### Infrastructure
- **Authentication**: API key-based security
- **Rate Limiting**: Request throttling and client management
- **Caching**: Redis-based performance optimization
- **Database**: PostgreSQL support for persistent storage
- **WebSocket**: Real-time job progress updates

#### Development
- **Testing**: Comprehensive test suite with pytest
- **Documentation**: OpenAPI/Swagger integration
- **Docker**: Containerized deployment support
- **Configuration**: Environment-based settings management