import * as React from 'react';
import {
  Alert,
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  Form,
  FormGroup,
  PageSection,
  Spinner,
  TextArea,
  Stack,
  StackItem,
} from '@patternfly/react-core';
import { PaperPlaneIcon } from '@patternfly/react-icons';
import { ChatAPI } from '@app/api/chat';

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

  const handleSendMessage = async () => {
    if (inputValue.trim() && !isLoading) {
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        text: inputValue,
        sender: 'user',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInputValue('');
      setIsLoading(true);
      setError(null);

      try {
        const response = await ChatAPI.createChatCompletion({
          message: userMessage.text,
        });

        const botMessage: ChatMessage = {
          ...response.message,
          timestamp: new Date(response.message.timestamp),
        };

        setMessages((prev) => [...prev, botMessage]);
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
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey && !isLoading) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <PageSection hasBodyWrapper={false}>
      <Card style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
        <CardHeader>
          <CardTitle>Chat</CardTitle>
        </CardHeader>
        <CardBody style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          {error && (
            <Alert variant="danger" title={error} isInline onClose={() => setError(null)} style={{ marginBottom: '16px' }} />
          )}
          <Stack hasGutter>
            {messages.map((message) => (
              <StackItem key={message.id}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: '8px',
                  }}
                >
                  <div
                    style={{
                      maxWidth: '70%',
                      padding: '12px',
                      borderRadius: '8px',
                      backgroundColor: message.sender === 'user' ? '#0066cc' : '#f5f5f5',
                      color: message.sender === 'user' ? 'white' : 'black',
                    }}
                  >
                    <div>
                      <p style={{ margin: 0 }}>{message.text}</p>
                      <small
                        style={{
                          opacity: 0.7,
                          marginTop: '4px',
                          color: message.sender === 'user' ? 'rgba(255,255,255,0.8)' : '#666',
                          display: 'block',
                        }}
                      >
                        {message.timestamp.toLocaleTimeString()}
                      </small>
                    </div>
                  </div>
                </div>
              </StackItem>
            ))}
            {isLoading && (
              <StackItem>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Spinner size="md" />
                  <span>Bot is typing...</span>
                </div>
              </StackItem>
            )}
          </Stack>
        </CardBody>
        <div style={{ padding: '16px', borderTop: '1px solid #d2d2d2' }}>
          <Form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}>
            <FormGroup fieldId="message-input">
              <div style={{ display: 'flex', gap: '8px' }}>
                <TextArea
                  id="message-input"
                  value={inputValue}
                  onChange={(_event, value) => setInputValue(value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Type your message..."
                  rows={2}
                  style={{ flex: 1 }}
                />
                <Button
                  variant="primary"
                  onClick={handleSendMessage}
                  isDisabled={!inputValue.trim() || isLoading}
                  icon={<PaperPlaneIcon />}
                  isLoading={isLoading}
                >
                  Send
                </Button>
              </div>
            </FormGroup>
          </Form>
        </div>
      </Card>
    </PageSection>
  );
};

export { Chat };