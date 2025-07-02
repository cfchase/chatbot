# MCP Server Integration with FastMCP

## Overview

This project implements a **Model Context Protocol (MCP)** server integration using the `fastmcp` Python package. The system loads MCP server tools from a `config.json` file and makes them available to Claude during chat interactions.

## What We Built

### 1. Core MCP Service (`backend/app/services/mcp_service.py`)
- **Purpose**: Loads and manages MCP tools from configuration
- **Features**:
  - Dynamic tool loading from `config.json`
  - Tool registration with FastMCP server
  - Resource management (health status, tool listings)
  - Tool execution interface for Claude integration

### 2. Enhanced Claude Service (`backend/app/services/claude_enhanced.py`)
- **Purpose**: Extends Claude API with MCP tool capabilities
- **Features**:
  - Automatic tool discovery from MCP service
  - Tool execution during conversations
  - Both streaming and non-streaming responses
  - Backward compatibility with existing Claude service

### 3. MCP Configuration (`backend/config.json`)
- **Purpose**: Defines available tools and resources
- **Included Tools**:
  - `get_current_time`: Get current date/time with timezone support
  - `calculate`: Perform mathematical calculations
  - `generate_uuid`: Generate UUIDs (v1 or v4)
  - `encode_decode_text`: Base64 and URL encoding/decoding
  - `weather_info`: Mock weather data (for demonstration)

### 4. API Endpoints (`backend/app/api/routes/v1/mcp/`)
- **MCP Status**: `GET /api/v1/mcp/status` - Server health and tool count
- **Tool List**: `GET /api/v1/mcp/tools` - Available tools and schemas
- **SSE Server**: Mounted at `/mcp/sse` for MCP client connections

### 5. Updated Chat System
- **Integration**: Chat endpoints now use enhanced Claude service
- **Tool Usage**: Claude can automatically use available MCP tools
- **Transparency**: Tool usage is clearly indicated in responses

## Key Files Created/Modified

```
backend/
├── config.json                           # MCP tool configuration
├── app/services/
│   ├── mcp_service.py                    # Core MCP service
│   └── claude_enhanced.py                # Enhanced Claude service
├── app/api/routes/v1/
│   ├── mcp/                              # MCP API routes
│   │   ├── __init__.py
│   │   └── router.py
│   └── chat/router.py                    # Updated to use enhanced Claude
├── main.py                               # Updated to mount MCP SSE server
└── pyproject.toml                        # Added fastmcp dependency
```

## How It Works

### 1. Startup Process
1. MCP service loads configuration from `config.json`
2. FastMCP server is created with tools from config
3. Tools are registered with their implementations
4. SSE server is mounted at `/mcp/sse` endpoint
5. Enhanced Claude service discovers available tools

### 2. Chat Flow with Tools
1. User sends message to chat endpoint
2. Enhanced Claude service gets available MCP tools
3. Claude API call includes tool definitions
4. If Claude decides to use a tool:
   - Tool call is detected in response
   - MCP service executes the tool
   - Result is included in final response
5. User sees both Claude's response and tool results

### 3. Tool Configuration Example
```json
{
  "mcp_server": {
    "name": "chatbot-mcp-server",
    "tools": [
      {
        "name": "calculate",
        "description": "Perform basic mathematical calculations",
        "parameters": {
          "type": "object",
          "properties": {
            "expression": {
              "type": "string",
              "description": "Mathematical expression to evaluate"
            }
          },
          "required": ["expression"]
        }
      }
    ]
  }
}
```

## API Endpoints

### Chat with MCP Tools
```bash
# Non-streaming chat
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"message": "What time is it in New York?", "stream": false}'

# Streaming chat
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"message": "Calculate 15 * 7 + 3", "stream": true}'
```

### MCP Server Status
```bash
curl http://localhost:8000/api/v1/mcp/status
```

### Available Tools
```bash
curl http://localhost:8000/api/v1/mcp/tools
```

### Connect MCP Client
```bash
# SSE endpoint for MCP clients
curl http://localhost:8000/mcp/sse
```

## Sample Tool Usage

When you ask Claude to perform tasks that match available tools, it will automatically use them:

**User**: "What's the current time in UTC?"
**Claude**: Uses `get_current_time` tool and responds with actual time

**User**: "Calculate 25 * 4 + 10"
**Claude**: Uses `calculate` tool and shows the computation result

**User**: "Generate a UUID for me"
**Claude**: Uses `generate_uuid` tool and provides a new UUID

**User**: "Encode 'hello world' in base64"
**Claude**: Uses `encode_decode_text` tool with base64_encode operation

## Running the System

### Prerequisites
- Python 3.11+
- FastMCP package (`pip install fastmcp==2.7.0`)
- Other dependencies from `pyproject.toml`

### Start the Server
```bash
cd backend
python3 main.py
```

### Test MCP Integration
```bash
# Check server status
curl http://localhost:8000/

# Check MCP status
curl http://localhost:8000/api/v1/mcp/status

# Test chat with tools (requires ANTHROPIC_API_KEY)
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"message": "What time is it?", "stream": false}'
```

## Configuration Options

### Environment Variables
- `ANTHROPIC_API_KEY`: Required for Claude integration
- `ANTHROPIC_MODEL`: Claude model to use (default: claude-sonnet-4-20250514)
- `PORT`: Server port (default: 8000)

### Adding New Tools
1. Add tool definition to `config.json`
2. Implement tool logic in `MCPService._register_tool()`
3. Add corresponding execution logic in `MCPService.execute_tool()`
4. Restart server

## Benefits of This Architecture

1. **Separation of Concerns**: MCP tools are defined separately from Claude logic
2. **Easy Extension**: Add new tools by updating configuration and implementations
3. **Standard Protocol**: Uses MCP standard for tool definitions
4. **Client Support**: Exposes SSE endpoint for external MCP clients
5. **Backward Compatible**: Existing chat functionality continues to work
6. **Tool Transparency**: Clear indication when tools are used

## Future Enhancements

- **Dynamic Tool Loading**: Hot-reload tools without server restart
- **External Tool Services**: Connect to remote MCP servers
- **Tool Authentication**: Secure tool access and permissions
- **Tool Composition**: Chain multiple tools together
- **Advanced Tool Types**: File operations, API integrations, database queries

This MCP integration provides a solid foundation for extending Claude's capabilities with custom tools while maintaining clean architecture and following MCP standards.