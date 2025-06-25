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
        # Check if we have Claude service available
        from app.services.claude import claude_service
        
        if not claude_service.is_available:
            # Fallback to echo mode with informative message
            response_text = (
                f"Echo: {request.message}\n\n"
                f"Note: Claude AI is not available. No Anthropic API key has been provided. "
                f"Please set the ANTHROPIC_API_KEY environment variable to enable Claude."
            )
        else:
            # Use Claude to generate response
            try:
                response_text = await claude_service.get_completion(
                    message=request.message,
                    user_id=request.user_id
                )
            except Exception as claude_error:
                # If Claude fails, fallback to echo with error message
                response_text = (
                    f"Echo: {request.message}\n\n"
                    f"Note: Claude encountered an error: {str(claude_error)}"
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
                "prompt_tokens": len(request.message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(request.message.split()) + len(response_text.split())
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
        # Check if we have Claude service available
        from app.services.claude import claude_service
        
        message_id = str(datetime.now().timestamp())
        
        if not claude_service.is_available:
            # Fallback to echo mode with informative message
            full_message = (
                f"Echo: {request.message}\n\n"
                f"Note: Claude AI is not available. No Anthropic API key has been provided. "
                f"Please set the ANTHROPIC_API_KEY environment variable to enable Claude."
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
            # This will be replaced with actual Claude streaming in Phase 8
            # For now, simulate streaming by echoing back
            response_prefix = "Echo: "
            
            # Stream the prefix first
            for char in response_prefix:
                data = {
                    "id": message_id,
                    "type": "content",
                    "content": char
                }
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(0.02)
            
            # Stream each word
            words = request.message.split()
            for i, word in enumerate(words):
                # Add space before word if not first word
                if i > 0:
                    data = {
                        "id": message_id,
                        "type": "content",
                        "content": " "
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                
                # Stream each character of the word
                for char in word:
                    data = {
                        "id": message_id,
                        "type": "content",
                        "content": char
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    await asyncio.sleep(0.02)
        
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
    
    It will be updated to use Claude AI in a future iteration.
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

