from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatCompletionRequest(BaseModel):
    """Request model for chat completions"""
    message: Optional[str] = Field(None, description="The user's message to send to the chatbot (legacy format)")
    messages: Optional[List[Dict[str, Any]]] = Field(None, description="Full conversation history in OpenAI format")
    stream: bool = Field(False, description="Whether to stream the response")
    user_id: str | None = Field(None, description="Optional user identifier")


class ChatMessage(BaseModel):
    """Individual chat message"""
    id: str = Field(..., description="Unique message identifier")
    text: str = Field(..., description="Message content")
    sender: Literal["user", "bot"] = Field(..., description="Message sender")
    timestamp: datetime = Field(..., description="Message timestamp")


class ChatCompletionResponse(BaseModel):
    """Response model for chat completions"""
    message: ChatMessage = Field(..., description="The response message from the chatbot")
    usage: dict | None = Field(None, description="Optional usage statistics")