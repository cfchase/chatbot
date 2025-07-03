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
            mock_text_block.type = "text"
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
            mock_text_block.type = "text"
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
            mock_mcp.call_tool = AsyncMock(return_value="Weather in New York: Sunny, 72°F")
            
            # Mock Claude response with tool use
            tool_use = MagicMock(spec=['type', 'id', 'name', 'input'])
            tool_use.type = "tool_use"
            tool_use.id = "tool_123"
            tool_use.name = "get_weather"
            tool_use.input = {"location": "New York"}
            
            # First response uses tool - use spec to avoid magic method issues
            mock_response1 = MagicMock()
            mock_text_block1 = MagicMock(spec=['text', 'type'])
            mock_text_block1.text = "I'll check the weather for you. "
            mock_text_block1.type = "text"
            mock_response1.content = [mock_text_block1, tool_use]
            
            # Second response after tool execution
            mock_response2 = MagicMock()
            mock_text_block2 = MagicMock(spec=['text', 'type'])
            mock_text_block2.text = "The weather in New York is sunny and 72°F."
            mock_text_block2.type = "text"
            mock_response2.content = [mock_text_block2]
            
            mock_anthropic_client.messages.create.side_effect = [mock_response1, mock_response2]
            
            # Test completion
            result = await service.get_completion("What's the weather in New York?")
            
            # Verify - The result should contain both the initial response and the continuation
            assert result == "I'll check the weather for you. The weather in New York is sunny and 72°F."
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
            tool_use = MagicMock(spec=['type', 'id', 'name', 'input'])
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
            mock_text_block.type = "text"
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
            mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_stream.__aexit__ = AsyncMock(return_value=None)
            
            mock_events = [
                MagicMock(type="content_block_delta", delta=MagicMock(text="Hello ")),
                MagicMock(type="content_block_delta", delta=MagicMock(text="there!"))
            ]
            
            # Create async iterator that yields events
            async def event_iterator():
                for event in mock_events:
                    yield event
            
            # Make the mock stream async iterable
            mock_stream.__aiter__ = lambda self: event_iterator()
            mock_stream.get_final_message = AsyncMock(return_value=MagicMock(content=[]))
            
            # Mock the stream method to return the async context manager
            # The stream method itself should be a regular method that returns the context manager
            mock_anthropic_client.messages.stream = MagicMock(return_value=mock_stream)
            
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
            mock_mcp.call_tool = AsyncMock(return_value="Result: 10")
            
            # Mock first stream with tool use
            mock_stream1 = AsyncMock()
            mock_stream1.__aenter__ = AsyncMock(return_value=mock_stream1)
            mock_stream1.__aexit__ = AsyncMock(return_value=None)
            
            tool_block = MagicMock(spec=['id', 'name', 'type'])
            tool_block.id = "tool_123"
            tool_block.name = "calculate"
            tool_block.type = "tool_use"
            
            # Create events with proper specs
            event1 = MagicMock(spec=['type', 'delta'])
            event1.type = "content_block_delta"
            delta1 = MagicMock(spec=['text'])
            delta1.text = "Let me calculate that. "
            event1.delta = delta1
            
            event2 = MagicMock(spec=['type', 'content_block'])
            event2.type = "content_block_start"
            event2.content_block = tool_block
            
            event3 = MagicMock(spec=['type', 'delta'])
            event3.type = "content_block_delta"
            delta3 = MagicMock(spec=['partial_json'])
            delta3.partial_json = '{"expression": "5 + 5"}'
            event3.delta = delta3
            
            mock_events1 = [event1, event2, event3]
            
            # Create async iterator for first stream
            async def event_iterator1():
                for event in mock_events1:
                    yield event
            
            mock_stream1.__aiter__ = lambda self: event_iterator1()
            mock_text_block = MagicMock(spec=['text', 'type'])
            mock_text_block.text = "Let me calculate that. "
            mock_stream1.get_final_message = AsyncMock(return_value=MagicMock(
                content=[mock_text_block, tool_block]
            ))
            
            # Mock second stream after tool execution
            mock_stream2 = AsyncMock()
            mock_stream2.__aenter__ = AsyncMock(return_value=mock_stream2)
            mock_stream2.__aexit__ = AsyncMock(return_value=None)
            
            # Create event for second stream with proper spec
            event4 = MagicMock(spec=['type', 'delta'])
            event4.type = "content_block_delta"
            delta4 = MagicMock(spec=['text'])
            delta4.text = "The answer is 10."
            event4.delta = delta4
            
            mock_events2 = [event4]
            
            # Create async iterator for second stream
            async def event_iterator2():
                for event in mock_events2:
                    yield event
            
            mock_stream2.__aiter__ = lambda self: event_iterator2()
            mock_stream2.get_final_message = AsyncMock(return_value=MagicMock(content=[]))
            
            # Set up the mock to return different streams
            mock_anthropic_client.messages.stream = MagicMock(side_effect=[mock_stream1, mock_stream2])
            
            # Test streaming
            chunks = []
            async for chunk in service.get_streaming_completion("What is 5 + 5?"):
                chunks.append(chunk)
            
            # Verify
            all_text = "".join(chunks)
            assert "Let me calculate that. " in all_text
            assert "The answer is 10." in all_text
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
            mock_text_block.type = "text"
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