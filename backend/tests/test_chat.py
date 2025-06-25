import pytest
import json
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_chat_completion_non_streaming():
    """Test non-streaming chat completion endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/completions",
            json={
                "message": "Hello, test!",
                "stream": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "message" in data
        assert "usage" in data
        
        # Check message structure
        message = data["message"]
        assert "id" in message
        assert "text" in message
        assert message["text"] == "Echo: Hello, test!"
        assert message["sender"] == "bot"
        assert "timestamp" in message
        
        # Check usage statistics
        usage = data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
        assert usage["prompt_tokens"] == 2
        assert usage["completion_tokens"] == 3
        assert usage["total_tokens"] == 5


@pytest.mark.asyncio
async def test_chat_completion_streaming():
    """Test streaming chat completion endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/completions",
            json={
                "message": "Hi",
                "stream": True
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert response.headers["cache-control"] == "no-cache"
        
        # Collect all events
        events = []
        content = ""
        
        # Parse SSE format
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                    if event_data.get("type") == "content":
                        content += event_data.get("content", "")
                except json.JSONDecodeError:
                    pass
        
        # Check that we got events
        assert len(events) > 0
        
        # Check that we got content events
        content_events = [e for e in events if e.get("type") == "content"]
        assert len(content_events) > 0
        
        # Check that we got a done event
        done_events = [e for e in events if e.get("type") == "done"]
        assert len(done_events) == 1
        
        # Check the accumulated content
        assert content == "Echo: Hi"


@pytest.mark.asyncio
async def test_chat_completion_default_no_stream():
    """Test that stream defaults to False when not provided"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/completions",
            json={
                "message": "Test default"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return non-streaming response
        assert "message" in data
        assert data["message"]["text"] == "Echo: Test default"


@pytest.mark.asyncio
async def test_chat_completion_empty_message():
    """Test handling of empty message"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/completions",
            json={
                "message": ""
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"]["text"] == "Echo: "


@pytest.mark.asyncio
async def test_chat_completion_with_user_id():
    """Test chat completion with user_id"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/completions",
            json={
                "message": "Hello",
                "user_id": "test-user-123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"]["text"] == "Echo: Hello"