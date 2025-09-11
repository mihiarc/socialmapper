# SocialMapper API Server

A FastAPI backend server that provides REST API access to SocialMapper's spatial analysis capabilities.

## Overview

SocialMapper is a powerful spatial analysis platform that helps understand community accessibility patterns, demographic distributions, and Points of Interest (POI) relationships. This API server exposes SocialMapper's functionality through RESTful endpoints.

## Features

### 🏢 POI Analysis
- Discover Points of Interest within travel time constraints
- Support for 10+ POI categories (libraries, hospitals, schools, parks, etc.)
- Travel time analysis with walking, biking, and driving modes

### 📊 Census Integration
- Access to comprehensive US Census demographic data
- Block group and ZCTA geographic levels
- Population, income, housing, and education variables

### 🎬 Demo Scenarios
- Pre-built analysis scenarios for common use cases
- Urban equity analysis
- Food desert identification
- Healthcare accessibility studies

### 📈 Results Management
- Track analysis progress in real-time
- Export results in multiple formats (CSV, GeoJSON, Parquet)
- Interactive map visualizations

## Installation

### Prerequisites

1. **Python 3.11+** with `uv` package manager
2. **Census API Key** (free from [api.census.gov](https://api.census.gov/data/key_signup.html))

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/mihiarc/socialmapper.git
   cd socialmapper/socialmapper-api
   
   # Create virtual environment and install dependencies
   uv venv
   uv pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Census API key:
   # SOCIALMAPPER_API_CENSUS_API_KEY=your_key_here
   ```

3. **Start the API server:**
   ```bash
   uv run python run_server.py
   ```

4. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Interactive API: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/api/v1/health

## API Endpoints

### Core Analysis
- `POST /api/v1/analysis/location` - Submit location analysis
- `GET /api/v1/analysis/{job_id}/status` - Check job status
- `GET /api/v1/analysis/{job_id}/result` - Get analysis results

### Metadata
- `GET /api/v1/metadata/poi-types` - Available POI categories
- `GET /api/v1/metadata/census-variables` - Census data variables

### Results Management
- `GET /api/v1/results/` - List all results
- `GET /api/v1/results/{job_id}` - Get specific result
- `DELETE /api/v1/results/{job_id}` - Delete result

### Demo
- `GET /api/v1/demo/scenarios` - Available demo scenarios
- `POST /api/v1/demo/run/{scenario_id}` - Run demo scenario

## Configuration

Key environment variables:

```bash
# Required
SOCIALMAPPER_API_CENSUS_API_KEY=your_census_api_key

# Optional - Server
SOCIALMAPPER_API_HOST=0.0.0.0
SOCIALMAPPER_API_PORT=8000

# Optional - Performance
SOCIALMAPPER_API_MAX_CONCURRENT_JOBS=10
SOCIALMAPPER_API_RATE_LIMIT_PER_MINUTE=60
SOCIALMAPPER_API_ENABLE_RESPONSE_COMPRESSION=true

# Optional - Authentication
SOCIALMAPPER_API_API_AUTH_ENABLED=false
SOCIALMAPPER_API_API_KEYS=your-secret-key
```

## Development

### Running Tests
```bash
uv run python -m pytest tests/ -v
```

### Code Quality
```bash
# Linting and formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy api_server/
```

### Docker Development
```bash
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Usage Examples

### Submit Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/location" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Chapel Hill, NC",
    "poi_type": "amenity",
    "poi_name": "library",
    "travel_time": 15,
    "census_variables": ["B01003_001E"]
  }'
```

### Check Status
```bash
curl "http://localhost:8000/api/v1/analysis/{job_id}/status"
```

### Get Results
```bash
curl "http://localhost:8000/api/v1/analysis/{job_id}/result"
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## Support

- GitHub Issues: https://github.com/mihiarc/socialmapper/issues
- Documentation: See `/docs` folder for detailed API documentation