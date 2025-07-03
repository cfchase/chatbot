import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from app.services.claude import claude_service, ClaudeService
from typing import List, Dict, Any


@pytest.fixture
def mock_mcp_tools():
    """Mock MCP tools for testing"""
    return [
        {
            "name": "get_weather",
            "description": "Get weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        },
        {
            "name": "calculate",
            "description": "Perform calculations",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    ]


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client"""
    client = AsyncMock()
    return client


class TestClaudeMCPIntegration:
    """Test Claude service with MCP tool integration"""
    
    @pytest.mark.asyncio
    async def test_get_completion_with_tools(self, mock_anthropic_client, mock_mcp_tools):
        """Test non-streaming completion with MCP tools available"""
        # Create a new service instance for testing
        service = ClaudeService()
        service.client = mock_anthropic_client
        
        # Mock MCP service
        with patch('app.services.claude.mcp_service') as mock_mcp:
            mock_mcp.get_tools.return_value = mock_mcp_tools
            
            # Mock Claude response without tool use
            mock_response = MagicMock()
            mock_text_block = MagicMock()
            mock_text_block.text = "The weather looks nice today!"
            mock_response.content = [mock_text_block]
            mock_anthropic_client.messages.create.return_value = mock_response
            
            # Test completion
            result = await service.get_completion("What's the weather?")
            
            # Verify
            assert result == "The weather looks nice today!"
            mock_anthropic_client.messages.create.assert_called_once()
            
            # Check that tools were included in the call
            call_args = mock_anthropic_client.messages.create.call_args
            assert "tools" in call_args.kwargs
            assert call_args.kwargs["tools"] == mock_mcp_tools
    
    @pytest.mark.asyncio
    async def test_get_completion_without_tools(self, mock_anthropic_client):
        """Test completion when no MCP tools are available"""
        # Create a new service instance for testing
        service = ClaudeService()
        service.client = mock_anthropic_client
        
        # Mock MCP service with no tools
        with patch('app.services.claude.mcp_service') as mock_mcp:
            mock_mcp.get_tools.return_value = []
            
            # Mock Claude response
            mock_response = MagicMock()
            mock_text_block = MagicMock()
            mock_text_block.text = "Hello there!"
            mock_response.content = [mock_text_block]
            mock_anthropic_client.messages.create.return_value = mock_response
            
            # Test completion
            result = await service.get_completion("Hi!")
            
            # Verify
            assert result == "Hello there!"
            call_args = mock_anthropic_client.messages.create.call_args
            assert "tools" not in call_args.kwargs
    
    @pytest.mark.asyncio
    async def test_get_completion_with_tool_use(self, mock_anthropic_client, mock_mcp_tools):
        """Test completion that uses an MCP tool"""
        # Create a new service instance for testing
        service = ClaudeService()
        service.client = mock_anthropic_client
        
        # Mock MCP service
        with patch('app.services.claude.mcp_service') as mock_mcp:
            mock_mcp.get_tools.return_value = mock_mcp_tools
            mock_mcp.call_tool.return_value = "Weather in New York: Sunny, 72°F"
            
            # Mock Claude response with tool use
            tool_use = MagicMock()
            tool_use.type = "tool_use"
            tool_use.id = "tool_123"
            tool_use.name = "get_weather"
            tool_use.input = {"location": "New York"}
            
            # First response uses tool
            mock_response1 = MagicMock()
            mock_text_block1 = MagicMock()
            mock_text_block1.text = "I'll check the weather for you. "
            mock_response1.content = [mock_text_block1, tool_use]
            
            # Second response after tool execution
            mock_response2 = MagicMock()
            mock_text_block2 = MagicMock()
            mock_text_block2.text = "The weather in New York is sunny and 72°F."
            mock_response2.content = [mock_text_block2]
            
            mock_anthropic_client.messages.create.side_effect = [mock_response1, mock_response2]
            
            # Test completion
            result = await service.get_completion("What's the weather in New York?")
            
            # Verify
            assert "I'll check the weather for you." in result
            assert "The weather in New York is sunny and 72°F." in result
            mock_mcp.call_tool.assert_called_once_with("get_weather", {"location": "New York"})
            assert mock_anthropic_client.messages.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_completion_with_tool_error(self, mock_anthropic_client, mock_mcp_tools):
        """Test completion when tool execution fails"""
        # Create a new service instance for testing
        service = ClaudeService()
        service.client = mock_anthropic_client
        
        # Mock MCP service
        with patch('app.services.claude.mcp_service') as mock_mcp:
            mock_mcp.get_tools.return_value = mock_mcp_tools
            mock_mcp.call_tool.side_effect = Exception("Tool execution failed")
            
            # Mock Claude response with tool use
            tool_use = MagicMock()
            tool_use.type = "tool_use"
            tool_use.id = "tool_123"
            tool_use.name = "get_weather"
            tool_use.input = {"location": "Invalid Location"}
            
            # First response uses tool
            mock_response1 = MagicMock()
            mock_response1.content = [tool_use]
            
            # Second response after tool error
            mock_response2 = MagicMock()
            mock_text_block = MagicMock()
            mock_text_block.text = "I encountered an error checking the weather."
            mock_response2.content = [mock_text_block]
            
            mock_anthropic_client.messages.create.side_effect = [mock_response1, mock_response2]
            
            # Test completion
            result = await service.get_completion("What's the weather in Invalid Location?")
            
            # Verify error handling
            assert "I encountered an error" in result
            mock_mcp.call_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_streaming_completion_with_tools(self, mock_anthropic_client, mock_mcp_tools):
        """Test streaming completion with MCP tools"""
        # Create a new service instance for testing
        service = ClaudeService()
        service.client = mock_anthropic_client
        
        # Mock MCP service
        with patch('app.services.claude.mcp_service') as mock_mcp:
            mock_mcp.get_tools.return_value = mock_mcp_tools
            
            # Mock streaming response
            mock_stream = AsyncMock()
            mock_events = [
                MagicMock(type="content_block_delta", delta=MagicMock(text="Hello ")),
                MagicMock(type="content_block_delta", delta=MagicMock(text="there!"))
            ]
            
            async def async_generator():
                for event in mock_events:
                    yield event
            
            mock_stream.__aiter__.return_value = async_generator()
            mock_stream.get_final_message.return_value = MagicMock(content=[])
            
            # Create a proper async context manager mock
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_stream
            async_cm.__aexit__.return_value = None
            mock_anthropic_client.messages.stream.return_value = async_cm
            
            # Test streaming
            chunks = []
            async for chunk in service.get_streaming_completion("Hi!"):
                chunks.append(chunk)
            
            # Verify
            assert chunks == ["Hello ", "there!"]
            mock_anthropic_client.messages.stream.assert_called_once()
            
            # Check that tools were included
            call_args = mock_anthropic_client.messages.stream.call_args
            assert "tools" in call_args.kwargs
            assert call_args.kwargs["tools"] == mock_mcp_tools
    
    @pytest.mark.asyncio
    async def test_streaming_completion_with_tool_use(self, mock_anthropic_client, mock_mcp_tools):
        """Test streaming completion that uses tools"""
        # Create a new service instance for testing
        service = ClaudeService()
        service.client = mock_anthropic_client
        
        # Mock MCP service
        with patch('app.services.claude.mcp_service') as mock_mcp:
            mock_mcp.get_tools.return_value = mock_mcp_tools
            mock_mcp.call_tool.return_value = "Result: 10"
            
            # Mock first stream with tool use
            mock_stream1 = AsyncMock()
            tool_block = MagicMock(
                id="tool_123",
                name="calculate",
                type="tool_use"
            )
            
            mock_events1 = [
                MagicMock(type="content_block_delta", delta=MagicMock(text="Let me calculate that. ")),
                MagicMock(type="content_block_start", content_block=tool_block),
                MagicMock(type="content_block_delta", delta=MagicMock(partial_json='{"expression": "5 + 5"}'))
            ]
            
            async def async_generator1():
                for event in mock_events1:
                    yield event
            
            mock_stream1.__aiter__.return_value = async_generator1()
            mock_text_block = MagicMock()
            mock_text_block.text = "Let me calculate that. "
            mock_stream1.get_final_message.return_value = MagicMock(
                content=[mock_text_block, tool_block]
            )
            
            # Mock second stream after tool execution
            mock_stream2 = AsyncMock()
            mock_events2 = [
                MagicMock(type="content_block_delta", delta=MagicMock(text="The answer is 10."))
            ]
            
            async def async_generator2():
                for event in mock_events2:
                    yield event
            
            mock_stream2.__aiter__.return_value = async_generator2()
            mock_stream2.get_final_message.return_value = MagicMock(content=[])
            
            # Create proper async context managers
            async_cm1 = AsyncMock()
            async_cm1.__aenter__.return_value = mock_stream1
            async_cm1.__aexit__.return_value = None
            
            async_cm2 = AsyncMock()
            async_cm2.__aenter__.return_value = mock_stream2
            async_cm2.__aexit__.return_value = None
            
            # Set up the mock to return different streams
            mock_anthropic_client.messages.stream.side_effect = [async_cm1, async_cm2]
            
            # Test streaming
            chunks = []
            async for chunk in service.get_streaming_completion("What is 5 + 5?"):
                chunks.append(chunk)
            
            # Verify
            assert "Let me calculate that. " in "".join(chunks)
            assert "The answer is 10." in "".join(chunks)
            mock_mcp.call_tool.assert_called_once_with("calculate", {"expression": "5 + 5"})
    
    @pytest.mark.asyncio
    async def test_conversation_history(self, mock_anthropic_client, mock_mcp_tools):
        """Test completion with conversation history"""
        # Create a new service instance for testing
        service = ClaudeService()
        service.client = mock_anthropic_client
        
        # Mock MCP service
        with patch('app.services.claude.mcp_service') as mock_mcp:
            mock_mcp.get_tools.return_value = mock_mcp_tools
            
            # Mock response
            mock_response = MagicMock()
            mock_text_block = MagicMock()
            mock_text_block.text = "Based on our previous discussion..."
            mock_response.content = [mock_text_block]
            mock_anthropic_client.messages.create.return_value = mock_response
            
            # Test with conversation history
            history = [
                {"role": "user", "content": "Tell me about Python"},
                {"role": "assistant", "content": "Python is a programming language..."}
            ]
            
            result = await service.get_completion("What else can you tell me?", conversation_history=history)
            
            # Verify conversation history was used
            call_args = mock_anthropic_client.messages.create.call_args
            messages = call_args.kwargs["messages"]
            assert len(messages) == 3  # Original 2 + new message
            assert messages[0]["content"] == "Tell me about Python"
            assert messages[2]["content"] == "What else can you tell me?"