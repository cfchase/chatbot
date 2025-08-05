import * as React from 'react';
import { Message, MessageProps } from '@patternfly/chatbot';
import { Modal, ModalVariant, Button, ModalHeader, ModalBody, ModalFooter } from '@patternfly/react-core';
import { DownloadIcon, CopyIcon } from '@patternfly/react-icons';

interface MessageWithImagePreviewProps extends MessageProps {
  content: string;
}

interface ImageModalState {
  isOpen: boolean;
  imageUrl: string;
  altText: string;
}

export const MessageWithImagePreview: React.FunctionComponent<MessageWithImagePreviewProps> = (props) => {
  const [imageModal, setImageModal] = React.useState<ImageModalState>({
    isOpen: false,
    imageUrl: '',
    altText: ''
  });

  const handleCloseModal = () => {
    setImageModal({ isOpen: false, imageUrl: '', altText: '' });
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(imageModal.imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = imageModal.altText || 'image';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading image:', error);
    }
  };

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(imageModal.imageUrl);
  };

  // Process content to add click handlers for images
  React.useEffect(() => {
    // Use a timeout to ensure the Message component has rendered
    const timeout = setTimeout(() => {
      const messageElement = document.getElementById(props.id || '');
      if (messageElement) {
        const images = messageElement.querySelectorAll('img');
        images.forEach((img) => {
          // Add styling
          img.style.maxWidth = '400px';
          img.style.maxHeight = '300px';
          img.style.width = 'auto';
          img.style.height = 'auto';
          img.style.borderRadius = '8px';
          img.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
          img.style.cursor = 'pointer';
          img.style.display = 'block';
          img.style.margin = '8px 0';
          
          // Add click handler
          img.onclick = () => {
            setImageModal({
              isOpen: true,
              imageUrl: img.src,
              altText: img.alt || 'Image'
            });
          };
        });
      }
    }, 100);

    return () => clearTimeout(timeout);
  }, [props.content, props.id]);

  // Transform content to handle plain image URLs
  const transformedContent = React.useMemo(() => {
    let content = props.content;
    
    // Convert plain image URLs to show URL text AND image preview
    const imageUrlRegex = /(^|\s)(https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp|svg)(\?[^\s]*)?)($|\s)/gim;
    content = content.replace(imageUrlRegex, (_match, prefix, url, _ext, _query, suffix) => {
      return `${prefix}${url}\n\n![Image](${url})${suffix}`;
    });
    
    return content;
  }, [props.content]);

  return (
    <>
      <Message {...props} content={transformedContent} />
      
      <Modal
        variant={ModalVariant.large}
        isOpen={imageModal.isOpen}
        onClose={handleCloseModal}
        aria-labelledby="image-preview-modal"
        aria-describedby="image-preview-modal-description"
      >
        <ModalHeader
          title="Image Preview"
          labelId="image-preview-modal"
          descriptorId="image-preview-modal-description"
        />
        <ModalBody>
          <div style={{ textAlign: 'center' }}>
            <img
              src={imageModal.imageUrl}
              alt={imageModal.altText}
              style={{
                maxWidth: '100%',
                maxHeight: '60vh',
                objectFit: 'contain'
              }}
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button key="download" variant="secondary" onClick={handleDownload} icon={<DownloadIcon />}>
            Download
          </Button>
          <Button key="copy" variant="secondary" onClick={handleCopyUrl} icon={<CopyIcon />}>
            Copy URL
          </Button>
          <Button key="close" variant="primary" onClick={handleCloseModal}>
            Close
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
};