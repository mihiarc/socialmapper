# MCP (Model Context Protocol) Setup Guide for SocialMapper API

## Overview

The Model Context Protocol (MCP) is an open standard developed by Anthropic that enables AI assistants to connect with external tools and data sources. This guide explains how to connect Claude (Desktop or Code) to your local SocialMapper API MCP server.

## Architecture

MCP uses a client-server architecture:
- **MCP Server**: Your FastAPI application with fastapi-mcp integration (running at http://localhost:8000/mcp)
- **MCP Client**: Claude Desktop or Claude Code that connects to your server
- **Transport**: HTTP with SSE (Server-Sent Events) or stdio transport via mcp-proxy

## Prerequisites

1. SocialMapper API server running with MCP enabled
2. Claude Desktop app or Claude Code CLI installed
3. mcp-proxy installed (for bridging HTTP/SSE to stdio)

## Server Configuration

Your FastAPI server is already configured with MCP support at `http://localhost:8000/mcp`. The server exposes:
- 8 tools across categories: demo, metadata, analysis, results
- MCP metrics and monitoring endpoints
- OpenAPI schema for tool discovery

### Verify Server Status

Run the test script to verify your MCP server is working:

```bash
uv run python test_mcp_connection.py
```

You should see:
- Server health: healthy
- MCP service status: healthy
- MCP enabled: True
- Total tools: 8

## Client Configuration

### Option 1: Claude Code CLI (Recommended for Development)

#### Project-Level Configuration (Already Created)

The `.mcp.json` file in your project root configures MCP for this project:

```json
{
  "mcpServers": {
    "socialmapper-local": {
      "command": "/Users/mihiarc/repos/socialmapper/socialmapper-api/.venv/bin/mcp-proxy",
      "args": ["http://localhost:8000/mcp"],
      "description": "Local SocialMapper API MCP server",
      "environment": {
        "MCP_CLIENT_ID": "claude-code-client",
        "MCP_VERSION": "1.0"
      }
    }
  }
}
```

#### Activate Configuration

1. Navigate to your project directory:
   ```bash
   cd /Users/mihiarc/repos/socialmapper/socialmapper-api
   ```

2. Refresh MCP configuration:
   ```bash
   claude mcp refresh
   ```

3. List available MCP servers:
   ```bash
   claude mcp list
   ```

4. Test the connection:
   ```bash
   claude mcp test socialmapper-local
   ```

### Option 2: Claude Desktop App

#### Configuration File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Configuration Steps

1. Create or edit the configuration file:

```json
{
  "mcpServers": {
    "socialmapper-local": {
      "command": "mcp-proxy",
      "args": ["http://localhost:8000/mcp"]
    }
  }
}
```

**Note for macOS**: Use the full path to mcp-proxy:

```json
{
  "mcpServers": {
    "socialmapper-local": {
      "command": "/usr/local/bin/mcp-proxy",
      "args": ["http://localhost:8000/mcp"]
    }
  }
}
```

Find your mcp-proxy path with:
```bash
which mcp-proxy
```

2. Restart Claude Desktop to load the configuration

3. Look for "socialmapper-local" in the MCP servers list within Claude Desktop

## Using MCP Tools in Claude

Once connected, you can use natural language to invoke the SocialMapper tools:

### Available Tools

1. **Analysis Tools**
   - Submit location analysis requests
   - Check analysis status
   - Get analysis results

2. **Metadata Tools**
   - Get available POI types
   - Retrieve supported locations

3. **Demo Tools**
   - Run pre-configured demo scenarios
   - Test urban equity analysis

4. **Results Tools**
   - Fetch completed analysis results
   - Export data in various formats

### Example Prompts

```
"Analyze accessibility for Times Square, New York with a 1-mile radius"

"Run the urban equity demo scenario"

"Check the status of job abc123"

"Get the list of available POI types"
```

## Authentication (Optional)

If your server requires authentication:

1. Set the API key environment variable:
   ```bash
   export API_KEYS='your-api-key-here'
   ```

2. Update the MCP configuration to include authentication headers:

```json
{
  "mcpServers": {
    "socialmapper-local": {
      "command": "mcp-proxy",
      "args": ["http://localhost:8000/mcp"],
      "environment": {
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Monitoring and Debugging

### Check MCP Metrics

```bash
# Get MCP metrics summary
curl http://localhost:8000/api/v1/mcp/metrics/summary

# Get tool-specific metrics
curl http://localhost:8000/api/v1/mcp/metrics/tool/submit_analysis

# Check MCP health
curl http://localhost:8000/api/v1/mcp/health
```

### View Logs

#### Claude Desktop Logs (macOS)
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

#### Server Logs
Check the terminal where your FastAPI server is running for detailed MCP activity logs.

### Common Issues and Solutions

1. **"MCP server not found"**
   - Ensure the server is running: `uv run python -m api_server.main`
   - Verify the server URL is correct: `http://localhost:8000`

2. **"mcp-proxy not found"**
   - Install mcp-proxy: `uv pip install mcp-proxy`
   - Use the full path in configuration

3. **"Connection refused"**
   - Check if the server is running on the correct port
   - Verify no firewall is blocking localhost connections

4. **"Authentication failed"**
   - Ensure API_KEYS environment variable is set
   - Check the API key is included in the server's allowed keys

## Advanced Configuration

### Custom Transport Options

For production environments, you might want to use different transport mechanisms:

1. **Direct SSE (Server-Sent Events)**
   - Requires Claude client that supports SSE directly
   - More efficient for real-time streaming

2. **WebSocket Transport**
   - For bi-directional real-time communication
   - Requires WebSocket support in both client and server

### Rate Limiting

The server implements rate limiting for MCP tools. Default: 60 requests per minute per client.

To adjust rate limiting, modify the server environment variables:
```bash
export MCP_RATE_LIMIT_PER_MINUTE=120
```

### Caching

Some tools support response caching. Default TTL: 300 seconds.

To adjust cache settings:
```bash
export MCP_CACHE_TTL=600
```

## Testing MCP Integration

### Using the Example Client

Run the provided example client to test MCP functionality:

```bash
uv run python examples/mcp_client_example.py
```

This will:
1. Connect to the MCP server
2. Discover available tools
3. Submit a sample analysis
4. Wait for completion
5. Display results

### Manual Testing with curl

Test individual MCP endpoints:

```bash
# List tools
curl http://localhost:8000/api/v1/mcp/tools

# Get tool details
curl http://localhost:8000/api/v1/mcp/tools/submit_analysis

# Check metrics
curl http://localhost:8000/api/v1/mcp/metrics/summary
```

## Security Considerations

1. **Local Development**: The default configuration assumes local development. For production:
   - Enable authentication: `MCP_AUTH_ENABLED=true`
   - Use HTTPS instead of HTTP
   - Implement proper API key management

2. **Network Security**: 
   - By default, the server only accepts connections from localhost
   - For remote access, configure appropriate firewall rules

3. **Data Privacy**:
   - MCP requests may contain sensitive location data
   - Ensure proper logging and data retention policies

## Troubleshooting

### Enable Debug Logging

For detailed MCP debugging:

```bash
export MCP_DEBUG=true
export LOG_LEVEL=DEBUG
uv run python -m api_server.main
```

### Check Server Configuration

Verify MCP is enabled in your server:

```python
# In Python
import os
print(f"MCP_ENABLED: {os.getenv('MCP_ENABLED', 'true')}")
print(f"MCP_MOUNT_PATH: {os.getenv('MCP_MOUNT_PATH', '/mcp')}")
```

### Validate Tool Registration

Check which tools are registered:

```bash
curl http://localhost:8000/api/v1/mcp/tools | jq '.tools[].name'
```

## Next Steps

1. **Explore Tools**: Use Claude to discover and test all available MCP tools
2. **Monitor Usage**: Check metrics dashboard at `/api/v1/mcp/metrics/summary`
3. **Customize Tools**: Add new FastAPI endpoints that automatically become MCP tools
4. **Production Setup**: Configure authentication, HTTPS, and remote access for production use

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [FastAPI-MCP Library](https://github.com/tadata-org/fastapi_mcp)
- [Claude Desktop Download](https://claude.ai/download)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## Support

For issues specific to:
- **MCP Protocol**: Check the official MCP documentation
- **FastAPI-MCP**: Refer to the fastapi-mcp GitHub repository
- **SocialMapper API**: Check the project's README and API documentation