import axios from 'axios';

const API_BASE_URL = '/api/v1';

export interface ChatCompletionRequest {
  message: string;
  user_id?: string;
}

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: string;
}

export interface ChatCompletionResponse {
  message: ChatMessage;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export class ChatAPI {
  static async createChatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    try {
      const response = await axios.post<ChatCompletionResponse>(
        `${API_BASE_URL}/chat/completions`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Error creating chat completion:', error);
      throw error;
    }
  }
}