import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from .models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage

router = APIRouter()


async def handle_non_streaming_chat(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """
    Handle non-streaming chat completion

    Returns a complete response with the full message
    """
    try:
        # Use LiteLLM service for LLM interactions
        from app.services.litellm_service import litellm_service

        # Determine which format is being used
        conversation_history = None
        message = None

        if request.messages:
            # New format: full conversation history
            conversation_history = request.messages
            # Extract the last user message for echo fallback
            for msg in reversed(request.messages):
                if msg.get("role") == "user":
                    message = msg.get("content", "")
                    break
        else:
            # Legacy format: single message
            message = request.message

        if not litellm_service.is_available:
            # Fallback to echo mode with informative message
            response_text = (
                f"Echo: {message}\n\n"
                f"Note: LLM service is not available. No API key has been provided. "
                f"Please set the API_KEY environment variable to enable LLM."
            )
        else:
            # Use LiteLLM to generate response
            try:
                response_text = await litellm_service.get_completion(
                    message=message or "",
                    user_id=request.user_id,
                    conversation_history=conversation_history
                )
            except Exception as llm_error:
                # If LLM fails, fallback to echo with error message
                response_text = (
                    f"Echo: {message}\n\n"
                    f"Note: LLM encountered an error: {str(llm_error)}"
                )
        
        bot_message = ChatMessage(
            id=str(datetime.now().timestamp()),
            text=response_text,
            sender="bot",
            timestamp=datetime.now()
        )
        
        return ChatCompletionResponse(
            message=bot_message,
            usage={
                "prompt_tokens": len((message or "").split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len((message or "").split()) + len(response_text.split())
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


async def generate_streaming_response(request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
    """
    Generate streaming chat completion response

    Yields Server-Sent Events with incremental content
    """
    try:
        # Use LiteLLM service for LLM interactions
        from app.services.litellm_service import litellm_service

        message_id = str(datetime.now().timestamp())

        # Determine which format is being used
        conversation_history = None
        message = None

        if request.messages:
            # New format: full conversation history
            conversation_history = request.messages
            # Extract the last user message for echo fallback
            for msg in reversed(request.messages):
                if msg.get("role") == "user":
                    message = msg.get("content", "")
                    break
        else:
            # Legacy format: single message
            message = request.message

        if not litellm_service.is_available:
            # Fallback to echo mode with informative message
            full_message = (
                f"Echo: {message}\n\n"
                f"Note: LLM service is not available. No API key has been provided. "
                f"Please set the API_KEY environment variable to enable LLM."
            )

            # Stream the full message character by character
            for char in full_message:
                data = {
                    "id": message_id,
                    "type": "content",
                    "content": char
                }
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(0.01)  # Faster for the notice
        else:
            # Use LiteLLM streaming
            try:
                async for chunk in litellm_service.get_streaming_completion(
                    message=message or "",
                    user_id=request.user_id,
                    conversation_history=conversation_history
                ):
                    data = {
                        "id": message_id,
                        "type": "content",
                        "content": chunk
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            except Exception as llm_error:
                # If LLM fails, send error message
                error_msg = f"\n\nError: LLM encountered an error: {str(llm_error)}"
                for char in error_msg:
                    data = {
                        "id": message_id,
                        "type": "content",
                        "content": char
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    await asyncio.sleep(0.01)
        
        # Send completion message
        completion_data = {
            "id": message_id,
            "type": "done",
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(completion_data)}\n\n"
        
    except Exception as e:
        error_data = {
            "type": "error",
            "error": str(e)
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    """
    Create a chat completion with optional streaming

    This endpoint returns either a JSON response or a Server-Sent Events stream
    based on the 'stream' parameter in the request.

    - stream=false (default): Returns a complete JSON response
    - stream=true: Returns a streaming response using Server-Sent Events

    Supports both legacy single message format and multi-turn conversation history.
    """
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            generate_streaming_response(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable Nginx buffering
            }
        )
    else:
        # Return non-streaming JSON response
        return await handle_non_streaming_chat(request)

