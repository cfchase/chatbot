import json
import logging
import uuid
import base64
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import random

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


class MCPService:
    """Service for managing MCP server and tools"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.mcp_server: Optional[FastMCP] = None
        self._load_config()
        self._setup_mcp_server()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded MCP configuration from {self.config_path}")
            else:
                logger.warning(f"Config file {self.config_path} not found. Using empty configuration.")
                self.config = {"mcp_server": {"name": "default-server", "tools": [], "resources": []}}
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            self.config = {"mcp_server": {"name": "default-server", "tools": [], "resources": []}}
    
    def _setup_mcp_server(self):
        """Initialize the FastMCP server with tools from config"""
        server_config = self.config.get("mcp_server", {})
        server_name = server_config.get("name", "chatbot-mcp-server")
        
        self.mcp_server = FastMCP(server_name)
        
        # Register tools from config
        self._register_tools()
        self._register_resources()
        
        logger.info(f"MCP server '{server_name}' initialized with {len(server_config.get('tools', []))} tools")
    
    def _register_tools(self):
        """Register all tools defined in the configuration"""
        tools = self.config.get("mcp_server", {}).get("tools", [])
        
        for tool_config in tools:
            tool_name = tool_config.get("name")
            if tool_name:
                self._register_tool(tool_name, tool_config)
    
    def _register_tool(self, tool_name: str, tool_config: Dict[str, Any]):
        """Register a single tool with the MCP server"""
        if not self.mcp_server:
            logger.error("MCP server not initialized")
            return
            
        try:
            if tool_name == "get_current_time":
                @self.mcp_server.tool()
                def get_current_time(timezone: str = "UTC") -> str:
                    """Get the current date and time"""
                    try:
                        import pytz
                        tz = pytz.timezone(timezone) if timezone != "UTC" else pytz.UTC
                        now = datetime.now(tz)
                        return f"Current time in {timezone}: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                    except Exception:
                        # Fallback if pytz is not available
                        now = datetime.now()
                        return f"Current time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}"
            
            elif tool_name == "calculate":
                @self.mcp_server.tool()
                def calculate(expression: str) -> str:
                    """Perform basic mathematical calculations"""
                    try:
                        # Basic safety check - only allow safe mathematical operations
                        allowed_chars = set("0123456789+-*/.() ")
                        if not all(c in allowed_chars for c in expression):
                            return "Error: Invalid characters in expression. Only numbers and basic operators (+, -, *, /, parentheses) are allowed."
                        
                        result = eval(expression)
                        return f"Result: {expression} = {result}"
                    except Exception as e:
                        return f"Error calculating '{expression}': {str(e)}"
            
            elif tool_name == "generate_uuid":
                @self.mcp_server.tool()
                def generate_uuid(version: int = 4) -> str:
                    """Generate a random UUID"""
                    try:
                        if version == 1:
                            result = str(uuid.uuid1())
                        else:
                            result = str(uuid.uuid4())
                        return f"Generated UUID (version {version}): {result}"
                    except Exception as e:
                        return f"Error generating UUID: {str(e)}"
            
            elif tool_name == "encode_decode_text":
                @self.mcp_server.tool()
                def encode_decode_text(text: str, operation: str) -> str:
                    """Encode or decode text using various methods"""
                    try:
                        if operation == "base64_encode":
                            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
                            return f"Base64 encoded: {encoded}"
                        elif operation == "base64_decode":
                            decoded = base64.b64decode(text).decode('utf-8')
                            return f"Base64 decoded: {decoded}"
                        elif operation == "url_encode":
                            encoded = urllib.parse.quote(text)
                            return f"URL encoded: {encoded}"
                        elif operation == "url_decode":
                            decoded = urllib.parse.unquote(text)
                            return f"URL decoded: {decoded}"
                        else:
                            return f"Error: Unknown operation '{operation}'"
                    except Exception as e:
                        return f"Error during {operation}: {str(e)}"
            
            elif tool_name == "weather_info":
                @self.mcp_server.tool()
                def weather_info(location: str, units: str = "celsius") -> str:
                    """Get weather information for a location (mock data)"""
                    try:
                        # Generate mock weather data
                        temp_base = random.randint(15, 30) if units == "celsius" else random.randint(60, 85)
                        conditions = ["sunny", "partly cloudy", "cloudy", "rainy", "snowy"]
                        condition = random.choice(conditions)
                        humidity = random.randint(30, 80)
                        wind_speed = random.randint(5, 25)
                        
                        temp_unit = "°C" if units == "celsius" else "°F"
                        
                        return f"""Weather for {location}:
- Temperature: {temp_base}{temp_unit}
- Condition: {condition.title()}
- Humidity: {humidity}%
- Wind Speed: {wind_speed} km/h
- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Note: This is mock weather data for demonstration purposes."""
                    except Exception as e:
                        return f"Error getting weather for {location}: {str(e)}"
            
            logger.info(f"Registered tool: {tool_name}")
            
        except Exception as e:
            logger.error(f"Error registering tool {tool_name}: {str(e)}")
    
    def _register_resources(self):
        """Register resources defined in the configuration"""
        resources = self.config.get("mcp_server", {}).get("resources", [])
        
        for resource_config in resources:
            resource_name = resource_config.get("name")
            resource_uri = resource_config.get("uri")
            
            if resource_name and resource_uri:
                self._register_resource(resource_name, resource_uri, resource_config)
    
    def _register_resource(self, resource_name: str, resource_uri: str, resource_config: Dict[str, Any]):
        """Register a single resource with the MCP server"""
        if not self.mcp_server:
            logger.error("MCP server not initialized")
            return
            
        try:
            if resource_uri == "status://health":
                @self.mcp_server.resource(resource_uri)
                def server_status() -> str:
                    """Get the current server status and health information"""
                    status_info = {
                        "status": "healthy",
                        "timestamp": datetime.now().isoformat(),
                        "server_name": self.config.get("mcp_server", {}).get("name", "unknown"),
                        "version": self.config.get("mcp_server", {}).get("version", "unknown"),
                        "tools_count": len(self.config.get("mcp_server", {}).get("tools", [])),
                        "resources_count": len(self.config.get("mcp_server", {}).get("resources", []))
                    }
                    return json.dumps(status_info, indent=2)
            
            elif resource_uri == "tools://list":
                @self.mcp_server.resource(resource_uri)
                def available_tools() -> str:
                    """List all available tools and their descriptions"""
                    tools = self.config.get("mcp_server", {}).get("tools", [])
                    tool_list = []
                    for tool in tools:
                        tool_info = {
                            "name": tool.get("name"),
                            "description": tool.get("description"),
                            "parameters": tool.get("parameters", {})
                        }
                        tool_list.append(tool_info)
                    return json.dumps({"tools": tool_list}, indent=2)
            
            logger.info(f"Registered resource: {resource_name} ({resource_uri})")
            
        except Exception as e:
            logger.error(f"Error registering resource {resource_name}: {str(e)}")
    
    def get_mcp_server(self) -> Optional[FastMCP]:
        """Get the FastMCP server instance"""
        return self.mcp_server
    
    def get_tools_for_claude(self) -> list[dict]:
        """Get tool definitions formatted for Claude API"""
        tools = []
        tool_configs = self.config.get("mcp_server", {}).get("tools", [])
        
        for tool_config in tool_configs:
            claude_tool = {
                "name": tool_config.get("name"),
                "description": tool_config.get("description"),
                "input_schema": tool_config.get("parameters", {})
            }
            tools.append(claude_tool)
        
        return tools
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with given parameters"""
        try:
            # This is a simple implementation - in a real scenario,
            # you'd want to properly integrate with the MCP server's tool execution
            if tool_name == "get_current_time":
                timezone = parameters.get("timezone", "UTC")
                try:
                    import pytz
                    tz = pytz.timezone(timezone) if timezone != "UTC" else pytz.UTC
                    now = datetime.now(tz)
                    return f"Current time in {timezone}: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                except Exception:
                    now = datetime.now()
                    return f"Current time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}"
            
            elif tool_name == "calculate":
                expression = parameters.get("expression", "")
                allowed_chars = set("0123456789+-*/.() ")
                if not all(c in allowed_chars for c in expression):
                    return "Error: Invalid characters in expression."
                result = eval(expression)
                return f"Result: {expression} = {result}"
            
            elif tool_name == "generate_uuid":
                version = parameters.get("version", 4)
                if version == 1:
                    result = str(uuid.uuid1())
                else:
                    result = str(uuid.uuid4())
                return f"Generated UUID (version {version}): {result}"
            
            elif tool_name == "encode_decode_text":
                text = parameters.get("text", "")
                operation = parameters.get("operation", "")
                
                if operation == "base64_encode":
                    encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
                    return f"Base64 encoded: {encoded}"
                elif operation == "base64_decode":
                    decoded = base64.b64decode(text).decode('utf-8')
                    return f"Base64 decoded: {decoded}"
                elif operation == "url_encode":
                    encoded = urllib.parse.quote(text)
                    return f"URL encoded: {encoded}"
                elif operation == "url_decode":
                    decoded = urllib.parse.unquote(text)
                    return f"URL decoded: {decoded}"
                else:
                    return f"Error: Unknown operation '{operation}'"
            
            elif tool_name == "weather_info":
                location = parameters.get("location", "")
                units = parameters.get("units", "celsius")
                
                temp_base = random.randint(15, 30) if units == "celsius" else random.randint(60, 85)
                conditions = ["sunny", "partly cloudy", "cloudy", "rainy", "snowy"]
                condition = random.choice(conditions)
                humidity = random.randint(30, 80)
                wind_speed = random.randint(5, 25)
                
                temp_unit = "°C" if units == "celsius" else "°F"
                
                return f"""Weather for {location}:
- Temperature: {temp_base}{temp_unit}
- Condition: {condition.title()}
- Humidity: {humidity}%
- Wind Speed: {wind_speed} km/h
- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Note: This is mock weather data for demonstration purposes."""
            
            else:
                return f"Error: Unknown tool '{tool_name}'"
                
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"


# Create a global instance
mcp_service = MCPService()