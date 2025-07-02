from typing import AsyncGenerator, Optional, Dict, Any, List
import logging
import json
from anthropic import AsyncAnthropic
from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeEnhancedService:
    """Enhanced Claude service with MCP tool integration"""
    
    def __init__(self):
        self.client: Optional[AsyncAnthropic] = None
        self.model_name: str = settings.anthropic_model
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Anthropic client if API key is available"""
        if settings.anthropic_api_key:
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            logger.info("Enhanced Claude client initialized successfully")
        else:
            logger.warning("No Anthropic API key found. Claude integration disabled.")
    
    @property
    def is_available(self) -> bool:
        """Check if Claude service is available"""
        return self.client is not None
    
    def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available MCP tools for Claude"""
        try:
            from app.services.mcp_service import mcp_service
            return mcp_service.get_tools_for_claude()
        except Exception as e:
            logger.error(f"Error getting MCP tools: {str(e)}")
            return []
    
    def _execute_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute an MCP tool and return the result"""
        try:
            from app.services.mcp_service import mcp_service
            return mcp_service.execute_tool(tool_name, parameters)
        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}: {str(e)}")
            return f"Error executing tool {tool_name}: {str(e)}"
    
    async def get_completion_with_tools(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Get a completion from Claude with MCP tools available
        
        Args:
            message: The user's message
            user_id: Optional user identifier for tracking
            conversation_history: Optional conversation history
            
        Returns:
            The Claude response text, potentially using tools
        """
        if not self.is_available:
            raise Exception("Claude service is not available. Please configure ANTHROPIC_API_KEY.")
        
        assert self.client is not None  # Type hint for linter
        
        try:
            # Get available MCP tools
            tools = self._get_mcp_tools()
            
            # Prepare messages
            messages = []
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Make the API call with tools if available
            if tools:
                response = await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=settings.max_tokens,
                    temperature=settings.temperature,
                    messages=messages,
                    tools=tools
                )
            else:
                response = await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=settings.max_tokens,
                    temperature=settings.temperature,
                    messages=messages
                )
            
            # Process the response
            final_response = ""
            
            for content in response.content:
                if content.type == "text":
                    final_response += content.text
                elif content.type == "tool_use":
                    # Execute the tool
                    tool_name = content.name
                    tool_parameters = content.input
                    
                    logger.info(f"Executing tool: {tool_name} with parameters: {tool_parameters}")
                    
                    tool_result = self._execute_mcp_tool(tool_name, tool_parameters)
                    
                    # Add tool result to response
                    final_response += f"\n\n**Tool used: {tool_name}**\n{tool_result}"
            
            return final_response if final_response else "No response generated"
            
        except Exception as e:
            logger.error(f"Error getting Claude completion with tools: {str(e)}")
            # Add more context to the error
            if "api_key" in str(e).lower():
                raise Exception("Invalid or missing API key")
            elif "rate" in str(e).lower():
                raise Exception("Rate limit exceeded. Please try again later.")
            else:
                raise Exception(f"Claude API error: {str(e)}")
    
    async def get_streaming_completion_with_tools(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Get a streaming completion from Claude with MCP tools available
        
        Args:
            message: The user's message
            user_id: Optional user identifier for tracking
            conversation_history: Optional conversation history
            
        Yields:
            Chunks of text as they are generated
        """
        if not self.is_available:
            raise Exception("Claude service is not available. Please configure ANTHROPIC_API_KEY.")
        
        assert self.client is not None  # Type hint for linter
        
        try:
            # Get available MCP tools
            tools = self._get_mcp_tools()
            
            # Prepare messages
            messages = []
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Track tool use for streaming
            tool_uses = []
            current_tool_use = None
            
            # Make the streaming API call with tools if available
            if tools:
                async with self.client.messages.stream(
                    model=self.model_name,
                    max_tokens=settings.max_tokens,
                    temperature=settings.temperature,
                    messages=messages,
                    tools=tools
                ) as stream:
                    async for event in stream:
                        if event.type == "content_block_start":
                            if event.content_block.type == "tool_use":
                                current_tool_use = {
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": {}
                                }
                        elif event.type == "content_block_delta":
                            if hasattr(event.delta, 'text'):
                                yield event.delta.text
                            elif hasattr(event.delta, 'partial_json') and current_tool_use:
                                # This is tool input being built up
                                try:
                                    # Try to parse the partial JSON
                                    current_tool_use["input"] = json.loads(event.delta.partial_json)
                                except json.JSONDecodeError:
                                    # Still building up the JSON
                                    pass
                        elif event.type == "content_block_stop":
                            if current_tool_use:
                                tool_uses.append(current_tool_use)
                                current_tool_use = None
                
                # Execute any tools that were used
                for tool_use in tool_uses:
                    tool_name = tool_use["name"]
                    tool_parameters = tool_use["input"]
                    
                    yield f"\n\n**Using tool: {tool_name}**\n"
                    
                    tool_result = self._execute_mcp_tool(tool_name, tool_parameters)
                    yield tool_result
            else:
                # No tools available, stream normally
                async with self.client.messages.stream(
                    model=self.model_name,
                    max_tokens=settings.max_tokens,
                    temperature=settings.temperature,
                    messages=messages
                ) as stream:
                    async for event in stream:
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, 'text'):
                                yield event.delta.text
                            
        except Exception as e:
            logger.error(f"Error getting streaming Claude completion with tools: {str(e)}")
            # Add more context to the error
            if "api_key" in str(e).lower():
                raise Exception("Invalid or missing API key")
            elif "rate" in str(e).lower():
                raise Exception("Rate limit exceeded. Please try again later.")
            else:
                raise Exception(f"Claude API error: {str(e)}")
    
    # Backward compatibility methods
    async def get_completion(self, message: str, user_id: Optional[str] = None) -> str:
        """Backward compatible completion method"""
        return await self.get_completion_with_tools(message, user_id)
    
    async def get_streaming_completion(
        self, 
        message: str, 
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Backward compatible streaming completion method"""
        async for chunk in self.get_streaming_completion_with_tools(message, user_id):
            yield chunk


# Create a global instance
claude_enhanced_service = ClaudeEnhancedService()