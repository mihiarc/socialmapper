# SocialMapper MCP Server v1.0.0 Release Notes

🎉 **Major Release: Model Context Protocol Integration**

## 🚀 What's New

### MCP Server for Claude Code Integration
We're excited to announce the release of the **SocialMapper MCP Server**, bringing powerful spatial analysis capabilities directly to Claude Code through the Model Context Protocol (MCP).

### 📦 Package Information
- **Package Name**: `socialmapper-mcp-server`
- **Version**: 1.0.0
- **NPM Registry**: https://www.npmjs.com/package/socialmapper-mcp-server
- **Installation**: `npm install -g socialmapper-mcp-server`

## ✨ Features

### 8 Available MCP Tools
1. **`analyze_location`** - Submit location-based accessibility analysis
2. **`get_analysis_status`** - Check analysis job progress  
3. **`get_results`** - Retrieve completed analysis results
4. **`get_poi_types`** - List available POI categories and types
5. **`get_census_variables`** - Get available demographic variables
6. **`get_demo_scenarios`** - View available demo analyses
7. **`run_demo_scenario`** - Execute pre-built demo scenarios
8. **`list_results`** - List all completed analyses

### Claude Code Integration
- **Natural Language Interface**: Ask questions like "What libraries are within 15 minutes of downtown?"
- **Real-time Analysis**: Submit and track spatial analysis jobs through conversation
- **Rich Responses**: AI-optimized formatting with emojis and structured content
- **Cross-platform Support**: Works on macOS, Linux, and Windows

### Technical Innovations
- **Custom FastAPI-MCP Bridge**: Seamless translation between stdio and HTTP protocols
- **Intelligent Dependency Management**: Automatic Python dependency resolution using uv with pip fallbacks
- **Zero NPM Dependencies**: Lightweight 7.9KB package with no node_modules bloat

## 🔧 Quick Start

### Prerequisites
1. **SocialMapper API Server** running locally
2. **Census API Key** (free from api.census.gov)
3. **Claude Code** installed

### Installation
```bash
# 1. Install the MCP server
npm install -g socialmapper-mcp-server

# 2. Start SocialMapper API with MCP enabled
cd path/to/socialmapper/socialmapper-api
export SOCIALMAPPER_API_MCP_ENABLED=true
export SOCIALMAPPER_API_CENSUS_API_KEY=your_api_key
uv run python -m api_server.main

# 3. Add to Claude Code
claude mcp add socialmapper --scope user -- npx socialmapper-mcp-server
```

## 💬 Usage Examples

Once connected, you can ask Claude Code:

- *"What types of places can SocialMapper analyze?"*
- *"Analyze libraries within 15 minutes walking distance of downtown Denver"*
- *"Show me available demographic variables for census analysis"*
- *"Run a demo scenario to see how accessibility analysis works"*
- *"Check the status of my analysis job"*
- *"Show me the results of my completed analysis"*

## 🏗️ Architecture

The MCP server consists of:

1. **Node.js Wrapper** (`bin/socialmapper-mcp.js`)
   - Cross-platform executable handling Python dependencies
   - Intelligent fallback from uv → python3 → python

2. **FastAPI-MCP Bridge** (`fastapi_mcp_bridge.py`)
   - Custom protocol translation layer
   - Converts MCP stdio ↔ HTTP requests to SocialMapper API
   - Enhanced AI-friendly response formatting

3. **SocialMapper API Integration**
   - Direct connection to existing FastAPI endpoints
   - Leverages all existing spatial analysis capabilities
   - Real-time job status and progress tracking

## 🔍 What's Under the Hood

### Protocol Innovation
The biggest technical challenge was bridging FastAPI-MCP (HTTP-based) with standard MCP (stdio-based). We solved this with a custom bridge that:
- Listens for JSON-RPC on stdin
- Translates to HTTP calls to SocialMapper API  
- Formats responses optimally for AI consumption
- Handles errors and timeouts gracefully

### Dependency Strategy
Instead of bundling Python dependencies, we use intelligent runtime resolution:
1. **Preferred**: `uv run --with httpx --with asyncio` (automatic dependency installation)
2. **Fallback**: `python3 -m pip install httpx` then run
3. **Last resort**: Plain Python execution with clear error messages

## 📊 Impact & Benefits

### For Users
- **Seamless Spatial Analysis**: Natural language access to complex GIS operations
- **No Learning Curve**: Use familiar conversational interface instead of APIs
- **Real-time Insights**: Interactive exploration of demographic and accessibility data

### For Developers
- **MCP Integration Pattern**: Reference implementation for FastAPI → MCP bridges
- **Cross-platform Distribution**: NPM packaging strategy for Python-based tools
- **Zero-dependency Philosophy**: Lightweight packages with runtime dependency resolution

## 🔮 Future Roadmap

- **Enhanced Visualizations**: Direct map rendering in Claude Code interface
- **Additional Data Sources**: GTFS transit data, OpenStreetMap routing
- **Batch Processing**: Support for analyzing multiple locations simultaneously
- **Custom Analysis Types**: User-defined spatial analysis workflows

## 🤝 Contributing

The MCP server is part of the main SocialMapper repository:
- **Repository**: https://github.com/mihiarc/socialmapper
- **MCP Code**: `socialmapper-api/` directory
- **Issues**: https://github.com/mihiarc/socialmapper/issues

## 📄 License

MIT License - same as SocialMapper core project

## 🎯 Get Started Today

```bash
npm install -g socialmapper-mcp-server
claude mcp add socialmapper --scope user -- npx socialmapper-mcp-server
```

**Transform your spatial analysis workflow with the power of conversational AI!** 🌍✨

---

*Released: August 24, 2025*
*SocialMapper Team*