import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Wand2,
  RefreshCw,
  Edit3,
  Save,
  X,
  ChevronDown,
  ChevronUp,
  Check,
  Sparkles,
  BookOpen,
  Palette,
  Lightbulb,
  GraduationCap,
  Brain,
  MessageCircle,
  Film,
} from 'lucide-react';
import {
  generateScript,
  getProject,
  regenerateSlideScript,
  updateSlideScript,
  approveScript,
  apiClient,
} from '../api/client';
import type { Slide } from '../api/client';
import GlassCard from '../components/GlassCard';
import Button from '../components/Button';

interface ContentType {
  id: string;
  name: string;
  description: string;
  example: string;
  default_image_style: string;
}

interface ImageStyle {
  id: string;
  name: string;
  description: string;
}

const CONTENT_TYPE_ICONS: Record<string, React.ReactNode> = {
  list_educational: <GraduationCap size={24} />,
  list_existential: <Brain size={24} />,
  wisdom_slideshow: <MessageCircle size={24} />,
  narrative_story: <Film size={24} />,
};

const IMAGE_STYLE_COLORS: Record<string, string> = {
  classical: 'linear-gradient(135deg, #8B4513 0%, #D4AF37 100%)',
  surreal: 'linear-gradient(135deg, #9333ea 0%, #ec4899 100%)',
  cinematic: 'linear-gradient(135deg, #0f172a 0%, #1e40af 100%)',
  minimal: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
};

const SUGGESTED_TOPICS: Record<string, string[]> = {
  list_educational: [
    '5 Stoic philosophers who changed history',
    '6 ancient schools of thought you should know',
    '4 philosophers who faced death bravely',
  ],
  list_existential: [
    '5 signs your mind is evolving',
    '4 wake-up calls that spark self-awareness',
    '6 things that happen when you stop living on autopilot',
  ],
  wisdom_slideshow: [
    'Why you can\'t think clearly',
    'The trap of chasing happiness',
    '4 mental traps that keep you stuck',
  ],
  narrative_story: [
    'The day Socrates chose death over silence',
    'How Marcus Aurelius faced the plague',
    'Diogenes meets Alexander the Great',
  ],
};

export default function ScriptGenerator() {
  const [topic, setTopic] = useState('');
  const [selectedContentType, setSelectedContentType] = useState('wisdom_slideshow');
  const [selectedImageStyle, setSelectedImageStyle] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [expandedSlideId, setExpandedSlideId] = useState<string | null>(null);
  const [editingSlideId, setEditingSlideId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<Slide>>({});

  // Fetch content types
  const { data: contentTypesData } = useQuery({
    queryKey: ['contentTypes'],
    queryFn: async () => {
      const response = await apiClient.get('/scripts/content-types');
      return response.data;
    },
  });

  // Fetch image styles
  const { data: imageStylesData } = useQuery({
    queryKey: ['imageStyles'],
    queryFn: async () => {
      const response = await apiClient.get('/scripts/image-styles');
      return response.data;
    },
  });

  const contentTypes: ContentType[] = contentTypesData?.content_types || [];
  const imageStyles: ImageStyle[] = imageStylesData?.image_styles || [];

  // Set default image style based on content type
  useEffect(() => {
    const ct = contentTypes.find((c) => c.id === selectedContentType);
    if (ct && !selectedImageStyle) {
      setSelectedImageStyle(ct.default_image_style);
    }
  }, [selectedContentType, contentTypes, selectedImageStyle]);

  // Update image style when content type changes
  const handleContentTypeChange = (ctId: string) => {
    setSelectedContentType(ctId);
    const ct = contentTypes.find((c) => c.id === ctId);
    if (ct) {
      setSelectedImageStyle(ct.default_image_style);
    }
  };

  // Fetch project when we have a projectId
  const { data: project, refetch: refetchProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  });

  // Generate script mutation
  const generateMutation = useMutation({
    mutationFn: generateScript,
    onSuccess: (data) => {
      setProjectId(data.project_id);
    },
  });

  // Regenerate single slide mutation
  const regenerateSlideMutation = useMutation({
    mutationFn: ({
      projectId,
      slideIndex,
      instruction,
    }: {
      projectId: string;
      slideIndex: number;
      instruction?: string;
    }) => regenerateSlideScript(projectId, slideIndex, instruction),
    onSuccess: () => {
      refetchProject();
    },
  });

  // Update slide mutation
  const updateSlideMutation = useMutation({
    mutationFn: ({
      projectId,
      slideId,
      data,
    }: {
      projectId: string;
      slideId: string;
      data: { title?: string | null; subtitle?: string | null; visual_description?: string | null; narration?: string | null };
    }) => updateSlideScript(projectId, slideId, data),
    onSuccess: () => {
      setEditingSlideId(null);
      setEditForm({});
      refetchProject();
    },
  });

  // Approve script mutation
  const approveMutation = useMutation({
    mutationFn: approveScript,
    onSuccess: () => {
      refetchProject();
    },
  });

  const handleGenerate = () => {
    if (!topic.trim()) return;
    generateMutation.mutate({
      topic,
      content_type: selectedContentType,
      image_style: selectedImageStyle,
    });
  };

  const handleEditSlide = (slide: Slide) => {
    setEditingSlideId(slide.id);
    setEditForm({
      title: slide.title || '',
      subtitle: slide.subtitle || '',
      visual_description: slide.visual_description || '',
    });
  };

  const handleSaveEdit = () => {
    if (editingSlideId && projectId) {
      updateSlideMutation.mutate({
        projectId,
        slideId: editingSlideId,
        data: editForm,
      });
    }
  };

  const handleCancelEdit = () => {
    setEditingSlideId(null);
    setEditForm({});
  };

  const handleRegenerateSlide = (slideIndex: number) => {
    if (projectId) {
      regenerateSlideMutation.mutate({ projectId, slideIndex });
    }
  };

  const handleStartOver = () => {
    setProjectId(null);
    setTopic('');
    setExpandedSlideId(null);
    setEditingSlideId(null);
  };

  const slides = project?.slides || [];
  const suggestedTopics = SUGGESTED_TOPICS[selectedContentType] || [];

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
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(102, 126, 234, 0.35)',
            }}
            whileHover={{ scale: 1.05, rotate: 5 }}
          >
            <Sparkles size={26} style={{ color: 'white' }} />
          </motion.div>
          <div>
            <h1
              style={{
                fontSize: '28px',
                fontWeight: 800,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              Script Generator
            </h1>
            <p style={{ color: '#64748b', marginTop: '4px' }}>
              Create philosophical slideshows with AI-powered scripts
            </p>
          </div>
        </div>
        {projectId && (
          <Button variant="secondary" onClick={handleStartOver}>
            Start Over
          </Button>
        )}
      </div>

      {/* Input Section - Show when no project */}
      {!projectId && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
        >
          {/* Content Type Selection */}
          <GlassCard padding="lg">
            <h3
              style={{
                fontWeight: 700,
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                color: '#0f172a',
                fontSize: '18px',
              }}
            >
              <BookOpen size={22} style={{ color: '#667eea' }} />
              1. Choose Content Type
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
              {contentTypes.map((ct) => (
                <motion.button
                  key={ct.id}
                  onClick={() => handleContentTypeChange(ct.id)}
                  style={{
                    textAlign: 'left',
                    padding: '20px',
                    borderRadius: '16px',
                    border:
                      selectedContentType === ct.id
                        ? '2px solid #667eea'
                        : '1px solid rgba(148, 163, 184, 0.3)',
                    background: selectedContentType === ct.id ? 'rgba(102, 126, 234, 0.08)' : 'white',
                    cursor: 'pointer',
                  }}
                  whileHover={{ borderColor: '#667eea', y: -2 }}
                >
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '12px',
                      background:
                        selectedContentType === ct.id
                          ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                          : 'rgba(148, 163, 184, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: '12px',
                      color: selectedContentType === ct.id ? 'white' : '#64748b',
                    }}
                  >
                    {CONTENT_TYPE_ICONS[ct.id] || <BookOpen size={24} />}
                  </div>
                  <p
                    style={{
                      fontSize: '15px',
                      fontWeight: 700,
                      color: selectedContentType === ct.id ? '#667eea' : '#0f172a',
                      marginBottom: '6px',
                    }}
                  >
                    {ct.name}
                  </p>
                  <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>
                    {ct.description}
                  </p>
                  <p
                    style={{
                      fontSize: '11px',
                      color: '#94a3b8',
                      fontStyle: 'italic',
                      padding: '6px 10px',
                      background: 'rgba(148, 163, 184, 0.1)',
                      borderRadius: '6px',
                    }}
                  >
                    "{ct.example}"
                  </p>
                </motion.button>
              ))}
            </div>
          </GlassCard>

          {/* Image Style Selection */}
          <GlassCard padding="lg">
            <h3
              style={{
                fontWeight: 700,
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                color: '#0f172a',
                fontSize: '18px',
              }}
            >
              <Palette size={22} style={{ color: '#667eea' }} />
              2. Choose Image Style
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 500,
                  color: '#64748b',
                  marginLeft: 'auto',
                }}
              >
                Auto-selected based on content type
              </span>
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
              {imageStyles.map((style) => (
                <motion.button
                  key={style.id}
                  onClick={() => setSelectedImageStyle(style.id)}
                  style={{
                    textAlign: 'center',
                    padding: '20px',
                    borderRadius: '16px',
                    border:
                      selectedImageStyle === style.id
                        ? '2px solid #667eea'
                        : '1px solid rgba(148, 163, 184, 0.3)',
                    background: 'white',
                    cursor: 'pointer',
                  }}
                  whileHover={{ borderColor: '#667eea', y: -2 }}
                >
                  <div
                    style={{
                      width: '100%',
                      height: '60px',
                      borderRadius: '10px',
                      background: IMAGE_STYLE_COLORS[style.id] || '#e2e8f0',
                      marginBottom: '12px',
                      border:
                        selectedImageStyle === style.id
                          ? '2px solid #667eea'
                          : '1px solid rgba(148, 163, 184, 0.2)',
                    }}
                  />
                  <p
                    style={{
                      fontSize: '14px',
                      fontWeight: 600,
                      color: selectedImageStyle === style.id ? '#667eea' : '#0f172a',
                      marginBottom: '4px',
                    }}
                  >
                    {style.name}
                  </p>
                  <p style={{ fontSize: '11px', color: '#64748b' }}>{style.description}</p>
                </motion.button>
              ))}
            </div>
          </GlassCard>

          {/* Topic Input */}
          <GlassCard padding="lg">
            <h3
              style={{
                fontWeight: 700,
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                color: '#0f172a',
                fontSize: '18px',
              }}
            >
              <Lightbulb size={22} style={{ color: '#667eea' }} />
              3. Enter Your Topic
            </h3>
            <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '12px' }}>
              Enter any topic - we'll enhance it into a compelling philosophical slideshow
            </p>
            <textarea
              className="textarea"
              style={{ fontSize: '16px', minHeight: '80px', marginBottom: '16px' }}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., anxiety, stoicism, why we procrastinate, the fear of failure..."
            />

            {/* Suggested Topics */}
            <div style={{ marginBottom: '20px' }}>
              <p style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>
                SUGGESTIONS FOR {contentTypes.find((c) => c.id === selectedContentType)?.name?.toUpperCase()}:
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {suggestedTopics.map((suggestion) => (
                  <motion.button
                    key={suggestion}
                    onClick={() => setTopic(suggestion)}
                    style={{
                      padding: '8px 14px',
                      background: topic === suggestion ? 'rgba(102, 126, 234, 0.15)' : 'rgba(148, 163, 184, 0.1)',
                      border: topic === suggestion ? '1px solid #667eea' : '1px solid transparent',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      color: topic === suggestion ? '#667eea' : '#64748b',
                      fontSize: '13px',
                    }}
                    whileHover={{ background: 'rgba(102, 126, 234, 0.1)' }}
                  >
                    {suggestion}
                  </motion.button>
                ))}
              </div>
            </div>

            <Button
              variant="gradient-purple"
              size="lg"
              fullWidth
              onClick={handleGenerate}
              loading={generateMutation.isPending}
              icon={<Wand2 size={20} />}
            >
              Generate Script
            </Button>
          </GlassCard>
        </motion.div>
      )}

      {/* Script Review Section - Show when we have a project */}
      {projectId && project && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
        >
          {/* Project Header */}
          <GlassCard gradient="purple" padding="lg">
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
              <div style={{ flex: 1 }}>
                <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                  Review Your Script
                </h2>
                <p style={{ fontSize: '15px', color: '#64748b', marginBottom: '12px' }}>
                  Edit individual slides, regenerate specific ones, or try a different style.
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <span
                    style={{
                      padding: '6px 12px',
                      background: 'rgba(102, 126, 234, 0.1)',
                      borderRadius: '8px',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: '#667eea',
                    }}
                  >
                    {project.topic}
                  </span>
                  <span
                    style={{
                      padding: '6px 12px',
                      background: 'rgba(102, 126, 234, 0.1)',
                      borderRadius: '8px',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: '#667eea',
                    }}
                  >
                    {slides.length} slides
                  </span>
                  <span
                    style={{
                      padding: '6px 12px',
                      background: 'rgba(102, 126, 234, 0.1)',
                      borderRadius: '8px',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: '#667eea',
                    }}
                  >
                    {project.script_style}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <Button
                  variant="primary"
                  onClick={() => approveMutation.mutate(projectId)}
                  icon={<Check size={20} />}
                  loading={approveMutation.isPending}
                  disabled={project.script_approved === 'Y'}
                >
                  {project.script_approved === 'Y' ? 'Approved' : 'Approve & Continue'}
                </Button>
              </div>
            </div>
          </GlassCard>

          {/* Slides Preview */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {slides.map((slide, index) => {
              const isExpanded = expandedSlideId === slide.id;
              const isEditing = editingSlideId === slide.id;
              const isHook = index === 0;
              const isCta = index === slides.length - 1;

              return (
                <motion.div
                  key={slide.id}
                  layout
                  style={{ gridColumn: isExpanded ? '1 / -1' : 'auto' }}
                >
                  <GlassCard
                    padding="none"
                    style={{
                      overflow: 'hidden',
                      border: isExpanded ? '2px solid #667eea' : '1px solid rgba(148, 163, 184, 0.2)',
                    }}
                  >
                    {/* Slide Header */}
                    <div
                      style={{
                        padding: '16px 20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        background: isExpanded ? 'rgba(102, 126, 234, 0.03)' : 'transparent',
                      }}
                      onClick={() => setExpandedSlideId(isExpanded ? null : slide.id)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '36px',
                            height: '36px',
                            borderRadius: '10px',
                            background: isHook
                              ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                              : isCta
                              ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                              : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: 'white',
                            fontSize: '13px',
                            fontWeight: 700,
                          }}
                        >
                          {isHook ? 'H' : isCta ? 'CTA' : index}
                        </span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a', marginBottom: '2px' }}>
                            {slide.title || `Slide ${index + 1}`}
                          </p>
                          <p
                            style={{
                              fontSize: '13px',
                              color: '#64748b',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {slide.subtitle?.substring(0, 60)}
                            {(slide.subtitle?.length || 0) > 60 ? '...' : ''}
                          </p>
                        </div>
                      </div>
                      {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </div>

                    {/* Expanded Content */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          style={{ overflow: 'hidden' }}
                        >
                          <div
                            style={{
                              padding: '20px',
                              borderTop: '1px solid rgba(148, 163, 184, 0.1)',
                              background: 'white',
                            }}
                          >
                            {isEditing ? (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                <div>
                                  <label className="label">Title</label>
                                  <input
                                    className="input"
                                    value={editForm.title || ''}
                                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                                  />
                                </div>
                                <div>
                                  <label className="label">Content</label>
                                  <textarea
                                    className="textarea"
                                    style={{ minHeight: '150px' }}
                                    value={editForm.subtitle || ''}
                                    onChange={(e) => setEditForm({ ...editForm, subtitle: e.target.value })}
                                  />
                                </div>
                                <div>
                                  <label className="label">Visual Description</label>
                                  <textarea
                                    className="textarea"
                                    value={editForm.visual_description || ''}
                                    onChange={(e) => setEditForm({ ...editForm, visual_description: e.target.value })}
                                    rows={3}
                                  />
                                </div>
                                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                                  <Button variant="secondary" onClick={handleCancelEdit} icon={<X size={16} />}>
                                    Cancel
                                  </Button>
                                  <Button
                                    variant="primary"
                                    onClick={handleSaveEdit}
                                    icon={<Save size={16} />}
                                    loading={updateSlideMutation.isPending}
                                  >
                                    Save Changes
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                <div>
                                  <p style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>
                                    CONTENT
                                  </p>
                                  <p style={{ fontSize: '15px', color: '#0f172a', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                                    {slide.subtitle}
                                  </p>
                                </div>
                                {slide.visual_description && (
                                  <div>
                                    <p style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>
                                      VISUAL
                                    </p>
                                    <p style={{ fontSize: '14px', color: '#64748b' }}>{slide.visual_description}</p>
                                  </div>
                                )}
                                <div
                                  style={{
                                    display: 'flex',
                                    gap: '12px',
                                    paddingTop: '12px',
                                    borderTop: '1px solid rgba(148, 163, 184, 0.1)',
                                  }}
                                >
                                  <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={(e) => {
                                      e?.stopPropagation();
                                      handleEditSlide(slide);
                                    }}
                                    icon={<Edit3 size={14} />}
                                  >
                                    Edit
                                  </Button>
                                  <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={(e) => {
                                      e?.stopPropagation();
                                      handleRegenerateSlide(index);
                                    }}
                                    icon={<RefreshCw size={14} />}
                                    loading={regenerateSlideMutation.isPending}
                                  >
                                    Regenerate
                                  </Button>
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </GlassCard>
                </motion.div>
              );
            })}
          </div>

          {/* Approval Status */}
          {project.script_approved === 'Y' && (
            <GlassCard gradient="green" padding="md">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Check size={24} style={{ color: '#10b981' }} />
                <div>
                  <p style={{ fontSize: '16px', fontWeight: 600, color: '#0f172a' }}>Script Approved!</p>
                  <p style={{ fontSize: '14px', color: '#64748b' }}>
                    Your script is ready. You can now proceed to generate images.
                  </p>
                </div>
              </div>
            </GlassCard>
          )}
        </motion.div>
      )}
    </div>
  );
}
