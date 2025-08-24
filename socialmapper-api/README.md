# SocialMapper MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to SocialMapper's spatial analysis capabilities.

## Overview

SocialMapper is a powerful spatial analysis platform that helps understand community accessibility patterns, demographic distributions, and Points of Interest (POI) relationships. This MCP server exposes SocialMapper's functionality to AI assistants like Claude Code.

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
2. **SocialMapper API server** running locally
3. **Census API Key** (free from [api.census.gov](https://api.census.gov/data/key_signup.html))

### Quick Start

1. **Install the MCP server package:**
   ```bash
   npm install -g socialmapper-mcp-server
   ```

2. **Start the SocialMapper API server:**
   ```bash
   # Navigate to your SocialMapper installation
   cd path/to/socialmapper/socialmapper-api
   
   # Set environment variables
   export SOCIALMAPPER_API_MCP_ENABLED=true
   export SOCIALMAPPER_API_CENSUS_API_KEY=your_census_api_key
   
   # Start the server
   uv run uvicorn api_server.main:app --host 0.0.0.0 --port 8000
   ```

3. **Add to Claude Code:**
   ```bash
   claude mcp add socialmapper --scope user -- npx socialmapper-mcp-server
   ```

## Available Tools

### Core Analysis
- **`analyze_location`** - Submit location-based accessibility analysis
- **`get_analysis_status`** - Check analysis job progress  
- **`get_results`** - Retrieve completed analysis results

### Metadata
- **`get_poi_types`** - List available POI categories and types
- **`get_census_variables`** - Get available demographic variables

### Demo & Examples
- **`get_demo_scenarios`** - View available demo analyses
- **`run_demo_scenario`** - Execute pre-built demo scenarios

### Results Management  
- **`list_results`** - List all completed analyses

## Usage Examples

Once connected to Claude Code, you can use natural language:

- *"What types of places can SocialMapper analyze?"*
- *"Analyze libraries within 15 minutes walking distance of downtown Denver"*
- *"Show me available demographic variables for census analysis"*
- *"Run a demo scenario to see how accessibility analysis works"*
- *"Check the status of my analysis job"*
- *"Show me the results of my completed analysis"*

## Configuration

### Environment Variables

Set these in your SocialMapper API server environment:

```bash
# Required
SOCIALMAPPER_API_MCP_ENABLED=true
SOCIALMAPPER_API_CENSUS_API_KEY=your_api_key

# Optional
SOCIALMAPPER_API_MCP_AUTH_ENABLED=false
SOCIALMAPPER_API_MCP_RATE_LIMIT_PER_MINUTE=60
SOCIALMAPPER_API_MCP_TOOL_TIMEOUT=30
```

### Advanced Configuration

For custom server URLs or advanced settings, see the [full documentation](https://github.com/mihiarc/socialmapper).

## Troubleshooting

### Common Issues

1. **"Server not responding"**
   - Ensure SocialMapper API server is running on localhost:8000
   - Check that MCP is enabled in server configuration

2. **"Census API errors"**
   - Verify your Census API key is valid
   - Check the key is properly set in environment variables

3. **"Tool not found"**
   - Restart Claude Code after adding the MCP server
   - Verify the server was added with correct scope

### Debug Mode

Run with debug logging:
```bash
SOCIALMAPPER_API_LOG_LEVEL=DEBUG uv run uvicorn api_server.main:app --reload
```

## Development

### Local Development

1. Clone the SocialMapper repository
2. Navigate to `socialmapper-api/`
3. Install dependencies: `uv pip install -e .`
4. Start development server: `uv run uvicorn api_server.main:app --reload`

### Contributing

See [CONTRIBUTING.md](https://github.com/mihiarc/socialmapper/blob/main/CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](https://github.com/mihiarc/socialmapper/blob/main/LICENSE) file.

## Support

- 📚 [Documentation](https://mihiarc.github.io/socialmapper)
- 🐛 [Issues](https://github.com/mihiarc/socialmapper/issues)
- 💬 [Discussions](https://github.com/mihiarc/socialmapper/discussions)

## Related

- [SocialMapper Core](https://github.com/mihiarc/socialmapper) - Main spatial analysis library
- [Model Context Protocol](https://modelcontextprotocol.io) - Open standard for AI tool integration
- [Claude Code](https://claude.ai/code) - AI-powered development assistant