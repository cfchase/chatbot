import * as React from 'react';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  Form,
  FormGroup,
  PageSection,
  TextArea,
  Stack,
  StackItem,
} from '@patternfly/react-core';
import { PaperPlaneIcon } from '@patternfly/react-icons';

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

  const handleSendMessage = () => {
    if (inputValue.trim()) {
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        text: inputValue,
        sender: 'user',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, newMessage]);
      setInputValue('');

      // Simulate bot response
      setTimeout(() => {
        const botResponse: ChatMessage = {
          id: (Date.now() + 1).toString(),
          text: `I received your message: "${inputValue}". This is a simple echo response.`,
          sender: 'bot',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botResponse]);
      }, 1000);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
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
                  isDisabled={!inputValue.trim()}
                  icon={<PaperPlaneIcon />}
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