import pytest
import json
from fastapi.testclient import TestClient
from main import app


def test_chat_completion_non_streaming():
    """Test non-streaming chat completion endpoint"""
    client = TestClient(app)
    response = client.post(
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
    # The response will either be from Claude or echo mode
    assert "Hello, test!" in message["text"] or "Echo: Hello, test!" in message["text"]
    assert message["sender"] == "bot"
    assert "timestamp" in message
    
    # Check usage statistics
    usage = data["usage"]
    assert "prompt_tokens" in usage
    assert "completion_tokens" in usage
    assert "total_tokens" in usage


def test_chat_completion_streaming():
    """Test streaming chat completion endpoint"""
    client = TestClient(app)
    response = client.post(
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
    
    # Check the accumulated content contains the message
    assert "Hi" in content


def test_chat_completion_default_no_stream():
    """Test that stream defaults to False when not provided"""
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "message": "Test default"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return non-streaming response
    assert "message" in data
    assert "Test default" in data["message"]["text"]


def test_chat_completion_empty_message():
    """Test handling of empty message"""
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "message": ""
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    # Empty message handling - either echo or Claude response
    assert "message" in data


def test_chat_completion_with_user_id():
    """Test chat completion with user_id"""
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "message": "Hello",
            "user_id": "test-user-123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Hello" in data["message"]["text"]