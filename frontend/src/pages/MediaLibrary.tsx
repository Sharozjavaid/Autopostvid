import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Film, Image, Music, FolderOpen, Download, ExternalLink, 
  Play, X, RefreshCw, HardDrive, Clock
} from 'lucide-react';
import GlassCard from '../components/GlassCard';
import { 
  browseStorage, 
  getStorageStats, 
} from '../api/client';
import type { StorageItem, StorageStats } from '../api/client';

type FilterType = 'all' | 'video' | 'image' | 'audio';

export default function MediaLibrary() {
  const [filter, setFilter] = useState<FilterType>('all');
  const [selectedItem, setSelectedItem] = useState<StorageItem | null>(null);

  // Fetch storage stats
  const { data: stats } = useQuery<StorageStats>({
    queryKey: ['storage-stats'],
    queryFn: getStorageStats,
  });

  // Fetch storage items
  const { data: storageData, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['storage-browse', filter],
    queryFn: () => browseStorage({
      folder: '',
      file_type: filter === 'all' ? undefined : filter,
      limit: 200,
    }),
  });

  const items = storageData?.items || [];

  const getIcon = (contentType: string) => {
    if (contentType.startsWith('video/')) return <Film size={20} />;
    if (contentType.startsWith('image/')) return <Image size={20} />;
    if (contentType.startsWith('audio/')) return <Music size={20} />;
    return <FolderOpen size={20} />;
  };

  const getIconBg = (contentType: string) => {
    if (contentType.startsWith('video/')) return 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)';
    if (contentType.startsWith('image/')) return 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)';
    if (contentType.startsWith('audio/')) return 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)';
    return 'linear-gradient(135deg, #6b7280 0%, #374151 100%)';
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ 
          fontSize: '2rem', 
          fontWeight: 700, 
          color: '#0f172a',
          marginBottom: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <HardDrive size={24} style={{ color: 'white' }} />
          </div>
          Media Library
        </h1>
        <p style={{ color: '#64748b', fontSize: '1rem' }}>
          Browse all your generated content stored in the cloud
        </p>
      </div>

      {/* Stats Cards */}
      {stats && stats.available && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '16px',
          marginBottom: '24px',
        }}>
          <GlassCard padding="sm">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <FolderOpen size={20} style={{ color: 'white' }} />
              </div>
              <div>
                <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px' }}>Total Files</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>{stats.total_files}</p>
              </div>
            </div>
          </GlassCard>
          
          <GlassCard padding="sm">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <HardDrive size={20} style={{ color: 'white' }} />
              </div>
              <div>
                <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px' }}>Total Size</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>{stats.total_size_mb.toFixed(1)} MB</p>
              </div>
            </div>
          </GlassCard>

          {Object.entries(stats.folders).map(([folder, data]) => (
            <GlassCard key={folder} padding="sm">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: folder === 'videos' 
                    ? 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)'
                    : folder === 'slides'
                    ? 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)'
                    : 'linear-gradient(135deg, #6b7280 0%, #374151 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  {folder === 'videos' ? <Film size={20} style={{ color: 'white' }} /> : <Image size={20} style={{ color: 'white' }} />}
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px', textTransform: 'capitalize' }}>{folder}</p>
                  <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>{data.count} files</p>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        marginBottom: '24px',
        alignItems: 'center',
        flexWrap: 'wrap',
      }}>
        {(['all', 'video', 'image', 'audio'] as FilterType[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: 500,
              background: filter === f 
                ? 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)' 
                : 'rgba(148, 163, 184, 0.1)',
              color: filter === f ? 'white' : '#64748b',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {f === 'all' && <FolderOpen size={16} />}
            {f === 'video' && <Film size={16} />}
            {f === 'image' && <Image size={16} />}
            {f === 'audio' && <Music size={16} />}
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          style={{
            marginLeft: 'auto',
            padding: '8px 16px',
            borderRadius: '8px',
            border: '1px solid rgba(148, 163, 184, 0.2)',
            background: 'white',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.875rem',
            color: '#64748b',
          }}
        >
          <RefreshCw size={16} className={isFetching ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Content Grid */}
      {isLoading ? (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '300px',
        }}>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            <RefreshCw size={32} style={{ color: '#8b5cf6' }} />
          </motion.div>
        </div>
      ) : items.length === 0 ? (
        <GlassCard>
          <div style={{ 
            textAlign: 'center', 
            padding: '60px 20px',
          }}>
            <div style={{ 
              fontSize: '4rem', 
              marginBottom: '16px',
            }}>
              📭
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#334155', marginBottom: '8px' }}>
              No media found
            </h3>
            <p style={{ color: '#64748b', maxWidth: '400px', margin: '0 auto' }}>
              {filter === 'all' 
                ? 'Generate some content to see it here. Videos, images, and slides will automatically appear in your library.'
                : `No ${filter} files found. Try generating some or change the filter.`}
            </p>
          </div>
        </GlassCard>
      ) : (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', 
          gap: '16px',
        }}>
          {items.map((item) => (
            <motion.div
              key={item.url}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ scale: 1.02 }}
              style={{ cursor: 'pointer' }}
              onClick={() => setSelectedItem(item)}
            >
              <GlassCard padding="none">
                {/* Preview */}
                <div style={{ 
                  aspectRatio: '16/9', 
                  position: 'relative',
                  background: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
                  overflow: 'hidden',
                }}>
                  {item.content_type.startsWith('video/') ? (
                    <>
                      <video
                        src={item.url}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        muted
                        preload="metadata"
                      />
                      <div style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        background: 'rgba(0, 0, 0, 0.6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}>
                        <Play size={24} fill="white" style={{ color: 'white', marginLeft: '2px' }} />
                      </div>
                    </>
                  ) : item.content_type.startsWith('image/') ? (
                    <img
                      src={item.url}
                      alt={item.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      loading="lazy"
                    />
                  ) : (
                    <div style={{ 
                      width: '100%', 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      background: getIconBg(item.content_type),
                    }}>
                      {getIcon(item.content_type)}
                    </div>
                  )}
                  
                  {/* Folder Badge */}
                  <div style={{
                    position: 'absolute',
                    top: '8px',
                    left: '8px',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    background: 'rgba(0, 0, 0, 0.6)',
                    backdropFilter: 'blur(4px)',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    color: 'white',
                    textTransform: 'capitalize',
                  }}>
                    {item.folder}
                  </div>
                  
                  {/* Size Badge */}
                  <div style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    background: 'rgba(0, 0, 0, 0.6)',
                    backdropFilter: 'blur(4px)',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    color: 'white',
                  }}>
                    {item.size_human}
                  </div>
                </div>
                
                {/* Info */}
                <div style={{ padding: '12px 16px' }}>
                  <p style={{ 
                    fontSize: '0.875rem', 
                    fontWeight: 500, 
                    color: '#0f172a',
                    marginBottom: '4px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {item.name}
                  </p>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    fontSize: '0.75rem',
                    color: '#64748b',
                  }}>
                    <Clock size={12} />
                    {formatDate(item.created_at)}
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}

      {/* Media Preview Modal */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.9)',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px',
            }}
            onClick={() => setSelectedItem(null)}
          >
            {/* Close button */}
            <button
              onClick={() => setSelectedItem(null)}
              style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                width: '44px',
                height: '44px',
                borderRadius: '50%',
                border: 'none',
                background: 'rgba(255, 255, 255, 0.1)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
              }}
            >
              <X size={24} />
            </button>

            {/* Media */}
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                maxWidth: '90vw',
                maxHeight: '80vh',
                borderRadius: '12px',
                overflow: 'hidden',
              }}
            >
              {selectedItem.content_type.startsWith('video/') ? (
                <video
                  src={selectedItem.url}
                  controls
                  autoPlay
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '80vh',
                    borderRadius: '12px',
                  }}
                />
              ) : selectedItem.content_type.startsWith('image/') ? (
                <img
                  src={selectedItem.url}
                  alt={selectedItem.name}
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '80vh',
                    borderRadius: '12px',
                  }}
                />
              ) : (
                <div style={{ 
                  padding: '40px', 
                  background: 'white', 
                  borderRadius: '12px',
                  textAlign: 'center',
                }}>
                  <p>Preview not available</p>
                </div>
              )}
            </motion.div>

            {/* Info Bar */}
            <div style={{
              marginTop: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              padding: '12px 20px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '10px',
              backdropFilter: 'blur(10px)',
            }}>
              <span style={{ color: 'white', fontSize: '0.875rem', fontWeight: 500 }}>
                {selectedItem.name}
              </span>
              <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.875rem' }}>
                {selectedItem.size_human}
              </span>
              <a
                href={selectedItem.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: '#8b5cf6',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                }}
              >
                <ExternalLink size={16} />
                Open
              </a>
              <a
                href={selectedItem.url}
                download={selectedItem.name}
                onClick={(e) => e.stopPropagation()}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: '#10b981',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                }}
              >
                <Download size={16} />
                Download
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
