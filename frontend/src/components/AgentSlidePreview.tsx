import { useState } from 'react';
import { motion } from 'framer-motion';
import { API_BASE_URL, type SlidePreviewData } from '../api/client';
import { useGallery } from '../context/GalleryContext';

interface AgentSlidePreviewProps {
  slide: SlidePreviewData;
  onExpand: (slide: SlidePreviewData) => void;
}

const styles = {
  container: {
    display: 'inline-block',
    marginTop: '0.75rem',
    marginBottom: '0.5rem',
  },
  
  card: {
    position: 'relative' as const,
    width: '180px',
    borderRadius: '12px',
    overflow: 'hidden',
    background: 'rgba(0,0,0,0.3)',
    border: '1px solid rgba(255,255,255,0.1)',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  
  imageContainer: {
    position: 'relative' as const,
    width: '180px',
    height: '320px', // 9:16 aspect ratio
    overflow: 'hidden',
  },
  
  image: {
    width: '100%',
    height: '100%',
    objectFit: 'cover' as const,
  },
  
  overlay: {
    position: 'absolute' as const,
    inset: 0,
    background: 'linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 50%)',
    opacity: 0,
    transition: 'opacity 0.2s ease',
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'flex-end',
    padding: '0.75rem',
    gap: '0.5rem',
  },
  
  overlayVisible: {
    opacity: 1,
  },
  
  actionButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.375rem',
    padding: '0.5rem 0.75rem',
    borderRadius: '8px',
    border: 'none',
    fontSize: '0.75rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  
  expandButton: {
    background: 'rgba(255,255,255,0.2)',
    color: '#fff',
    backdropFilter: 'blur(8px)',
  },
  
  downloadButton: {
    background: 'rgba(59, 130, 246, 0.8)',
    color: '#fff',
  },
  
  galleryButton: {
    background: 'rgba(139, 92, 246, 0.8)',
    color: '#fff',
  },
  
  galleryButtonAdded: {
    background: 'rgba(34, 197, 94, 0.8)',
    color: '#fff',
  },
  
  meta: {
    padding: '0.625rem 0.75rem',
    background: 'rgba(0,0,0,0.4)',
    borderTop: '1px solid rgba(255,255,255,0.05)',
  },
  
  slideNumber: {
    fontSize: '0.625rem',
    fontWeight: 600,
    color: '#8b5cf6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    marginBottom: '0.25rem',
  },
  
  title: {
    fontSize: '0.75rem',
    fontWeight: 500,
    color: '#fff',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  
  settings: {
    display: 'flex',
    gap: '0.5rem',
    marginTop: '0.375rem',
  },
  
  settingTag: {
    fontSize: '0.625rem',
    padding: '0.125rem 0.375rem',
    borderRadius: '4px',
    background: 'rgba(255,255,255,0.1)',
    color: 'rgba(255,255,255,0.6)',
  },
};

export default function AgentSlidePreview({ slide, onExpand }: AgentSlidePreviewProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const { addSlide, hasItem } = useGallery();
  const isInGallery = hasItem(slide.slide_id);
  
  // Build full image URL
  const imageUrl = slide.image.url.startsWith('http') 
    ? slide.image.url 
    : `${API_BASE_URL}${slide.image.url}`;
  
  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `slide_${slide.slide_index}_${slide.slide_id}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };
  
  const handleAddToGallery = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isInGallery && !isSaving) {
      setIsSaving(true);
      try {
        await addSlide(slide);
      } catch (error) {
        console.error('Failed to save to gallery:', error);
      } finally {
        setIsSaving(false);
      }
    }
  };
  
  const handleExpand = () => {
    onExpand(slide);
  };
  
  return (
    <motion.div
      style={styles.container}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <motion.div
        style={styles.card}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={handleExpand}
        whileHover={{ scale: 1.02, boxShadow: '0 8px 32px rgba(139, 92, 246, 0.2)' }}
      >
        <div style={styles.imageContainer}>
          <img
            src={imageUrl}
            alt={slide.content.title || `Slide ${slide.slide_index + 1}`}
            style={styles.image}
            loading="lazy"
          />
          
          <div style={{ ...styles.overlay, ...(isHovered ? styles.overlayVisible : {}) }}>
            <motion.button
              style={{ ...styles.actionButton, ...styles.expandButton }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleExpand}
            >
              🔍 Expand
            </motion.button>
            
            <motion.button
              style={{ ...styles.actionButton, ...styles.downloadButton }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleDownload}
            >
              ⬇️ Download
            </motion.button>
            
            <motion.button
              style={{ 
                ...styles.actionButton, 
                ...(isInGallery ? styles.galleryButtonAdded : styles.galleryButton)
              }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleAddToGallery}
              disabled={isInGallery || isSaving}
            >
              {isSaving ? '⏳ Saving...' : isInGallery ? '✓ In Gallery' : '📁 Save to Gallery'}
            </motion.button>
          </div>
        </div>
        
        <div style={styles.meta}>
          <div style={styles.slideNumber}>
            Slide {slide.slide_index + 1}
          </div>
          <div style={styles.title}>
            {slide.content.title || 'Untitled'}
          </div>
          <div style={styles.settings}>
            <span style={styles.settingTag}>{slide.settings.font}</span>
            <span style={styles.settingTag}>{slide.settings.model}</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
