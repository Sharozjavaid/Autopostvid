import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle2,
  Image as ImageIcon,
  FileText,
  Settings,
  Send,
  Download,
  ArrowLeft,
  Edit3,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  Palette,
  Type,
  RefreshCw,
  AlertCircle,
  Play,
  X
} from 'lucide-react';
import {
  getProject,
  getSlideImageUrl,
  API_BASE_URL,
  api
} from '../api/client';
// Note: Project type is used for type inference
import GlassCard from '../components/GlassCard';
import Button from '../components/Button';

// TikTok post function
const postToTikTok = async (projectId: string, caption?: string): Promise<{
  success: boolean;
  publish_id?: string;
  error?: string;
  image_count?: number;
}> => {
  const response = await api.post(`/api/projects/${projectId}/post-to-tiktok`, {
    caption
  });
  return response.data;
};

// Check TikTok status
const getTikTokStatus = async () => {
  const response = await api.get('/api/tiktok/status');
  return response.data;
};

// Instagram post function
const postToInstagram = async (projectId: string, caption?: string, hashtags?: string[]): Promise<{
  success: boolean;
  post_id?: string;
  error?: string;
  image_count?: number;
  instagram_url?: string;
  status?: string;
}> => {
  const response = await api.post(`/api/projects/${projectId}/post-to-instagram`, {
    caption,
    hashtags
  });
  return response.data;
};

// Check Instagram status
const getInstagramStatus = async () => {
  try {
    const response = await api.get('/api/instagram/status');
    return response.data;
  } catch {
    // If endpoint doesn't exist, assume connected (Post Bridge doesn't need auth check)
    return { connected: true };
  }
};

export default function CompletedProjectView() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  // Query client available for future invalidation needs
  useQueryClient();
  
  const [expandedSection, setExpandedSection] = useState<string | null>('images');
  const [selectedSlideIndex, setSelectedSlideIndex] = useState<number | null>(null);
  const [showTikTokModal, setShowTikTokModal] = useState(false);
  const [tiktokCaption, setTiktokCaption] = useState('');
  const [postResult, setPostResult] = useState<{ success: boolean; message: string } | null>(null);
  
  // Instagram state
  const [showInstagramModal, setShowInstagramModal] = useState(false);
  const [instagramCaption, setInstagramCaption] = useState('');
  const [instagramHashtags, setInstagramHashtags] = useState('');
  const [instagramPostResult, setInstagramPostResult] = useState<{ success: boolean; message: string; url?: string } | null>(null);

  // Fetch project data
  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  });

  // Fetch TikTok status
  const { data: tiktokStatus } = useQuery({
    queryKey: ['tiktok-status'],
    queryFn: getTikTokStatus,
    staleTime: 30000,
  });

  // Post to TikTok mutation
  const postToTikTokMutation = useMutation({
    mutationFn: () => postToTikTok(projectId!, tiktokCaption || project?.topic || 'Philosophy Slideshow'),
    onSuccess: (data) => {
      if (data.success) {
        setPostResult({ success: true, message: `Slideshow sent to TikTok drafts! ${data.image_count} images uploaded.` });
      } else {
        setPostResult({ success: false, message: data.error || 'Failed to post to TikTok' });
      }
    },
    onError: (error: Error) => {
      setPostResult({ success: false, message: error.message });
    },
  });
  
  // Fetch Instagram status (just to show connected)
  const { data: instagramStatus } = useQuery({
    queryKey: ['instagram-status'],
    queryFn: getInstagramStatus,
    staleTime: 60000,
  });
  
  // Post to Instagram mutation
  const postToInstagramMutation = useMutation({
    mutationFn: () => {
      const caption = instagramCaption || project?.topic || 'Philosophy Slideshow';
      // Parse hashtags from comma-separated string, always include philosophizemeapp
      let hashtags = instagramHashtags
        .split(',')
        .map(h => h.trim().replace(/^#/, ''))
        .filter(h => h.length > 0);
      // Always include philosophizemeapp first
      if (!hashtags.includes('philosophizemeapp')) {
        hashtags = ['philosophizemeapp', ...hashtags];
      }
      if (hashtags.length === 1) {
        // Add some default hashtags if only our required one
        hashtags = ['philosophizemeapp', 'philosophy', 'wisdom', 'stoicism', 'motivation'];
      }
      return postToInstagram(projectId!, caption, hashtags);
    },
    onSuccess: (data) => {
      if (data.success) {
        setInstagramPostResult({ 
          success: true, 
          message: `Carousel with ${data.image_count} images posted to Instagram!`,
          url: data.instagram_url
        });
      } else {
        setInstagramPostResult({ success: false, message: data.error || 'Failed to post to Instagram' });
      }
    },
    onError: (error: Error) => {
      setInstagramPostResult({ success: false, message: error.message });
    },
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <RefreshCw size={32} className="animate-spin" style={{ color: '#667eea' }} />
      </div>
    );
  }

  if (error || !project) {
    return (
      <GlassCard padding="xl">
        <div style={{ textAlign: 'center', padding: '48px' }}>
          <AlertCircle size={48} style={{ color: '#ef4444', marginBottom: '16px' }} />
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>
            Project Not Found
          </h2>
          <p style={{ color: '#64748b', marginBottom: '24px' }}>
            This project doesn't exist or couldn't be loaded.
          </p>
          <Link to="/projects">
            <Button variant="primary">Back to Projects</Button>
          </Link>
        </div>
      </GlassCard>
    );
  }

  const slides = project.slides || [];
  const completedSlides = slides.filter(s => s.image_status === 'complete');
  const allImagesComplete = slides.length > 0 && slides.every(s => s.image_status === 'complete');

  // Get project settings info
  const firstSlide = slides[0];
  const usedFont = firstSlide?.current_font || 'social';
  const usedTheme = firstSlide?.current_theme || 'golden_dust';

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const handlePostToTikTok = () => {
    if (!tiktokStatus?.authenticated) {
      // Redirect to TikTok auth
      window.open(`${API_BASE_URL}/api/tiktok/auth`, '_blank');
      return;
    }
    setTiktokCaption(project.topic || project.name);
    setShowTikTokModal(true);
  };

  const confirmTikTokPost = () => {
    setPostResult(null);
    postToTikTokMutation.mutate();
  };
  
  const handlePostToInstagram = () => {
    setInstagramCaption(project?.topic || project?.name || '');
    setInstagramHashtags('philosophizemeapp, philosophy, wisdom, stoicism, motivation');
    setShowInstagramModal(true);
  };
  
  const confirmInstagramPost = () => {
    setInstagramPostResult(null);
    postToInstagramMutation.mutate();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Link to="/projects">
            <motion.button
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                background: 'rgba(255, 255, 255, 0.8)',
                border: '1px solid rgba(148, 163, 184, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
              whileHover={{ scale: 1.05, background: 'rgba(102, 126, 234, 0.1)' }}
              whileTap={{ scale: 0.95 }}
            >
              <ArrowLeft size={20} style={{ color: '#64748b' }} />
            </motion.button>
          </Link>
          <div>
            <h1 style={{
              fontSize: '28px',
              fontWeight: 800,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {project.name || project.topic}
            </h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 12px',
                fontSize: '12px',
                fontWeight: 600,
                borderRadius: '16px',
                background: allImagesComplete ? 'rgba(34, 197, 94, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                color: allImagesComplete ? '#16a34a' : '#d97706',
              }}>
                {allImagesComplete ? <CheckCircle2 size={14} /> : <Clock size={14} />}
                {allImagesComplete ? 'Complete' : `${completedSlides.length}/${slides.length} slides`}
              </span>
              <span style={{ fontSize: '13px', color: '#64748b' }}>
                {slides.length} slides
              </span>
              <span style={{ fontSize: '13px', color: '#94a3b8' }}>•</span>
              <span style={{ fontSize: '13px', color: '#64748b' }}>
                {new Date(project.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            variant="secondary"
            icon={<Edit3 size={18} />}
            onClick={() => navigate(`/static-slideshow/${projectId}`)}
          >
            Edit Project
          </Button>
          <Button
            variant="secondary"
            icon={<Send size={18} />}
            onClick={handlePostToTikTok}
            disabled={!allImagesComplete}
          >
            Post to TikTok
          </Button>
          <Button
            variant="primary"
            icon={<Send size={18} />}
            onClick={handlePostToInstagram}
            disabled={!allImagesComplete}
            style={{ background: 'linear-gradient(135deg, #833AB4 0%, #FD1D1D 50%, #FCB045 100%)' }}
          >
            Post to Instagram
          </Button>
        </div>
      </div>

      {/* Main Content - All sections in one view */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '24px' }}>
        {/* Left Column - Main content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Images Section */}
          <GlassCard padding="none">
            <div
              style={{
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                borderBottom: expandedSection === 'images' ? '1px solid rgba(148, 163, 184, 0.15)' : 'none',
              }}
              onClick={() => toggleSection('images')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <ImageIcon size={20} style={{ color: 'white' }} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#0f172a' }}>
                    Generated Images
                  </h3>
                  <p style={{ fontSize: '13px', color: '#64748b' }}>
                    {completedSlides.length} of {slides.length} slides complete
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  borderRadius: '16px',
                  background: allImagesComplete ? 'rgba(34, 197, 94, 0.1)' : 'rgba(102, 126, 234, 0.1)',
                  color: allImagesComplete ? '#16a34a' : '#667eea',
                }}>
                  {allImagesComplete ? 'All Complete' : 'In Progress'}
                </span>
                {expandedSection === 'images' ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </div>
            </div>
            
            <AnimatePresence>
              {expandedSection === 'images' && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  style={{ overflow: 'hidden' }}
                >
                  <div style={{ padding: '20px 24px' }}>
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', 
                      gap: '12px' 
                    }}>
                      {slides.map((slide, index) => (
                        <motion.div
                          key={slide.id}
                          style={{
                            aspectRatio: '9/16',
                            borderRadius: '12px',
                            overflow: 'hidden',
                            background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                            position: 'relative',
                            cursor: 'pointer',
                            border: selectedSlideIndex === index ? '3px solid #667eea' : '1px solid rgba(148, 163, 184, 0.2)',
                          }}
                          whileHover={{ scale: 1.02 }}
                          onClick={() => setSelectedSlideIndex(selectedSlideIndex === index ? null : index)}
                        >
                          {slide.final_image_path ? (
                            <img
                              src={getSlideImageUrl(slide.final_image_path) || ''}
                              alt={slide.title || `Slide ${index + 1}`}
                              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            />
                          ) : (
                            <div style={{
                              position: 'absolute',
                              inset: 0,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}>
                              {slide.image_status === 'generating' ? (
                                <RefreshCw size={24} className="animate-spin" style={{ color: '#667eea' }} />
                              ) : (
                                <ImageIcon size={24} style={{ color: '#94a3b8' }} />
                              )}
                            </div>
                          )}
                          
                          {/* Slide number badge */}
                          <div style={{
                            position: 'absolute',
                            top: '8px',
                            left: '8px',
                            padding: '4px 10px',
                            fontSize: '11px',
                            fontWeight: 700,
                            borderRadius: '12px',
                            background: index === 0
                              ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                              : index === slides.length - 1
                                ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                                : 'rgba(0, 0, 0, 0.6)',
                            color: 'white',
                            backdropFilter: 'blur(4px)',
                          }}>
                            {index === 0 ? 'Hook' : index === slides.length - 1 ? 'Outro' : `#${index}`}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>

          {/* Script Section */}
          <GlassCard padding="none">
            <div
              style={{
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                borderBottom: expandedSection === 'script' ? '1px solid rgba(148, 163, 184, 0.15)' : 'none',
              }}
              onClick={() => toggleSection('script')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <FileText size={20} style={{ color: 'white' }} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#0f172a' }}>
                    Script Content
                  </h3>
                  <p style={{ fontSize: '13px', color: '#64748b' }}>
                    {slides.length} slides • {project.script_style || 'auto'} style
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  borderRadius: '16px',
                  background: project.script_approved === 'Y' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                  color: project.script_approved === 'Y' ? '#16a34a' : '#d97706',
                }}>
                  {project.script_approved === 'Y' ? 'Approved' : 'Draft'}
                </span>
                {expandedSection === 'script' ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </div>
            </div>
            
            <AnimatePresence>
              {expandedSection === 'script' && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  style={{ overflow: 'hidden' }}
                >
                  <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {slides.map((slide, index) => (
                      <div
                        key={slide.id}
                        style={{
                          padding: '16px',
                          background: 'rgba(248, 250, 252, 0.5)',
                          borderRadius: '12px',
                          border: '1px solid rgba(148, 163, 184, 0.15)',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '28px',
                            height: '28px',
                            borderRadius: '8px',
                            background: index === 0
                              ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                              : index === slides.length - 1
                                ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: 700,
                          }}>
                            {index === 0 ? 'H' : index === slides.length - 1 ? 'O' : index}
                          </span>
                          <span style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>
                            {slide.title || 'Untitled'}
                          </span>
                        </div>
                        {slide.subtitle && (
                          <p style={{ fontSize: '14px', color: '#334155', marginBottom: '8px' }}>
                            {slide.subtitle}
                          </p>
                        )}
                        {slide.visual_description && (
                          <p style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic' }}>
                            Visual: {slide.visual_description.substring(0, 100)}...
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>
        </div>

        {/* Right Column - Settings & Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Selected Slide Preview */}
          {selectedSlideIndex !== null && slides[selectedSlideIndex] && (
            <GlassCard padding="lg">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a' }}>
                  Slide Preview
                </h3>
                <button
                  onClick={() => setSelectedSlideIndex(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#94a3b8',
                  }}
                >
                  <X size={18} />
                </button>
              </div>
              <div style={{
                aspectRatio: '9/16',
                borderRadius: '12px',
                overflow: 'hidden',
                marginBottom: '16px',
              }}>
                {slides[selectedSlideIndex].final_image_path && (
                  <img
                    src={getSlideImageUrl(slides[selectedSlideIndex].final_image_path) || ''}
                    alt={slides[selectedSlideIndex].title || 'Slide preview'}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                )}
              </div>
              <div>
                <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>
                  {slides[selectedSlideIndex].title}
                </p>
                <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                  {slides[selectedSlideIndex].subtitle}
                </p>
              </div>
            </GlassCard>
          )}

          {/* Project Settings */}
          <GlassCard gradient="purple" padding="lg">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
              <Settings size={20} style={{ color: '#667eea' }} />
              <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a' }}>
                Generation Settings
              </h3>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: 'rgba(102, 126, 234, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <Type size={16} style={{ color: '#667eea' }} />
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: '#64748b' }}>Font</p>
                  <p style={{ fontSize: '14px', fontWeight: 500, color: '#0f172a' }}>
                    {usedFont.charAt(0).toUpperCase() + usedFont.slice(1)}
                  </p>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: 'rgba(102, 126, 234, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <Palette size={16} style={{ color: '#667eea' }} />
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: '#64748b' }}>Theme</p>
                  <p style={{ fontSize: '14px', fontWeight: 500, color: '#0f172a' }}>
                    {usedTheme.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </p>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: 'rgba(102, 126, 234, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <FileText size={16} style={{ color: '#667eea' }} />
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: '#64748b' }}>Script Style</p>
                  <p style={{ fontSize: '14px', fontWeight: 500, color: '#0f172a' }}>
                    {project.script_style || 'Auto-detected'}
                  </p>
                </div>
              </div>
            </div>
          </GlassCard>

          {/* Quick Actions */}
          <GlassCard padding="lg">
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a', marginBottom: '16px' }}>
              Quick Actions
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Button
                variant="secondary"
                fullWidth
                icon={<Download size={18} />}
              >
                Download All Images
              </Button>
              <Button
                variant="secondary"
                fullWidth
                icon={<Play size={18} />}
              >
                Preview Slideshow
              </Button>
              <Button
                variant="secondary"
                fullWidth
                icon={<Send size={18} />}
                onClick={handlePostToTikTok}
                disabled={!allImagesComplete}
              >
                Post to TikTok
              </Button>
              <Button
                variant="primary"
                fullWidth
                icon={<Send size={18} />}
                onClick={handlePostToInstagram}
                disabled={!allImagesComplete}
              >
                Post to Instagram
              </Button>
            </div>
          </GlassCard>

          {/* TikTok Status */}
          <GlassCard gradient={tiktokStatus?.authenticated ? 'green' : 'orange'} padding="md">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {tiktokStatus?.authenticated ? (
                <>
                  <CheckCircle2 size={20} style={{ color: '#16a34a' }} />
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>
                      TikTok Connected
                    </p>
                    <p style={{ fontSize: '12px', color: '#64748b' }}>
                      Ready to post slideshows
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <AlertCircle size={20} style={{ color: '#d97706' }} />
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>
                      TikTok Not Connected
                    </p>
                    <a
                      href={`${API_BASE_URL}/api/tiktok/auth`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ fontSize: '12px', color: '#667eea', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      Connect Account <ExternalLink size={12} />
                    </a>
                  </div>
                </>
              )}
            </div>
          </GlassCard>
          
          {/* Instagram Status */}
          <GlassCard gradient={instagramStatus?.connected ? 'green' : 'orange'} padding="md">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {instagramStatus?.connected ? (
                <>
                  <CheckCircle2 size={20} style={{ color: '#16a34a' }} />
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>
                      Instagram Connected
                    </p>
                    <p style={{ fontSize: '12px', color: '#64748b' }}>
                      via Post Bridge
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <AlertCircle size={20} style={{ color: '#d97706' }} />
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>
                      Instagram Not Connected
                    </p>
                    <a
                      href="https://post-bridge.com/dashboard"
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ fontSize: '12px', color: '#667eea', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      Connect via Post Bridge <ExternalLink size={12} />
                    </a>
                  </div>
                </>
              )}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* TikTok Post Modal */}
      <AnimatePresence>
        {showTikTokModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              backdropFilter: 'blur(4px)',
            }}
            onClick={() => !postToTikTokMutation.isPending && setShowTikTokModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              style={{
                background: 'white',
                borderRadius: '24px',
                padding: '32px',
                width: '100%',
                maxWidth: '480px',
                boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>
                  Post to TikTok
                </h2>
                <button
                  onClick={() => setShowTikTokModal(false)}
                  disabled={postToTikTokMutation.isPending}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#94a3b8',
                  }}
                >
                  <X size={20} />
                </button>
              </div>

              {postResult ? (
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                  <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '20px',
                    background: postResult.success ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px',
                  }}>
                    {postResult.success ? (
                      <CheckCircle2 size={32} style={{ color: '#22c55e' }} />
                    ) : (
                      <AlertCircle size={32} style={{ color: '#ef4444' }} />
                    )}
                  </div>
                  <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>
                    {postResult.success ? 'Sent to TikTok Drafts!' : 'Failed to Post'}
                  </h3>
                  <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '24px' }}>
                    {postResult.message}
                  </p>
                  <Button variant="primary" onClick={() => setShowTikTokModal(false)}>
                    Close
                  </Button>
                </div>
              ) : (
                <>
                  <div style={{ marginBottom: '24px' }}>
                    <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>
                      Caption
                    </label>
                    <textarea
                      className="textarea"
                      value={tiktokCaption}
                      onChange={(e) => setTiktokCaption(e.target.value)}
                      placeholder="Enter a caption for your TikTok..."
                      rows={3}
                    />
                    <p style={{ fontSize: '12px', color: '#64748b', marginTop: '6px' }}>
                      This slideshow will be sent to your TikTok drafts for final review.
                    </p>
                  </div>

                  <div style={{
                    padding: '16px',
                    background: 'rgba(102, 126, 234, 0.05)',
                    borderRadius: '12px',
                    marginBottom: '24px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <ImageIcon size={20} style={{ color: '#667eea' }} />
                      <div>
                        <p style={{ fontSize: '14px', fontWeight: 500, color: '#0f172a' }}>
                          {completedSlides.length} images ready
                        </p>
                        <p style={{ fontSize: '12px', color: '#64748b' }}>
                          Will be posted as a photo slideshow
                        </p>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '12px' }}>
                    <Button
                      variant="secondary"
                      fullWidth
                      onClick={() => setShowTikTokModal(false)}
                      disabled={postToTikTokMutation.isPending}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="primary"
                      fullWidth
                      onClick={confirmTikTokPost}
                      loading={postToTikTokMutation.isPending}
                      icon={<Send size={18} />}
                    >
                      Send to Drafts
                    </Button>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Instagram Post Modal */}
      <AnimatePresence>
        {showInstagramModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              backdropFilter: 'blur(4px)',
            }}
            onClick={() => !postToInstagramMutation.isPending && setShowInstagramModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              style={{
                background: 'white',
                borderRadius: '24px',
                padding: '32px',
                width: '100%',
                maxWidth: '520px',
                boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <h2 style={{ 
                  fontSize: '20px', 
                  fontWeight: 700, 
                  background: 'linear-gradient(135deg, #833AB4 0%, #FD1D1D 50%, #FCB045 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text'
                }}>
                  Post to Instagram
                </h2>
                <button
                  onClick={() => setShowInstagramModal(false)}
                  disabled={postToInstagramMutation.isPending}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#94a3b8',
                  }}
                >
                  <X size={20} />
                </button>
              </div>

              {instagramPostResult ? (
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                  <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '20px',
                    background: instagramPostResult.success ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px',
                  }}>
                    {instagramPostResult.success ? (
                      <CheckCircle2 size={32} style={{ color: '#22c55e' }} />
                    ) : (
                      <AlertCircle size={32} style={{ color: '#ef4444' }} />
                    )}
                  </div>
                  <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>
                    {instagramPostResult.success ? 'Posted to Instagram!' : 'Failed to Post'}
                  </h3>
                  <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '16px' }}>
                    {instagramPostResult.message}
                  </p>
                  {instagramPostResult.url && (
                    <a
                      href={instagramPostResult.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ 
                        display: 'inline-flex', 
                        alignItems: 'center', 
                        gap: '6px',
                        fontSize: '14px', 
                        color: '#833AB4', 
                        marginBottom: '16px',
                        textDecoration: 'none'
                      }}
                    >
                      View on Instagram <ExternalLink size={14} />
                    </a>
                  )}
                  <div>
                    <Button variant="primary" onClick={() => setShowInstagramModal(false)}>
                      Close
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>
                      Caption
                    </label>
                    <textarea
                      className="textarea"
                      value={instagramCaption}
                      onChange={(e) => setInstagramCaption(e.target.value)}
                      placeholder="Enter a caption for your Instagram post..."
                      rows={3}
                    />
                  </div>
                  
                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>
                      Hashtags
                    </label>
                    <input
                      type="text"
                      className="input"
                      value={instagramHashtags}
                      onChange={(e) => setInstagramHashtags(e.target.value)}
                      placeholder="philosophy, wisdom, stoicism"
                      style={{
                        width: '100%',
                        padding: '12px 16px',
                        borderRadius: '12px',
                        border: '1px solid rgba(148, 163, 184, 0.3)',
                        fontSize: '14px',
                        background: 'rgba(248, 250, 252, 0.5)',
                      }}
                    />
                    <p style={{ fontSize: '12px', color: '#64748b', marginTop: '6px' }}>
                      Comma-separated hashtags. <strong>#philosophizemeapp</strong> is always included automatically.
                    </p>
                  </div>

                  <div style={{
                    padding: '16px',
                    background: 'linear-gradient(135deg, rgba(131, 58, 180, 0.05) 0%, rgba(253, 29, 29, 0.05) 50%, rgba(252, 176, 69, 0.05) 100%)',
                    borderRadius: '12px',
                    marginBottom: '24px',
                    border: '1px solid rgba(131, 58, 180, 0.1)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <ImageIcon size={20} style={{ color: '#833AB4' }} />
                      <div>
                        <p style={{ fontSize: '14px', fontWeight: 500, color: '#0f172a' }}>
                          {Math.min(completedSlides.length, 10)} images ready
                        </p>
                        <p style={{ fontSize: '12px', color: '#64748b' }}>
                          Will be posted as a carousel (max 10 images)
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div style={{
                    padding: '12px 16px',
                    background: 'rgba(245, 158, 11, 0.1)',
                    borderRadius: '10px',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                  }}>
                    <AlertCircle size={18} style={{ color: '#d97706', flexShrink: 0 }} />
                    <p style={{ fontSize: '13px', color: '#92400e' }}>
                      This will post directly to Instagram (not to drafts).
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: '12px' }}>
                    <Button
                      variant="secondary"
                      fullWidth
                      onClick={() => setShowInstagramModal(false)}
                      disabled={postToInstagramMutation.isPending}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="primary"
                      fullWidth
                      onClick={confirmInstagramPost}
                      loading={postToInstagramMutation.isPending}
                      icon={<Send size={18} />}
                    >
                      Post Now
                    </Button>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
