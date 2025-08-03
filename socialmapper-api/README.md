# SocialMapper API Backend

A high-performance FastAPI-based REST API server that provides programmatic access to SocialMapper's community mapping and demographic analysis capabilities. This backend service enables clean separation between UI and core analysis functionality.

## Overview

The SocialMapper API provides a modern, async REST interface for:
- Location-based demographic analysis with US Census data integration
- Points of Interest (POI) analysis with customizable travel times
- Multi-modal transportation analysis (walking, driving, public transit)
- Batch processing for multiple locations
- Export functionality in various formats (CSV, GeoJSON, Parquet)

## Features

- **Async Job Processing**: Long-running analyses processed asynchronously with real-time status tracking
- **Multi-Modal Analysis**: Support for walking, driving, and public transit travel modes
- **Census Integration**: Automatic integration with US Census Bureau data for demographic insights
- **Flexible POI Support**: Analyze OpenStreetMap POIs or upload custom POI datasets
- **Multiple Export Formats**: CSV, GeoJSON, Parquet, and GeoParquet export options
- **Production Ready**: Built-in rate limiting, CORS support, and optional API key authentication
- **Auto Documentation**: Interactive API documentation via Swagger UI and ReDoc
- **Health Monitoring**: Comprehensive health checks and system status endpoints

## Quick Start

### Prerequisites

- Python 3.11 or higher
- SocialMapper core library
- Census API key (get one free at https://api.census.gov/data/key_signup.html)

### Installation

```bash
# Clone the repository
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper/socialmapper-api

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```bash
# Required
CENSUS_API_KEY=your_census_api_key_here

# Optional - API Server Settings
SOCIALMAPPER_API_HOST=0.0.0.0
SOCIALMAPPER_API_PORT=8000
SOCIALMAPPER_API_WORKERS=4

# Optional - CORS (for frontend integration)
SOCIALMAPPER_API_CORS_ORIGINS=["http://localhost:3000"]

# Optional - Authentication
SOCIALMAPPER_API_KEY_ENABLED=false
SOCIALMAPPER_API_KEYS=["your-secret-api-key"]

# Optional - Rate Limiting
SOCIALMAPPER_RATE_LIMIT_ENABLED=true
SOCIALMAPPER_RATE_LIMIT_PER_MINUTE=60

# Optional - Storage Settings
SOCIALMAPPER_RESULTS_TTL_HOURS=24
SOCIALMAPPER_MAX_STORAGE_GB=10
```

### Running the Server

Development mode with auto-reload:
```bash
# Using the run script
uv run python run_server.py

# Or directly with uvicorn
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Production mode with multiple workers:
```bash
uv run uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Key API Endpoints

### Health & Status
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/status` - Detailed system status

### Analysis Endpoints
- `POST /api/v1/analysis/location` - Analyze a single location
- `POST /api/v1/analysis/custom-pois` - Analyze with custom POI dataset
- `POST /api/v1/analysis/batch` - Batch analysis for multiple locations
- `GET /api/v1/analysis/{job_id}/status` - Check analysis job status
- `POST /api/v1/analysis/{job_id}/cancel` - Cancel running analysis

### Results Endpoints
- `GET /api/v1/results/{job_id}` - Retrieve analysis results
- `GET /api/v1/results/{job_id}/export` - Export results (CSV, GeoJSON, etc.)
- `POST /api/v1/results/{job_id}/export` - Export with custom options
- `DELETE /api/v1/results/{job_id}` - Delete results
- `GET /api/v1/results/storage/stats` - Storage usage statistics

### Metadata Endpoints
- `GET /api/v1/census/variables` - List available census variables
- `GET /api/v1/poi/types` - List available POI types
- `GET /api/v1/geography/search` - Search for geographic locations

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def analyze_location():
    async with httpx.AsyncClient() as client:
        # Start analysis
        response = await client.post(
            "http://localhost:8000/api/v1/analysis/location",
            json={
                "name": "Downtown Coffee Shop Analysis",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "travel_time_minutes": 15,
                "travel_mode": "walking",
                "poi_types": ["cafe", "coffee_shop"],
                "census_variables": ["B01003_001E", "B19013_001E"]
            }
        )
        
        job_id = response.json()["job_id"]
        print(f"Analysis started: {job_id}")
        
        # Poll for completion
        while True:
            status_response = await client.get(
                f"http://localhost:8000/api/v1/analysis/{job_id}/status"
            )
            status = status_response.json()
            
            if status["status"] == "completed":
                break
            elif status["status"] == "failed":
                print(f"Analysis failed: {status['error']}")
                return
                
            print(f"Status: {status['status']} ({status['progress']}%)")
            await asyncio.sleep(2)
        
        # Get results
        results = await client.get(
            f"http://localhost:8000/api/v1/results/{job_id}"
        )
        
        data = results.json()
        print(f"Found {data['total_pois']} POIs")
        print(f"Population: {data['demographics']['total_population']:,}")
        
        # Export as CSV
        export = await client.get(
            f"http://localhost:8000/api/v1/results/{job_id}/export?format=csv"
        )
        
        with open("results.csv", "wb") as f:
            f.write(export.content)

# Run the analysis
asyncio.run(analyze_location())
```

### cURL Examples

```bash
# Start a location analysis
curl -X POST "http://localhost:8000/api/v1/analysis/location" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NYC Parks Analysis",
    "latitude": 40.7580,
    "longitude": -73.9855,
    "travel_time_minutes": 20,
    "travel_mode": "walking",
    "poi_types": ["park", "playground"]
  }'

# Check job status
curl "http://localhost:8000/api/v1/analysis/{job_id}/status"

# Get results
curl "http://localhost:8000/api/v1/results/{job_id}" | jq

# Export as GeoJSON
curl "http://localhost:8000/api/v1/results/{job_id}/export?format=geojson" \
  -o results.geojson
```

### JavaScript/TypeScript Example

```typescript
// Using the provided TypeScript client
import { SocialMapperAPIClient } from './client';

const client = new SocialMapperAPIClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key' // if authentication is enabled
});

// Start analysis
const { job_id } = await client.analyzeSingleLocation({
  name: 'Grocery Store Access',
  latitude: 34.0522,
  longitude: -118.2437,
  travel_time_minutes: 10,
  travel_mode: 'driving',
  poi_types: ['supermarket', 'grocery_store']
});

// Poll for completion
const result = await client.pollJobStatus(job_id);

// Export results
const csvData = await client.exportResults(job_id, 'csv');
```

## Docker Deployment

### Build and Run with Docker

```bash
# Build the image
docker build -t socialmapper-api .

# Run the container
docker run -d \
  --name socialmapper-api \
  -p 8000:8000 \
  -e CENSUS_API_KEY=your_key_here \
  socialmapper-api
```

### Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Docker Compose (Production)

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

## Development

### Project Structure

```
socialmapper-api/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
├── dependencies.py         # Dependency injection
├── models/                 # Pydantic models
│   ├── analysis.py        # Analysis request/response models
│   ├── census.py          # Census data models
│   ├── geography.py       # Geographic models
│   └── results.py         # Result models
├── routers/               # API route handlers
│   ├── analysis.py        # Analysis endpoints
│   ├── health.py          # Health check endpoints
│   ├── metadata.py        # Metadata endpoints
│   └── results.py         # Results endpoints
├── services/              # Business logic
│   ├── analysis.py        # Analysis orchestration
│   ├── job_manager.py     # Async job management
│   └── storage.py         # Result storage
├── middleware/            # Custom middleware
│   ├── auth.py           # API key authentication
│   ├── cors.py           # CORS configuration
│   └── rate_limit.py     # Rate limiting
└── tests/                # Test suite
    ├── test_analysis.py
    ├── test_results.py
    └── conftest.py
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_analysis.py -v

# Run integration tests only
uv run pytest -m integration
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy .
```

## Performance Tuning

### Optimization Tips

1. **Worker Configuration**: Adjust workers based on CPU cores
   ```bash
   # Recommended: 2-4 workers per CPU core
   uvicorn main:app --workers $(nproc)
   ```

2. **Connection Pooling**: Configure database connection pools in production

3. **Caching**: Enable Redis for improved performance
   ```bash
   SOCIALMAPPER_REDIS_URL=redis://localhost:6379
   ```

4. **Resource Limits**: Set appropriate limits
   ```bash
   SOCIALMAPPER_MAX_CONCURRENT_JOBS=20
   SOCIALMAPPER_MAX_STORAGE_GB=100
   ```

## Monitoring

### Metrics and Logging

- Structured JSON logging for production environments
- Prometheus metrics available at `/metrics` (when enabled)
- Request ID tracking for debugging

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Detailed status
curl http://localhost:8000/api/v1/status
```

## Security

### Best Practices

1. **API Keys**: Enable authentication in production
   ```bash
   SOCIALMAPPER_API_KEY_ENABLED=true
   SOCIALMAPPER_API_KEYS=["key1", "key2"]
   ```

2. **HTTPS**: Always use HTTPS in production (handled by reverse proxy)

3. **Rate Limiting**: Configure appropriate limits
   ```bash
   SOCIALMAPPER_RATE_LIMIT_PER_MINUTE=60
   ```

4. **CORS**: Restrict origins to known frontends
   ```bash
   SOCIALMAPPER_API_CORS_ORIGINS=["https://yourdomain.com"]
   ```

## Troubleshooting

### Common Issues

1. **Census API Key**: Ensure your Census API key is valid
2. **Port Conflicts**: Check if port 8000 is already in use
3. **Memory Issues**: Increase Docker memory limits for large analyses
4. **CORS Errors**: Verify frontend origin is in allowed list

### Debug Mode

Enable debug logging:
```bash
SOCIALMAPPER_LOG_LEVEL=DEBUG uv run python run_server.py
```

## Contributing

We welcome contributions! Please see the main [SocialMapper repository](https://github.com/mihiarc/socialmapper) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Support

- **Documentation**: [Full Documentation](https://socialmapper.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/mihiarc/socialmapper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mihiarc/socialmapper/discussions)