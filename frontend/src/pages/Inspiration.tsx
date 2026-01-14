import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lightbulb,
  Plus,
  Search,
  Filter,
  Trash2,
  ExternalLink,
  Image,
  Eye,
  Heart,
  X,
  Upload,
  Link as LinkIcon,
  ChevronLeft,
  ChevronRight,
  Play,
  Tag,
} from 'lucide-react';
import GlassCard from '../components/GlassCard';
import Button from '../components/Button';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API functions
const fetchReferences = async (formatType?: string, tags?: string) => {
  const params = new URLSearchParams();
  if (formatType) params.append('format_type', formatType);
  if (tags) params.append('tags', tags);
  const res = await fetch(`${API_BASE}/api/inspiration?${params}`);
  if (!res.ok) throw new Error('Failed to fetch references');
  return res.json();
};

const scrapeReference = async (data: { url: string; format_type: string; tags: string[]; notes: string }) => {
  const res = await fetch(`${API_BASE}/api/inspiration/scrape`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to scrape TikTok');
  return res.json();
};

const createManualReference = async (data: { title: string; format_type: string; tags: string[]; notes: string; url?: string }) => {
  const res = await fetch(`${API_BASE}/api/inspiration/manual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create reference');
  return res.json();
};

const uploadFrame = async (refId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/inspiration/${refId}/frames`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload frame');
  return res.json();
};

const deleteReference = async (refId: string) => {
  const res = await fetch(`${API_BASE}/api/inspiration/${refId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete reference');
  return res.json();
};

const fetchReferenceDetail = async (refId: string) => {
  const res = await fetch(`${API_BASE}/api/inspiration/${refId}`);
  if (!res.ok) throw new Error('Failed to fetch reference');
  return res.json();
};

interface Reference {
  id: string;
  url: string;
  format_type: string;
  tags: string[];
  notes: string;
  title: string;
  uploader: string;
  view_count: number;
  like_count: number;
  frame_count: number;
  added_date: string;
  is_manual: boolean;
}

const formatTypes = [
  { id: '', name: 'All Formats' },
  { id: 'slideshow', name: 'Slideshow' },
  { id: 'narrated_video', name: 'Narrated Video' },
  { id: 'mentor_slideshow', name: 'Mentor Slideshow' },
  { id: 'quote_video', name: 'Quote Video' },
  { id: 'story_video', name: 'Story Video' },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.05 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function Inspiration() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [formatFilter, setFormatFilter] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [addMode, setAddMode] = useState<'url' | 'manual'>('url');
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);

  // Form states
  const [newUrl, setNewUrl] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [newFormat, setNewFormat] = useState('slideshow');
  const [newTags, setNewTags] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['inspiration', formatFilter],
    queryFn: () => fetchReferences(formatFilter || undefined),
  });

  const { data: selectedRefData } = useQuery({
    queryKey: ['inspiration-detail', selectedRef],
    queryFn: () => fetchReferenceDetail(selectedRef!),
    enabled: !!selectedRef,
  });

  const scrapeMutation = useMutation({
    mutationFn: scrapeReference,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inspiration'] });
      setShowAddModal(false);
      resetForm();
    },
  });

  const manualMutation = useMutation({
    mutationFn: createManualReference,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inspiration'] });
      setShowAddModal(false);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteReference,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inspiration'] });
      setSelectedRef(null);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ refId, file }: { refId: string; file: File }) => uploadFrame(refId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inspiration-detail', selectedRef] });
    },
  });

  const resetForm = () => {
    setNewUrl('');
    setNewTitle('');
    setNewFormat('slideshow');
    setNewTags('');
    setNewNotes('');
    setIsSubmitting(false);
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    const tags = newTags.split(',').map(t => t.trim()).filter(Boolean);

    if (addMode === 'url') {
      await scrapeMutation.mutateAsync({ url: newUrl, format_type: newFormat, tags, notes: newNotes });
    } else {
      await manualMutation.mutateAsync({ title: newTitle, format_type: newFormat, tags, notes: newNotes, url: newUrl });
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || !selectedRef) return;

    Array.from(files).forEach(file => {
      uploadMutation.mutate({ refId: selectedRef, file });
    });
  };

  const references = data?.references || [];
  const filteredRefs = references.filter((r: Reference) =>
    r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.tags.some((t: string) => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <motion.div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '18px',
              background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(245, 158, 11, 0.35)',
            }}
            whileHover={{ scale: 1.05, rotate: 5 }}
          >
            <Lightbulb size={26} style={{ color: 'white' }} />
          </motion.div>
          <div>
            <h1 style={{
              fontSize: '28px',
              fontWeight: 800,
              background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              Inspiration
            </h1>
            <p style={{ color: '#64748b', marginTop: '4px' }}>
              {data?.total || 0} reference examples for AI learning
            </p>
          </div>
        </div>
        <Button variant="primary" icon={<Plus size={18} />} onClick={() => setShowAddModal(true)}>
          Add Reference
        </Button>
      </div>

      {/* Filters */}
      <GlassCard padding="md">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
            <input
              type="text"
              className="input"
              style={{ paddingLeft: '44px' }}
              placeholder="Search by title or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Filter size={18} style={{ color: '#64748b' }} />
            <select
              className="select"
              style={{ width: '180px' }}
              value={formatFilter}
              onChange={(e) => setFormatFilter(e.target.value)}
            >
              {formatTypes.map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          </div>
        </div>
      </GlassCard>

      {/* References Grid */}
      {isLoading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <GlassCard key={i} padding="lg">
              <div style={{ animation: 'pulse 2s infinite' }}>
                <div style={{ height: '200px', background: 'rgba(148, 163, 184, 0.2)', borderRadius: '12px', marginBottom: '12px' }} />
                <div style={{ height: '20px', background: 'rgba(148, 163, 184, 0.15)', borderRadius: '6px', width: '75%' }} />
              </div>
            </GlassCard>
          ))}
        </div>
      ) : filteredRefs.length > 0 ? (
        <motion.div
          style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {filteredRefs.map((ref: Reference) => (
            <motion.div key={ref.id} variants={itemVariants}>
              <GlassCard hover padding="none" onClick={() => { setSelectedRef(ref.id); setCurrentFrameIndex(0); }}>
                {/* Thumbnail */}
                <div style={{
                  aspectRatio: '16/9',
                  background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                  borderRadius: '16px 16px 0 0',
                  overflow: 'hidden',
                  position: 'relative',
                }}>
                  {ref.frame_count > 0 ? (
                    <img
                      src={`${API_BASE}/api/inspiration/${ref.id}/frame/0`}
                      alt={ref.title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                      <Image size={48} style={{ color: '#475569' }} />
                    </div>
                  )}
                  {/* Frame count badge */}
                  <div style={{
                    position: 'absolute',
                    bottom: '8px',
                    right: '8px',
                    background: 'rgba(0,0,0,0.7)',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}>
                    <Image size={12} />
                    {ref.frame_count} frames
                  </div>
                  {/* Format badge */}
                  <div style={{
                    position: 'absolute',
                    top: '8px',
                    left: '8px',
                    background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontWeight: 600,
                    color: 'white',
                  }}>
                    {ref.format_type.replace('_', ' ')}
                  </div>
                </div>

                {/* Content */}
                <div style={{ padding: '16px' }}>
                  <h3 style={{ fontWeight: 600, color: '#0f172a', fontSize: '15px', marginBottom: '8px' }} className="line-clamp-2">
                    {ref.title || 'Untitled Reference'}
                  </h3>

                  {/* Stats */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px', color: '#64748b', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Eye size={14} />
                      {formatNumber(ref.view_count)}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Heart size={14} />
                      {formatNumber(ref.like_count)}
                    </div>
                    {ref.uploader && (
                      <span>@{ref.uploader}</span>
                    )}
                  </div>

                  {/* Tags */}
                  {ref.tags.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {ref.tags.slice(0, 3).map((tag, i) => (
                        <span key={i} style={{
                          padding: '4px 8px',
                          borderRadius: '6px',
                          background: 'rgba(245, 158, 11, 0.1)',
                          color: '#d97706',
                          fontSize: '11px',
                          fontWeight: 500,
                        }}>
                          {tag}
                        </span>
                      ))}
                      {ref.tags.length > 3 && (
                        <span style={{ fontSize: '11px', color: '#94a3b8' }}>+{ref.tags.length - 3}</span>
                      )}
                    </div>
                  )}
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <GlassCard padding="xl">
          <div style={{ textAlign: 'center', padding: '48px' }}>
            <motion.div
              style={{
                width: '80px',
                height: '80px',
                borderRadius: '24px',
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(239, 68, 68, 0.1) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 20px',
              }}
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Lightbulb size={36} style={{ color: '#f59e0b' }} />
            </motion.div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>No references yet</h3>
            <p style={{ color: '#64748b', marginBottom: '24px' }}>
              Add TikTok examples to train the AI on successful formats
            </p>
            <Button variant="primary" icon={<Plus size={18} />} onClick={() => setShowAddModal(true)}>
              Add First Reference
            </Button>
          </div>
        </GlassCard>
      )}

      {/* Add Modal */}
      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
            }}
            onClick={() => setShowAddModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'white',
                borderRadius: '24px',
                padding: '32px',
                width: '500px',
                maxHeight: '80vh',
                overflow: 'auto',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <h2 style={{ fontSize: '20px', fontWeight: 700 }}>Add Reference</h2>
                <button onClick={() => setShowAddModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                  <X size={24} style={{ color: '#64748b' }} />
                </button>
              </div>

              {/* Mode toggle */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
                <button
                  onClick={() => setAddMode('url')}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '12px',
                    border: addMode === 'url' ? '2px solid #f59e0b' : '2px solid #e2e8f0',
                    background: addMode === 'url' ? 'rgba(245, 158, 11, 0.1)' : 'white',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  <LinkIcon size={18} style={{ color: addMode === 'url' ? '#f59e0b' : '#64748b' }} />
                  <span style={{ fontWeight: 600, color: addMode === 'url' ? '#f59e0b' : '#64748b' }}>From URL</span>
                </button>
                <button
                  onClick={() => setAddMode('manual')}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '12px',
                    border: addMode === 'manual' ? '2px solid #f59e0b' : '2px solid #e2e8f0',
                    background: addMode === 'manual' ? 'rgba(245, 158, 11, 0.1)' : 'white',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  <Upload size={18} style={{ color: addMode === 'manual' ? '#f59e0b' : '#64748b' }} />
                  <span style={{ fontWeight: 600, color: addMode === 'manual' ? '#f59e0b' : '#64748b' }}>Manual Upload</span>
                </button>
              </div>

              {/* Form */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {addMode === 'url' ? (
                  <div>
                    <label style={{ fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px', display: 'block' }}>
                      TikTok URL
                    </label>
                    <input
                      type="url"
                      className="input"
                      placeholder="https://www.tiktok.com/@user/video/..."
                      value={newUrl}
                      onChange={(e) => setNewUrl(e.target.value)}
                    />
                    <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                      Note: Slideshow/photo URLs may not work. Video URLs work best.
                    </p>
                  </div>
                ) : (
                  <div>
                    <label style={{ fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px', display: 'block' }}>
                      Title
                    </label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., Viral Stoicism Slideshow"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                    />
                  </div>
                )}

                <div>
                  <label style={{ fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px', display: 'block' }}>
                    Format Type
                  </label>
                  <select
                    className="select"
                    value={newFormat}
                    onChange={(e) => setNewFormat(e.target.value)}
                  >
                    <option value="slideshow">Slideshow</option>
                    <option value="narrated_video">Narrated Video</option>
                    <option value="mentor_slideshow">Mentor Slideshow</option>
                    <option value="quote_video">Quote Video</option>
                    <option value="story_video">Story Video</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px', display: 'block' }}>
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g., stoicism, philosophy, viral"
                    value={newTags}
                    onChange={(e) => setNewTags(e.target.value)}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px', display: 'block' }}>
                    Notes (why this is a good example)
                  </label>
                  <textarea
                    className="input"
                    style={{ minHeight: '80px', resize: 'vertical' }}
                    placeholder="e.g., Great hook, cinematic visuals, emotional storytelling..."
                    value={newNotes}
                    onChange={(e) => setNewNotes(e.target.value)}
                  />
                </div>

                <Button
                  variant="primary"
                  onClick={handleSubmit}
                  disabled={isSubmitting || (addMode === 'url' ? !newUrl : !newTitle)}
                  style={{ marginTop: '8px' }}
                >
                  {isSubmitting ? 'Adding...' : addMode === 'url' ? 'Scrape & Add' : 'Create Reference'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Detail Modal / Lightbox */}
      <AnimatePresence>
        {selectedRef && selectedRefData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.9)',
              display: 'flex',
              zIndex: 100,
            }}
            onClick={() => setSelectedRef(null)}
          >
            {/* Left side - Frame viewer */}
            <div
              style={{ flex: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}
              onClick={(e) => e.stopPropagation()}
            >
              {selectedRefData.frames && selectedRefData.frames.length > 0 ? (
                <>
                  <img
                    src={`${API_BASE}/api/inspiration/${selectedRef}/frame/${currentFrameIndex}`}
                    alt=""
                    style={{ maxHeight: '90vh', maxWidth: '100%', borderRadius: '12px' }}
                  />
                  {/* Navigation */}
                  {selectedRefData.frames.length > 1 && (
                    <>
                      <button
                        onClick={() => setCurrentFrameIndex(Math.max(0, currentFrameIndex - 1))}
                        style={{
                          position: 'absolute',
                          left: '20px',
                          background: 'rgba(255,255,255,0.1)',
                          border: 'none',
                          borderRadius: '50%',
                          width: '48px',
                          height: '48px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          cursor: 'pointer',
                          opacity: currentFrameIndex === 0 ? 0.3 : 1,
                        }}
                        disabled={currentFrameIndex === 0}
                      >
                        <ChevronLeft size={24} style={{ color: 'white' }} />
                      </button>
                      <button
                        onClick={() => setCurrentFrameIndex(Math.min(selectedRefData.frames.length - 1, currentFrameIndex + 1))}
                        style={{
                          position: 'absolute',
                          right: '20px',
                          background: 'rgba(255,255,255,0.1)',
                          border: 'none',
                          borderRadius: '50%',
                          width: '48px',
                          height: '48px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          cursor: 'pointer',
                          opacity: currentFrameIndex === selectedRefData.frames.length - 1 ? 0.3 : 1,
                        }}
                        disabled={currentFrameIndex === selectedRefData.frames.length - 1}
                      >
                        <ChevronRight size={24} style={{ color: 'white' }} />
                      </button>
                      {/* Frame counter */}
                      <div style={{
                        position: 'absolute',
                        bottom: '20px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(0,0,0,0.7)',
                        padding: '8px 16px',
                        borderRadius: '20px',
                        color: 'white',
                        fontSize: '14px',
                      }}>
                        {currentFrameIndex + 1} / {selectedRefData.frames.length}
                      </div>
                    </>
                  )}
                </>
              ) : (
                <div style={{ color: '#64748b', textAlign: 'center' }}>
                  <Image size={64} style={{ marginBottom: '16px', opacity: 0.5 }} />
                  <p>No frames yet</p>
                  <Button
                    variant="secondary"
                    icon={<Upload size={16} />}
                    onClick={() => fileInputRef.current?.click()}
                    style={{ marginTop: '16px' }}
                  >
                    Upload Screenshots
                  </Button>
                </div>
              )}
            </div>

            {/* Right side - Info panel */}
            <div
              style={{
                width: '400px',
                background: 'white',
                padding: '32px',
                overflowY: 'auto',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <h2 style={{ fontSize: '18px', fontWeight: 700 }}>Reference Details</h2>
                <button onClick={() => setSelectedRef(null)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                  <X size={24} style={{ color: '#64748b' }} />
                </button>
              </div>

              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
                {selectedRefData.title || 'Untitled'}
              </h3>

              {selectedRefData.url && (
                <a
                  href={selectedRefData.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    color: '#f59e0b',
                    fontSize: '13px',
                    marginBottom: '16px',
                  }}
                >
                  <ExternalLink size={14} />
                  View Original
                </a>
              )}

              {/* Stats */}
              <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
                <div style={{ textAlign: 'center', flex: 1, padding: '12px', background: '#f8fafc', borderRadius: '12px' }}>
                  <Eye size={20} style={{ color: '#64748b', margin: '0 auto 4px' }} />
                  <div style={{ fontWeight: 700, fontSize: '18px' }}>{formatNumber(selectedRefData.view_count)}</div>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>Views</div>
                </div>
                <div style={{ textAlign: 'center', flex: 1, padding: '12px', background: '#f8fafc', borderRadius: '12px' }}>
                  <Heart size={20} style={{ color: '#64748b', margin: '0 auto 4px' }} />
                  <div style={{ fontWeight: 700, fontSize: '18px' }}>{formatNumber(selectedRefData.like_count)}</div>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>Likes</div>
                </div>
                <div style={{ textAlign: 'center', flex: 1, padding: '12px', background: '#f8fafc', borderRadius: '12px' }}>
                  <Image size={20} style={{ color: '#64748b', margin: '0 auto 4px' }} />
                  <div style={{ fontWeight: 700, fontSize: '18px' }}>{selectedRefData.frame_count}</div>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>Frames</div>
                </div>
              </div>

              {/* Format */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '4px', display: 'block' }}>Format</label>
                <span style={{
                  display: 'inline-block',
                  padding: '6px 12px',
                  background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(239, 68, 68, 0.1) 100%)',
                  color: '#d97706',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '13px',
                }}>
                  {selectedRefData.format_type.replace('_', ' ')}
                </span>
              </div>

              {/* Tags */}
              {selectedRefData.tags && selectedRefData.tags.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px', display: 'block' }}>Tags</label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {selectedRefData.tags.map((tag: string, i: number) => (
                      <span key={i} style={{
                        padding: '4px 10px',
                        background: '#f1f5f9',
                        borderRadius: '6px',
                        fontSize: '12px',
                        color: '#475569',
                      }}>
                        <Tag size={10} style={{ marginRight: '4px' }} />
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              {selectedRefData.notes && (
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px', display: 'block' }}>Notes</label>
                  <p style={{ fontSize: '14px', color: '#374151', lineHeight: 1.6 }}>{selectedRefData.notes}</p>
                </div>
              )}

              {/* Frame thumbnails */}
              {selectedRefData.frames && selectedRefData.frames.length > 0 && (
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px', display: 'block' }}>
                    All Frames
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                    {selectedRefData.frames.map((_: string, i: number) => (
                      <div
                        key={i}
                        onClick={() => setCurrentFrameIndex(i)}
                        style={{
                          aspectRatio: '9/16',
                          borderRadius: '8px',
                          overflow: 'hidden',
                          cursor: 'pointer',
                          border: currentFrameIndex === i ? '2px solid #f59e0b' : '2px solid transparent',
                        }}
                      >
                        <img
                          src={`${API_BASE}/api/inspiration/${selectedRef}/frame/${i}`}
                          alt=""
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Upload more frames */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                style={{ display: 'none' }}
                onChange={handleFileUpload}
              />
              <Button
                variant="secondary"
                icon={<Upload size={16} />}
                onClick={() => fileInputRef.current?.click()}
                style={{ width: '100%', marginBottom: '12px' }}
              >
                Upload More Screenshots
              </Button>

              {/* Delete */}
              <Button
                variant="danger"
                icon={<Trash2 size={16} />}
                onClick={() => {
                  if (confirm('Delete this reference?')) {
                    deleteMutation.mutate(selectedRef);
                  }
                }}
                style={{ width: '100%' }}
              >
                Delete Reference
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
