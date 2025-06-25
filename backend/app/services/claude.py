from typing import AsyncGenerator, Optional
import logging
from anthropic import AsyncAnthropic
from app.config import settings

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
    
    async def get_completion(self, message: str, user_id: Optional[str] = None) -> str:
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
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            )
            
            # Extract text from the response
            return response.content[0].text if response.content else "No response generated"
            
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
        user_id: Optional[str] = None
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
            async with self.client.messages.stream(
                model=self.model_name,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield event.delta.text
                            
        except Exception as e:
            logger.error(f"Error getting streaming Claude completion: {str(e)}")
            # Add more context to the error
            if "api_key" in str(e).lower():
                raise Exception("Invalid or missing API key")
            elif "rate" in str(e).lower():
                raise Exception("Rate limit exceeded. Please try again later.")
            else:
                raise Exception(f"Claude API error: {str(e)}")


# Create a global instance
claude_service = ClaudeService()