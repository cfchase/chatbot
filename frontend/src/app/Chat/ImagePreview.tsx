import * as React from 'react';
import { Modal, ModalVariant, Button, ModalHeader, ModalBody, ModalFooter, Gallery, GalleryItem } from '@patternfly/react-core';
import { DownloadIcon, CopyIcon } from '@patternfly/react-icons';

interface ImagePreviewProps {
  content: string;
}

interface ImageModalState {
  isOpen: boolean;
  imageUrl: string;
  altText: string;
}

interface DetectedImage {
  url: string;
  alt: string;
}

export const ImagePreview: React.FunctionComponent<ImagePreviewProps> = ({ content }) => {
  const [imageModal, setImageModal] = React.useState<ImageModalState>({
    isOpen: false,
    imageUrl: '',
    altText: ''
  });

  // Detect images in content
  const detectedImages = React.useMemo(() => {
    const images: DetectedImage[] = [];
    
    // Detect markdown images: ![alt text](url)
    const markdownImageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
    let match;
    while ((match = markdownImageRegex.exec(content)) !== null) {
      images.push({
        url: match[2],
        alt: match[1] || 'Image'
      });
    }
    
    // Detect plain image URLs
    const imageUrlRegex = /https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp|svg)(\?[^\s]*)?/gi;
    while ((match = imageUrlRegex.exec(content)) !== null) {
      const url = match[0];
      // Check if this URL is already part of a markdown image
      const isMarkdownImage = images.some(img => img.url === url);
      if (!isMarkdownImage) {
        images.push({
          url: url,
          alt: 'Image'
        });
      }
    }
    
    return images;
  }, [content]);

  const handleImageClick = (url: string, alt: string) => {
    setImageModal({ isOpen: true, imageUrl: url, altText: alt });
  };

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
      const filename = imageModal.imageUrl.split('/').pop()?.split('?')[0] || 'image';
      a.download = filename;
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

  // If no images detected, return null
  if (detectedImages.length === 0) {
    return null;
  }

  return (
    <>
      <div style={{ marginTop: '12px' }}>
        <Gallery hasGutter minWidths={{ default: '300px', md: '400px' }}>
          {detectedImages.map((image, index) => (
            <GalleryItem key={`${image.url}-${index}`}>
              <div
                style={{
                  cursor: 'pointer',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                  transition: 'transform 0.2s',
                  backgroundColor: 'var(--pf-v6-global--BackgroundColor--200)'
                }}
                onClick={() => handleImageClick(image.url, image.alt)}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = 'scale(1.02)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                <img
                  src={image.url}
                  alt={image.alt}
                  style={{
                    width: '100%',
                    height: '300px',
                    objectFit: 'cover',
                    display: 'block'
                  }}
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const parent = target.parentElement;
                    if (parent) {
                      parent.innerHTML = `
                        <div style="
                          width: 100%;
                          height: 300px;
                          display: flex;
                          align-items: center;
                          justify-content: center;
                          color: var(--pf-v6-global--danger-color--100);
                          font-size: 14px;
                          padding: 16px;
                          text-align: center;
                        ">
                          Failed to load image
                        </div>
                      `;
                    }
                  }}
                />
              </div>
            </GalleryItem>
          ))}
        </Gallery>
      </div>
      
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