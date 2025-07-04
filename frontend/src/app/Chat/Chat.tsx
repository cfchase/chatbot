import * as React from 'react';
import {
  Alert,
  Button,
  PageSection,
  Switch,
} from '@patternfly/react-core';
import {
  Chatbot,
  ChatbotContent,
  ChatbotDisplayMode,
  ChatbotFooter,
  ChatbotFootnote,
  ChatbotHeader,
  ChatbotHeaderMain,
  ChatbotHeaderTitle,
  ChatbotHeaderActions,
  Message,
  MessageBar,
  MessageBox,
} from '@patternfly/chatbot';
import { ChatAPI, StreamingEvent } from '@app/api/chat';
import aiLogo from '@app/images/ai-logo-transparent.svg';
import avatarImg from '@app/images/user-avatar.svg';

export interface IChatProps {
  sampleProp?: string;
}

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const Chat: React.FunctionComponent<IChatProps> = () => {
  const [messages, setMessages] = React.useState<ChatMessage[]>([
    {
      id: '1',
      text: 'Hello! How can I help you today?',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [streamingMode, setStreamingMode] = React.useState(true);
  const streamControllerRef = React.useRef<EventSource | null>(null);
  const [announcement, setAnnouncement] = React.useState<string | undefined>();

  const handleSendMessage = async (message: string | number) => {
    const messageText = typeof message === 'string' ? message : message.toString();
    
    if (messageText.trim() && !isLoading) {
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        text: messageText,
        sender: 'user',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInputValue('');
      setIsLoading(true);
      setError(null);

      try {
        if (streamingMode) {
          // Streaming mode
          let accumulatedText = '';
          
          const botMessage: ChatMessage = {
            id: Date.now().toString() + '-bot',
            text: '',
            sender: 'bot',
            timestamp: new Date(),
          };
          
          setMessages((prev) => [...prev, botMessage]);
          
          streamControllerRef.current = ChatAPI.createStreamingChatCompletion(
            {
              message: userMessage.text,
              stream: true,
            },
            (event: StreamingEvent) => {
              if (event.type === 'content' && event.content) {
                accumulatedText += event.content;
                setMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (lastMessage && lastMessage.id === botMessage.id) {
                    lastMessage.text = accumulatedText;
                  }
                  return newMessages;
                });
              } else if (event.type === 'done') {
                setIsLoading(false);
                streamControllerRef.current = null;
                setAnnouncement('Message received');
              } else if (event.type === 'error') {
                setError(event.error || 'Streaming error occurred');
                setIsLoading(false);
                streamControllerRef.current = null;
              }
            },
            (error) => {
              console.error('Streaming error:', error);
              setError('Failed to stream message. Please try again.');
              setIsLoading(false);
              streamControllerRef.current = null;
            },
            () => {
              setIsLoading(false);
              streamControllerRef.current = null;
            }
          );
        } else {
          // Non-streaming mode
          const response = await ChatAPI.createChatCompletion({
            message: userMessage.text,
            stream: false,
          });

          const botMessage: ChatMessage = {
            ...response.message,
            timestamp: new Date(response.message.timestamp),
          };

          setMessages((prev) => [...prev, botMessage]);
          setAnnouncement('Message received');
        }
      } catch (err) {
        console.error('Error sending message:', err);
        setError('Failed to send message. Please try again.');
        
        // Add error message to chat
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          text: 'Sorry, I encountered an error. Please try again.',
          sender: 'bot',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        if (!streamingMode) {
          setIsLoading(false);
        }
      }
    }
  };

  const handleStopStreaming = () => {
    if (streamControllerRef.current) {
      streamControllerRef.current.close();
      streamControllerRef.current = null;
      setIsLoading(false);
    }
  };

  // Cleanup streaming on unmount
  React.useEffect(() => {
    return () => {
      if (streamControllerRef.current) {
        streamControllerRef.current.close();
      }
    };
  }, []);

  const displayMode = ChatbotDisplayMode.embedded;

  return (
    <PageSection hasBodyWrapper={false}>
      <Chatbot displayMode={displayMode} isVisible>
        <ChatbotHeader>
          <ChatbotHeaderMain>
            <ChatbotHeaderTitle>Chat</ChatbotHeaderTitle>
            <ChatbotHeaderActions>
              <Switch
                id="streaming-mode"
                label="Streaming mode"
                isChecked={streamingMode}
                onChange={(_event, checked) => setStreamingMode(checked)}
                isDisabled={isLoading}
              />
            </ChatbotHeaderActions>
          </ChatbotHeaderMain>
        </ChatbotHeader>
        <ChatbotContent>
          <MessageBox announcement={announcement} ariaLabel="Chat messages">
            {error && (
              <Alert 
                variant="danger" 
                title={error} 
                isInline 
                actionClose={<Button variant="plain" onClick={() => setError(null)} aria-label="Close alert" />}
                style={{ marginBottom: '16px' }} 
              />
            )}
            {messages.map((message, index) => {
              const isLastBotMessage = 
                message.sender === 'bot' && 
                index === messages.length - 1 && 
                isLoading && 
                streamingMode;

              return (
                <Message
                  key={message.id}
                  id={message.id}
                  role={message.sender === 'user' ? 'user' : 'bot'}
                  content={message.text}
                  timestamp={message.timestamp.toLocaleTimeString()}
                  avatar={message.sender === 'user' ? avatarImg : aiLogo}
                  name={message.sender === 'user' ? 'You' : 'Claude AI'}
                  isLoading={isLastBotMessage}
                />
              );
            })}
            {isLoading && !streamingMode && (
              <Message
                id="loading-message"
                role="bot"
                content=""
                avatar={aiLogo}
                name="Claude AI"
                isLoading
              />
            )}
          </MessageBox>
        </ChatbotContent>
        <ChatbotFooter>
          <MessageBar
            onSendMessage={handleSendMessage}
            hasStopButton={isLoading && streamingMode}
            handleStopButton={handleStopStreaming}
            isSendButtonDisabled={!inputValue.trim() || isLoading}
            value={inputValue}
            onChange={(_event, value) => setInputValue(value as string)}
            placeholder="Type your message..."
          />
          <ChatbotFootnote label="Powered by Claude AI" />
        </ChatbotFooter>
      </Chatbot>
    </PageSection>
  );
};

export { Chat };