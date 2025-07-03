from typing import AsyncGenerator, Optional, List, Dict, Any
import logging
import json
from anthropic import AsyncAnthropic
from anthropic.types import ToolUseBlock
from app.config import settings
from app.services.mcp_service import mcp_service

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for interacting with Claude API"""
    
    def __init__(self):
        self.client: Optional[AsyncAnthropic] = None
        self.model_name: str = settings.anthropic_model
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Anthropic client if API key is available"""
        if settings.anthropic_api_key:
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            logger.info("Claude client initialized successfully")
            # Model selection will happen on first use
        else:
            logger.warning("No Anthropic API key found. Claude integration disabled.")
    
    
    @property
    def is_available(self) -> bool:
        """Check if Claude service is available"""
        return self.client is not None
    
    async def get_completion(self, message: str, user_id: Optional[str] = None, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Get a non-streaming completion from Claude
        
        Args:
            message: The user's message
            user_id: Optional user identifier for tracking
            
        Returns:
            The Claude response text
            
        Raises:
            Exception: If Claude is not available or API call fails
        """
        if not self.is_available:
            raise Exception("Claude service is not available. Please configure ANTHROPIC_API_KEY.")
        
        
        try:
            # Prepare messages
            messages = conversation_history if conversation_history else []
            if not conversation_history or (conversation_history and conversation_history[-1]["content"] != message):
                messages.append({"role": "user", "content": message})
            
            # Get available MCP tools
            tools = mcp_service.get_tools()
            
            # Create message with or without tools
            create_params = {
                "model": self.model_name,
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature,
                "messages": messages
            }
            
            if tools:
                create_params["tools"] = tools
            
            response = await self.client.messages.create(**create_params)
            
            # Process response and handle tool use
            result_text = ""
            
            for content in response.content:
                if hasattr(content, 'text') and content.text:
                    result_text += content.text
                elif hasattr(content, 'type') and content.type == 'tool_use':
                    # Execute the tool
                    tool_result = await self._execute_tool(content)
                    
                    # Add tool use and result to conversation
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": tool_result
                        }]
                    })
                    
                    # Continue conversation with tool result
                    continuation = await self.get_completion("", user_id, messages)
                    result_text += continuation
                    break
            
            return result_text if result_text else "No response generated"
            
        except Exception as e:
            logger.error(f"Error getting Claude completion: {str(e)}")
            # Add more context to the error
            if "api_key" in str(e).lower():
                raise Exception("Invalid or missing API key")
            elif "rate" in str(e).lower():
                raise Exception("Rate limit exceeded. Please try again later.")
            else:
                raise Exception(f"Claude API error: {str(e)}")
    
    async def get_streaming_completion(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Get a streaming completion from Claude
        
        Args:
            message: The user's message
            user_id: Optional user identifier for tracking
            
        Yields:
            Chunks of text as they are generated
            
        Raises:
            Exception: If Claude is not available or API call fails
        """
        if not self.is_available:
            raise Exception("Claude service is not available. Please configure ANTHROPIC_API_KEY.")
        
        
        try:
            # Prepare messages
            messages = conversation_history if conversation_history else []
            if not conversation_history or (conversation_history and conversation_history[-1]["content"] != message):
                messages.append({"role": "user", "content": message})
            
            # Get available MCP tools
            tools = mcp_service.get_tools()
            
            # Create stream parameters
            stream_params = {
                "model": self.model_name,
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature,
                "messages": messages
            }
            
            if tools:
                stream_params["tools"] = tools
            
            async with self.client.messages.stream(**stream_params) as stream:
                tool_use_blocks = []
                
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield event.delta.text
                    elif event.type == "content_block_start" and hasattr(event.content_block, 'type') and event.content_block.type == "tool_use":
                        # Start collecting tool use data
                        tool_use_blocks.append({
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                            "input": ""
                        })
                    elif event.type == "content_block_delta" and hasattr(event.delta, 'partial_json'):
                        # Accumulate tool input
                        if tool_use_blocks:
                            tool_use_blocks[-1]["input"] += event.delta.partial_json
                
                # After streaming completes, handle any tool uses
                if tool_use_blocks:
                    final_message = await stream.get_final_message()
                    messages.append({"role": "assistant", "content": final_message.content})
                    
                    for tool_block in tool_use_blocks:
                        # Parse the accumulated input
                        try:
                            tool_input = json.loads(tool_block["input"])
                        except json.JSONDecodeError:
                            tool_input = {}
                        
                        # Execute tool
                        tool_result = await mcp_service.call_tool(tool_block["name"], tool_input)
                        
                        # Add tool result to conversation
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": tool_block["id"],
                                "content": tool_result
                            }]
                        })
                    
                    # Continue conversation with tool results
                    async for chunk in self.get_streaming_completion("", user_id, messages):
                        yield chunk
                            
        except Exception as e:
            logger.error(f"Error getting streaming Claude completion: {str(e)}")
            # Add more context to the error
            if "api_key" in str(e).lower():
                raise Exception("Invalid or missing API key")
            elif "rate" in str(e).lower():
                raise Exception("Rate limit exceeded. Please try again later.")
            else:
                raise Exception(f"Claude API error: {str(e)}")
    
    async def _execute_tool(self, tool_use: ToolUseBlock) -> str:
        """
        Execute a tool and return the result
        
        Args:
            tool_use: The tool use block from Claude's response
            
        Returns:
            The tool execution result as a string
        """
        try:
            result = await mcp_service.call_tool(tool_use.name, tool_use.input)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_use.name}: {str(e)}")
            return f"Error executing tool: {str(e)}"


# Create a global instance
claude_service = ClaudeService()