import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.requests import Request

logger = logging.getLogger(__name__)

router = APIRouter()


def get_mcp_app():
    """Get the MCP FastMCP application for SSE transport"""
    try:
        from app.services.mcp_service import mcp_service
        mcp_server = mcp_service.get_mcp_server()
        if mcp_server:
            # Get the SSE app from FastMCP
            return mcp_server.sse_app()
        else:
            logger.error("MCP server not available")
            return None
    except Exception as e:
        logger.error(f"Error getting MCP app: {str(e)}")
        return None


@router.get("/status")
async def mcp_status():
    """Get MCP server status"""
    try:
        from app.services.mcp_service import mcp_service
        server_config = mcp_service.config.get("mcp_server", {})
        
        return JSONResponse({
            "status": "healthy",
            "server_name": server_config.get("name", "unknown"),
            "version": server_config.get("version", "unknown"),
            "tools_count": len(server_config.get("tools", [])),
            "resources_count": len(server_config.get("resources", [])),
            "tools": [tool.get("name") for tool in server_config.get("tools", [])],
            "mcp_available": mcp_service.get_mcp_server() is not None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting MCP status: {str(e)}")


@router.get("/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    try:
        from app.services.mcp_service import mcp_service
        tools = mcp_service.get_tools_for_claude()
        
        return JSONResponse({
            "tools": tools,
            "count": len(tools)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing MCP tools: {str(e)}")


# This is a special endpoint that will be mounted as a sub-application
# The actual MCP SSE server will be mounted in the main application
async def mcp_sse_handler(request: Request) -> Response:
    """Handler for MCP SSE requests - this will be mounted as a sub-app"""
    mcp_app = get_mcp_app()
    if not mcp_app:
        return Response("MCP server not available", status_code=503)
    
    # Forward the request to the MCP SSE app
    return await mcp_app(request.scope, request.receive, request._send)