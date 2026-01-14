import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE_URL, type SlidePreviewData } from '../api/client';
import { useGallery, type GalleryItem } from '../context/GalleryContext';
import SlideLightbox from './SlideLightbox';

interface GalleryPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const styles = {
  backdrop: {
    position: 'fixed' as const,
    inset: 0,
    background: 'rgba(0, 0, 0, 0.5)',
    backdropFilter: 'blur(4px)',
    zIndex: 900,
  },
  
  panel: {
    position: 'fixed' as const,
    top: 0,
    right: 0,
    width: '420px',
    height: '100vh',
    background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%)',
    borderLeft: '1px solid rgba(255,255,255,0.1)',
    display: 'flex',
    flexDirection: 'column' as const,
    zIndex: 950,
    overflow: 'hidden',
  },
  
  header: {
    padding: '1.5rem',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  
  title: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  
  count: {
    fontSize: '0.75rem',
    fontWeight: 500,
    padding: '0.25rem 0.5rem',
    borderRadius: '999px',
    background: 'rgba(139, 92, 246, 0.2)',
    color: '#a78bfa',
  },
  
  closeButton: {
    width: '32px',
    height: '32px',
    borderRadius: '8px',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    color: '#fff',
    fontSize: '1rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
  },
  
  controls: {
    padding: '1rem 1.5rem',
    borderBottom: '1px solid rgba(255,255,255,0.05)',
    display: 'flex',
    gap: '0.75rem',
  },
  
  filterButton: {
    flex: 1,
    padding: '0.625rem',
    borderRadius: '8px',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    color: 'rgba(255,255,255,0.7)',
    fontSize: '0.8125rem',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  
  filterButtonActive: {
    background: 'rgba(139, 92, 246, 0.2)',
    borderColor: 'rgba(139, 92, 246, 0.3)',
    color: '#a78bfa',
  },
  
  content: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '1rem',
  },
  
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '0.75rem',
  },
  
  slideCard: {
    position: 'relative' as const,
    borderRadius: '10px',
    overflow: 'hidden',
    background: 'rgba(0,0,0,0.3)',
    border: '1px solid rgba(255,255,255,0.1)',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  
  slideImage: {
    width: '100%',
    aspectRatio: '9 / 16',
    objectFit: 'cover' as const,
  },
  
  slideMeta: {
    position: 'absolute' as const,
    bottom: 0,
    left: 0,
    right: 0,
    padding: '0.5rem',
    background: 'linear-gradient(to top, rgba(0,0,0,0.9) 0%, transparent 100%)',
  },
  
  slideTitle: {
    fontSize: '0.6875rem',
    fontWeight: 500,
    color: '#fff',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  
  slideDate: {
    fontSize: '0.5625rem',
    color: 'rgba(255,255,255,0.5)',
    marginTop: '0.125rem',
  },
  
  deleteButton: {
    position: 'absolute' as const,
    top: '0.375rem',
    right: '0.375rem',
    width: '24px',
    height: '24px',
    borderRadius: '6px',
    background: 'rgba(239, 68, 68, 0.8)',
    border: 'none',
    color: '#fff',
    fontSize: '0.75rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0,
    transition: 'opacity 0.2s ease',
  },
  
  emptyState: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    padding: '3rem',
    textAlign: 'center' as const,
  },
  
  emptyIcon: {
    width: '64px',
    height: '64px',
    borderRadius: '16px',
    background: 'rgba(139, 92, 246, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.75rem',
    marginBottom: '1rem',
  },
  
  emptyTitle: {
    fontSize: '1rem',
    fontWeight: 500,
    color: '#fff',
    marginBottom: '0.5rem',
  },
  
  emptyText: {
    fontSize: '0.8125rem',
    color: 'rgba(255,255,255,0.5)',
    lineHeight: 1.5,
  },
  
  footer: {
    padding: '1rem 1.5rem',
    borderTop: '1px solid rgba(255,255,255,0.08)',
    display: 'flex',
    gap: '0.75rem',
  },
  
  footerButton: {
    flex: 1,
    padding: '0.75rem',
    borderRadius: '8px',
    border: 'none',
    fontSize: '0.8125rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.375rem',
  },
  
  downloadAllButton: {
    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    color: '#fff',
  },
  
  clearButton: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    color: '#ef4444',
  },
};

type FilterType = 'all' | 'recent' | 'project';

// Convert GalleryItem to SlidePreviewData for lightbox
function itemToSlidePreview(item: GalleryItem): SlidePreviewData {
  return {
    slide_id: item.slide_id || item.id,
    slide_index: (item.metadata as Record<string, unknown>)?.slide_index as number || 0,
    project_id: item.project_id || '',
    content: {
      title: item.title,
      subtitle: item.subtitle,
    },
    image: {
      url: item.image_url || '',
      background_url: (item.metadata as Record<string, unknown>)?.background_url as string || null,
      width: (item.metadata as Record<string, unknown>)?.image_width as number || 1080,
      height: (item.metadata as Record<string, unknown>)?.image_height as number || 1920,
    },
    settings: {
      font: item.font || 'social',
      theme: item.theme || 'golden_dust',
      model: item.content_style || 'gpt15',
    },
  };
}

export default function GalleryPanel({ isOpen, onClose }: GalleryPanelProps) {
  const { items, removeItem, clearGallery } = useGallery();
  const [filter, setFilter] = useState<FilterType>('all');
  const [selectedItem, setSelectedItem] = useState<GalleryItem | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  
  // Filter items
  const filteredItems = useMemo(() => {
    let filtered = [...items];
    
    if (filter === 'recent') {
      // Last 24 hours
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
      filtered = filtered.filter((s) => s.created_at && s.created_at > yesterday);
    }
    
    // Sort by created_at descending
    return filtered.sort((a, b) => 
      new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
    );
  }, [items, filter]);
  
  // Get unique projects
  const projectCount = useMemo(() => {
    return new Set(items.filter(s => s.project_id).map((s) => s.project_id)).size;
  }, [items]);
  
  const handleDownloadAll = async () => {
    for (const item of filteredItems) {
      if (!item.image_url) continue;
      try {
        const imageUrl = item.image_url.startsWith('http') 
          ? item.image_url 
          : `${API_BASE_URL}${item.image_url}`;
        
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${item.item_type}_${item.id}.png`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Small delay between downloads
        await new Promise((resolve) => setTimeout(resolve, 200));
      } catch (error) {
        console.error('Failed to download item:', error);
      }
    }
  };
  
  const handleClearGallery = async () => {
    if (confirm('Are you sure you want to clear the entire gallery?')) {
      await clearGallery();
    }
  };
  
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  const handleNavigate = (direction: 'prev' | 'next') => {
    if (!selectedItem) return;
    
    const currentIndex = filteredItems.findIndex(s => s.id === selectedItem.id);
    const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
    
    if (newIndex >= 0 && newIndex < filteredItems.length) {
      setSelectedItem(filteredItems[newIndex]);
    }
  };
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            style={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          
          <motion.div
            style={styles.panel}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          >
            {/* Header */}
            <div style={styles.header}>
              <div style={styles.title}>
                📁 Gallery
                <span style={styles.count}>{items.length}</span>
              </div>
              <motion.button
                style={styles.closeButton}
                onClick={onClose}
                whileHover={{ scale: 1.05, background: 'rgba(255,255,255,0.1)' }}
                whileTap={{ scale: 0.95 }}
              >
                ✕
              </motion.button>
            </div>
            
            {/* Filters */}
            <div style={styles.controls}>
              <button
                style={{
                  ...styles.filterButton,
                  ...(filter === 'all' ? styles.filterButtonActive : {}),
                }}
                onClick={() => setFilter('all')}
              >
                All ({items.length})
              </button>
              <button
                style={{
                  ...styles.filterButton,
                  ...(filter === 'recent' ? styles.filterButtonActive : {}),
                }}
                onClick={() => setFilter('recent')}
              >
                Recent
              </button>
              <button
                style={{
                  ...styles.filterButton,
                  ...(filter === 'project' ? styles.filterButtonActive : {}),
                }}
                onClick={() => setFilter('project')}
              >
                Projects ({projectCount})
              </button>
            </div>
            
            {/* Content */}
            <div style={styles.content}>
              {filteredItems.length === 0 ? (
                <div style={styles.emptyState}>
                  <div style={styles.emptyIcon}>📭</div>
                  <h3 style={styles.emptyTitle}>No Items Yet</h3>
                  <p style={styles.emptyText}>
                    {filter === 'all' 
                      ? 'Save slides from the chat to build your gallery.'
                      : 'No items match this filter.'}
                  </p>
                </div>
              ) : (
                <div style={styles.grid}>
                  {filteredItems.map((item) => (
                    <motion.div
                      key={item.id}
                      style={styles.slideCard}
                      whileHover={{ scale: 1.02 }}
                      onMouseEnter={() => setHoveredId(item.id)}
                      onMouseLeave={() => setHoveredId(null)}
                      onClick={() => setSelectedItem(item)}
                    >
                      {item.image_url ? (
                        <img
                          src={
                            item.image_url.startsWith('http')
                              ? item.image_url
                              : `${API_BASE_URL}${item.image_url}`
                          }
                          alt={item.title || 'Item'}
                          style={styles.slideImage}
                          loading="lazy"
                        />
                      ) : (
                        <div style={{ ...styles.slideImage, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '2rem' }}>
                          {item.item_type === 'script' ? '📝' : '📄'}
                        </div>
                      )}
                      
                      <div style={styles.slideMeta}>
                        <div style={styles.slideTitle}>
                          {item.title || `${item.item_type} ${item.id.slice(0, 6)}`}
                        </div>
                        <div style={styles.slideDate}>
                          {formatDate(item.created_at)}
                        </div>
                      </div>
                      
                      <motion.button
                        style={{
                          ...styles.deleteButton,
                          opacity: hoveredId === item.id ? 1 : 0,
                        }}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          removeItem(item.id);
                        }}
                      >
                        🗑
                      </motion.button>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Footer */}
            {items.length > 0 && (
              <div style={styles.footer}>
                <motion.button
                  style={{ ...styles.footerButton, ...styles.downloadAllButton }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleDownloadAll}
                >
                  ⬇️ Download All ({filteredItems.length})
                </motion.button>
                
                <motion.button
                  style={{ ...styles.footerButton, ...styles.clearButton }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleClearGallery}
                >
                  🗑 Clear
                </motion.button>
              </div>
            )}
          </motion.div>
          
          {/* Lightbox */}
          {selectedItem && (
            <SlideLightbox
              slide={itemToSlidePreview(selectedItem)}
              slides={filteredItems.map(itemToSlidePreview)}
              onClose={() => setSelectedItem(null)}
              onNavigate={handleNavigate}
            />
          )}
        </>
      )}
    </AnimatePresence>
  );
}
