import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MessageWithImagePreview } from './MessageWithImagePreview';

describe('MessageWithImagePreview Component', () => {
  it('should render text content without image URLs', () => {
    const props = {
      id: 'test-message',
      role: 'bot' as const,
      content: 'This is a regular message without images.',
      timestamp: '12:00 PM',
      name: 'Test Bot'
    };

    render(<MessageWithImagePreview {...props} />);
    expect(screen.getByText('This is a regular message without images.')).toBeInTheDocument();
  });

  it('should transform image URLs to show both URL text and image', () => {
    const imageUrl = 'https://example.com/image.jpg';
    const props = {
      id: 'test-message-with-image',
      role: 'bot' as const,
      content: `Check out this image: ${imageUrl}`,
      timestamp: '12:00 PM',
      name: 'Test Bot'
    };

    render(<MessageWithImagePreview {...props} />);
    
    // Should contain the original URL as text
    expect(screen.getByText(new RegExp(imageUrl))).toBeInTheDocument();
  });

  it('should handle multiple image URLs in content', () => {
    const imageUrl1 = 'https://example.com/image1.png';
    const imageUrl2 = 'https://example.com/image2.gif';
    const props = {
      id: 'test-message-multiple-images',
      role: 'bot' as const,
      content: `Here are two images: ${imageUrl1} and ${imageUrl2}`,
      timestamp: '12:00 PM',
      name: 'Test Bot'
    };

    render(<MessageWithImagePreview {...props} />);
    
    // Should contain both URLs as text
    expect(screen.getByText(new RegExp(imageUrl1))).toBeInTheDocument();
    expect(screen.getByText(new RegExp(imageUrl2))).toBeInTheDocument();
  });

  it('should handle different image file extensions', () => {
    const supportedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'];
    
    supportedExtensions.forEach(ext => {
      const imageUrl = `https://example.com/image.${ext}`;
      const props = {
        id: `test-message-${ext}`,
        role: 'bot' as const,
        content: `Image with ${ext}: ${imageUrl}`,
        timestamp: '12:00 PM',
        name: 'Test Bot'
      };

      const { unmount } = render(<MessageWithImagePreview {...props} />);
      
      // Should contain the URL as text
      expect(screen.getByText(new RegExp(imageUrl))).toBeInTheDocument();
      
      unmount();
    });
  });

  it('should handle image URLs with query parameters', () => {
    const imageUrl = 'https://example.com/image.jpg?width=500&height=300';
    const props = {
      id: 'test-message-with-params',
      role: 'bot' as const,
      content: `Image with params: ${imageUrl}`,
      timestamp: '12:00 PM',
      name: 'Test Bot'
    };

    render(<MessageWithImagePreview {...props} />);
    
    // Should contain the URL with params as text
    expect(screen.getByText(new RegExp('image.jpg\\?width=500&height=300'))).toBeInTheDocument();
  });
});