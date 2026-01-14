import { useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE_URL, type SlidePreviewData } from '../api/client';
import { useGallery } from '../context/GalleryContext';

interface SlideLightboxProps {
  slide: SlidePreviewData | null;
  slides?: SlidePreviewData[];
  onClose: () => void;
  onNavigate?: (direction: 'prev' | 'next') => void;
}

const styles = {
  backdrop: {
    position: 'fixed' as const,
    inset: 0,
    background: 'rgba(0, 0, 0, 0.9)',
    backdropFilter: 'blur(20px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '2rem',
  },
  
  content: {
    position: 'relative' as const,
    display: 'flex',
    gap: '2rem',
    maxWidth: '100%',
    maxHeight: '100%',
  },
  
  imageContainer: {
    position: 'relative' as const,
    maxHeight: 'calc(100vh - 4rem)',
    borderRadius: '16px',
    overflow: 'hidden',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
  },
  
  image: {
    maxHeight: 'calc(100vh - 4rem)',
    maxWidth: 'min(540px, 50vw)',
    objectFit: 'contain' as const,
  },
  
  sidebar: {
    width: '320px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1.5rem',
    color: '#fff',
  },
  
  closeButton: {
    position: 'absolute' as const,
    top: '1rem',
    right: '1rem',
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: 'rgba(255,255,255,0.1)',
    border: '1px solid rgba(255,255,255,0.2)',
    color: '#fff',
    fontSize: '1.25rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    zIndex: 10,
  },
  
  navButton: {
    position: 'absolute' as const,
    top: '50%',
    transform: 'translateY(-50%)',
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    background: 'rgba(255,255,255,0.1)',
    border: '1px solid rgba(255,255,255,0.2)',
    color: '#fff',
    fontSize: '1.5rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    zIndex: 10,
  },
  
  prevButton: {
    left: '1rem',
  },
  
  nextButton: {
    right: '1rem',
  },
  
  sectionTitle: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: 'rgba(255,255,255,0.5)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.1em',
    marginBottom: '0.5rem',
  },
  
  title: {
    fontSize: '1.5rem',
    fontWeight: 600,
    color: '#fff',
    lineHeight: 1.3,
  },
  
  subtitle: {
    fontSize: '1rem',
    color: 'rgba(255,255,255,0.7)',
    lineHeight: 1.5,
    marginTop: '0.5rem',
  },
  
  metaGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
  },
  
  metaItem: {
    background: 'rgba(255,255,255,0.05)',
    borderRadius: '10px',
    padding: '0.75rem',
  },
  
  metaLabel: {
    fontSize: '0.625rem',
    fontWeight: 600,
    color: 'rgba(255,255,255,0.4)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    marginBottom: '0.25rem',
  },
  
  metaValue: {
    fontSize: '0.875rem',
    fontWeight: 500,
    color: '#fff',
  },
  
  actions: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.75rem',
    marginTop: 'auto',
  },
  
  actionButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    padding: '0.875rem 1rem',
    borderRadius: '10px',
    border: 'none',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  
  downloadButton: {
    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    color: '#fff',
  },
  
  galleryButton: {
    background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
    color: '#fff',
  },
  
  galleryButtonAdded: {
    background: 'rgba(34, 197, 94, 0.2)',
    border: '1px solid rgba(34, 197, 94, 0.3)',
    color: '#22c55e',
  },
};

export default function SlideLightbox({ slide, slides = [], onClose, onNavigate }: SlideLightboxProps) {
  const { addSlide, hasItem } = useGallery();
  
  const isInGallery = slide ? hasItem(slide.slide_id) : false;
  const currentIndex = slide ? slides.findIndex(s => s.slide_id === slide.slide_id) : -1;
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex < slides.length - 1;
  
  // Build full image URL
  const imageUrl = slide?.image.url.startsWith('http') 
    ? slide.image.url 
    : `${API_BASE_URL}${slide?.image.url}`;
  
  // Keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowLeft' && hasPrev && onNavigate) {
      onNavigate('prev');
    } else if (e.key === 'ArrowRight' && hasNext && onNavigate) {
      onNavigate('next');
    }
  }, [onClose, onNavigate, hasPrev, hasNext]);
  
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);
  
  const handleDownload = async () => {
    if (!slide) return;
    
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
  
  const handleAddToGallery = () => {
    if (slide && !isInGallery) {
      addSlide(slide);
    }
  };
  
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };
  
  if (!slide) return null;
  
  return (
    <AnimatePresence>
      <motion.div
        style={styles.backdrop}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={handleBackdropClick}
      >
        <motion.button
          style={styles.closeButton}
          onClick={onClose}
          whileHover={{ scale: 1.1, background: 'rgba(255,255,255,0.2)' }}
          whileTap={{ scale: 0.95 }}
        >
          ✕
        </motion.button>
        
        {/* Navigation arrows */}
        {hasPrev && onNavigate && (
          <motion.button
            style={{ ...styles.navButton, ...styles.prevButton }}
            onClick={() => onNavigate('prev')}
            whileHover={{ scale: 1.1, background: 'rgba(255,255,255,0.2)' }}
            whileTap={{ scale: 0.95 }}
          >
            ←
          </motion.button>
        )}
        
        {hasNext && onNavigate && (
          <motion.button
            style={{ ...styles.navButton, ...styles.nextButton }}
            onClick={() => onNavigate('next')}
            whileHover={{ scale: 1.1, background: 'rgba(255,255,255,0.2)' }}
            whileTap={{ scale: 0.95 }}
          >
            →
          </motion.button>
        )}
        
        <motion.div
          style={styles.content}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          {/* Image */}
          <div style={styles.imageContainer}>
            <motion.img
              key={slide.slide_id}
              src={imageUrl}
              alt={slide.content.title || `Slide ${slide.slide_index + 1}`}
              style={styles.image}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2 }}
            />
          </div>
          
          {/* Sidebar */}
          <div style={styles.sidebar}>
            <div>
              <div style={styles.sectionTitle}>Slide {slide.slide_index + 1}</div>
              <h2 style={styles.title}>{slide.content.title || 'Untitled Slide'}</h2>
              {slide.content.subtitle && (
                <p style={styles.subtitle}>{slide.content.subtitle}</p>
              )}
            </div>
            
            <div>
              <div style={styles.sectionTitle}>Settings</div>
              <div style={styles.metaGrid}>
                <div style={styles.metaItem}>
                  <div style={styles.metaLabel}>Font</div>
                  <div style={styles.metaValue}>{slide.settings.font}</div>
                </div>
                <div style={styles.metaItem}>
                  <div style={styles.metaLabel}>Model</div>
                  <div style={styles.metaValue}>{slide.settings.model}</div>
                </div>
                <div style={styles.metaItem}>
                  <div style={styles.metaLabel}>Theme</div>
                  <div style={styles.metaValue}>{slide.settings.theme}</div>
                </div>
                <div style={styles.metaItem}>
                  <div style={styles.metaLabel}>Size</div>
                  <div style={styles.metaValue}>{slide.image.width}×{slide.image.height}</div>
                </div>
              </div>
            </div>
            
            <div style={styles.actions}>
              <motion.button
                style={{ ...styles.actionButton, ...styles.downloadButton }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleDownload}
              >
                ⬇️ Download Image
              </motion.button>
              
              <motion.button
                style={{ 
                  ...styles.actionButton, 
                  ...(isInGallery ? styles.galleryButtonAdded : styles.galleryButton)
                }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleAddToGallery}
                disabled={isInGallery}
              >
                {isInGallery ? '✓ Already in Gallery' : '📁 Add to Gallery'}
              </motion.button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
