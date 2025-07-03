import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from fastmcp import Client
from app.config import settings

logger = logging.getLogger(__name__)


class MCPService:
    """Service for managing MCP (Model Context Protocol) servers and tools"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.tools: List[Dict[str, Any]] = []
        self._config: Optional[Dict[str, Any]] = None
        self._initialized = False
        self._config_loaded = False
        self._load_config_and_client()
    
    def _load_config_and_client(self) -> None:
        """Load configuration and create client (synchronous)"""
        if self._config_loaded:
            return
            
        self._config_loaded = True
        
        try:
            # Load configuration
            config_path = Path(settings.mcp_config_path)
            if not config_path.exists():
                logger.info(f"MCP config file not found at {config_path}. Using empty configuration.")
                self._config = {"mcpServers": {}}
                self.client = Client(self._config)
                return
            
            with open(config_path, 'r') as f:
                self._config = json.load(f)
            
            # Initialize FastMCP client with the configuration
            self.client = Client(self._config)
            logger.info(f"MCP client created with config from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config or create client: {str(e)}")
            self._config = None
            self.client = None
    
    async def initialize(self) -> None:
        """Initialize the MCP service by connecting to servers and discovering tools"""
        if self._initialized:
            return
        
        # Mark as initialized immediately to prevent multiple initialization attempts
        self._initialized = True
        
        if not self.client:
            logger.info("No MCP client available. MCP tools will not be available.")
            return
            
        try:
            # Connect to servers and discover tools
            async with self.client:
                discovered_tools = await self.client.list_tools()
                
                # Convert FastMCP tools to Anthropic-compatible format
                self.tools = []
                for tool in discovered_tools:
                    anthropic_tool = {
                        "name": tool.name,
                        "description": tool.description or f"MCP tool: {tool.name}",
                        "input_schema": tool.inputSchema
                    }
                    self.tools.append(anthropic_tool)
                
                logger.info(f"MCP initialized with {len(self.tools)} tools from {len(self._config.get('mcpServers', {}))} servers")
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP tools: {str(e)}")
            self.tools = []
    
    async def shutdown(self) -> None:
        """Shutdown the MCP service and close connections"""
        # Simply reset the service state
        # The Client will handle cleanup when garbage collected
        self.client = None
        self.tools = []
        self._initialized = False
        self._config_loaded = False
        self._config = None
    
    def _reset_for_testing(self) -> None:
        """Reset the service for testing purposes"""
        self.client = None
        self.tools = []
        self._initialized = False
        self._config_loaded = False
        self._config = None
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of available tools in Anthropic format"""
        return self.tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool and return the result"""
        if not self.client:
            raise Exception("MCP service not initialized or no servers configured")
        
        try:
            async with self.client:
                result = await self.client.call_tool(name, arguments)
                # FastMCP returns a list of results, we typically want the first one
                if result and len(result) > 0:
                    return result[0].text if hasattr(result[0], 'text') else str(result[0])
                return "Tool executed successfully with no output"
        except Exception as e:
            logger.error(f"Error calling MCP tool {name}: {str(e)}")
            raise Exception(f"Failed to execute tool {name}: {str(e)}")
    
    @property
    def is_available(self) -> bool:
        """Check if MCP service has any tools available"""
        return len(self.tools) > 0


# Create a global instance
mcp_service = MCPService()