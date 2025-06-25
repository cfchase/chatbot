from datetime import datetime
from fastapi import APIRouter, HTTPException
from .models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage

router = APIRouter()


@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """
    Create a chat completion (dummy endpoint that echoes the prompt)
    
    This endpoint currently returns a simple echo of the user's message.
    It will be updated to use Claude AI in a future iteration.
    """
    try:
        # For now, just echo back the user's message
        response_text = f"Echo: {request.message}"
        
        # Create the response message
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