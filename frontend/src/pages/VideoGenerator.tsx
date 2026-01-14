import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Video, 
  Wand2, 
  Play,
  ChevronLeft,
  ChevronRight,
  Download,
  Zap,
  Clock,
  Sparkles
} from 'lucide-react';
import {
  generateScript,
  getProject,
  generateBatchImages,
  getSlideImageUrl,
} from '../api/client';
import GlassCard from '../components/GlassCard';
import Button from '../components/Button';
import StepIndicator from '../components/StepIndicator';

const STEPS = [
  { id: 'topic', label: 'Topic', description: 'Enter story' },
  { id: 'script', label: 'Script', description: 'Review narrative' },
  { id: 'images', label: 'Images', description: 'Generate frames' },
  { id: 'video', label: 'Video', description: 'AI transitions' },
  { id: 'export', label: 'Export', description: 'Download' },
];

const TRANSITION_STYLES = [
  { id: 'smooth', name: 'Smooth Flow', description: 'Gentle morphing between scenes', icon: '🌊' },
  { id: 'dynamic', name: 'Dynamic', description: 'Energetic camera movements', icon: '⚡' },
  { id: 'cinematic', name: 'Cinematic', description: 'Film-like transitions', icon: '🎬' },
  { id: 'zoom', name: 'Zoom & Pan', description: 'Ken Burns effect', icon: '🔍' },
];

const VIDEO_PRESETS = [
  { id: 'tiktok', name: 'TikTok', resolution: '1080x1920', fps: 30, duration: '60s' },
  { id: 'reels', name: 'Instagram Reels', resolution: '1080x1920', fps: 30, duration: '90s' },
  { id: 'youtube', name: 'YouTube Shorts', resolution: '1080x1920', fps: 30, duration: '60s' },
  { id: 'square', name: 'Square (IG)', resolution: '1080x1080', fps: 30, duration: '60s' },
];

const SUGGESTED_TOPICS = [
  'The Transformation: From Slave to Sage',
  'What Marcus Aurelius Wrote at Night',
  'The Moment Buddha Achieved Enlightenment',
  'How Diogenes Humiliated Alexander the Great',
];

export default function VideoGenerator() {
  const [currentStep, setCurrentStep] = useState(0);
  const [topic, setTopic] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [selectedTransition, setSelectedTransition] = useState('cinematic');
  const [selectedPreset, setSelectedPreset] = useState('tiktok');
  const [selectedTheme, setSelectedTheme] = useState('scene_portrait');
  const [selectedModel] = useState('gpt15');
  const [selectedFont] = useState('montserrat');
  const [selectedVoice, setSelectedVoice] = useState('adam');
  const [processingVideo, setProcessingVideo] = useState(false);

  // Fetch project
  const { data: project, refetch: refetchProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  });

  // Generate script mutation
  const generateScriptMutation = useMutation({
    mutationFn: generateScript,
    onSuccess: (data) => {
      setProjectId(data.project_id);
      setCurrentStep(1);
    },
  });

  // Generate images mutation
  const generateImagesMutation = useMutation({
    mutationFn: ({ projectId, model, font }: { projectId: string; model: string; font: string }) =>
      generateBatchImages(projectId, { model, font }),
    onSuccess: () => {
      const interval = setInterval(() => refetchProject(), 2000);
      setTimeout(() => clearInterval(interval), 60000);
    },
  });

  const handleGenerateScript = () => {
    if (!topic.trim()) return;
    generateScriptMutation.mutate({
      topic,
      content_type: 'narrative',
      num_slides: 8,
    });
  };

  const slides = project?.slides || [];
  const completedSlides = slides.filter((s) => s.image_status === 'complete').length;
  const currentPreset = VIDEO_PRESETS.find((p) => p.id === selectedPreset);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <motion.div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '18px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(59, 130, 246, 0.35)',
            }}
            whileHover={{ scale: 1.05, rotate: 5 }}
          >
            <Video size={26} style={{ color: 'white' }} />
          </motion.div>
          <div>
            <h1 style={{ 
              fontSize: '28px', 
              fontWeight: 800, 
              background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              Image-to-Video Generator
            </h1>
            <p style={{ color: '#64748b', marginTop: '4px' }}>
              Transform static images into dynamic videos with AI transitions
            </p>
          </div>
        </div>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px', 
          padding: '8px 16px', 
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)',
          borderRadius: '20px',
          border: '1px solid rgba(59, 130, 246, 0.2)',
        }}>
          <Zap size={16} style={{ color: '#3b82f6' }} />
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#3b82f6' }}>Powered by fal.ai Helix</span>
        </div>
      </div>

      {/* Step Indicator */}
      <GlassCard padding="lg">
        <StepIndicator
          steps={STEPS}
          currentStep={currentStep}
          onStepClick={(step) => step <= currentStep && setCurrentStep(step)}
          variant="blue"
        />
      </GlassCard>

      {/* Step Content */}
      <AnimatePresence mode="wait">
        {/* Step 0: Topic Input */}
        {currentStep === 0 && (
          <motion.div
            key="topic"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}
          >
            {/* Main input */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <GlassCard padding="lg">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  <div>
                    <label style={{ 
                      display: 'block', 
                      fontSize: '16px', 
                      fontWeight: 600, 
                      color: '#0f172a', 
                      marginBottom: '8px' 
                    }}>
                      Video Concept
                    </label>
                    <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '12px' }}>
                      Describe the story or concept for your video
                    </p>
                    <textarea
                      className="textarea"
                      style={{ fontSize: '16px', minHeight: '120px' }}
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="e.g., The moment Marcus Aurelius realized he must accept what he cannot change..."
                    />
                  </div>

                  <Button
                    variant="gradient-blue"
                    size="lg"
                    fullWidth
                    onClick={handleGenerateScript}
                    loading={generateScriptMutation.isPending}
                    icon={<Wand2 size={20} />}
                  >
                    Generate Video Script
                  </Button>
                </div>
              </GlassCard>

              {/* Suggested topics */}
              <div>
                <h3 style={{ 
                  fontSize: '14px', 
                  fontWeight: 600, 
                  color: '#64748b', 
                  marginBottom: '12px' 
                }}>
                  Video Ideas
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  {SUGGESTED_TOPICS.map((suggestion) => (
                    <motion.button
                      key={suggestion}
                      onClick={() => setTopic(suggestion)}
                      style={{
                        textAlign: 'left',
                        padding: '14px 18px',
                        background: 'rgba(255, 255, 255, 0.8)',
                        border: '1px solid rgba(148, 163, 184, 0.3)',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        color: '#334155',
                        fontSize: '14px',
                      }}
                      whileHover={{ 
                        borderColor: '#3b82f6', 
                        background: 'rgba(59, 130, 246, 0.08)',
                        color: '#3b82f6',
                      }}
                    >
                      {suggestion}
                    </motion.button>
                  ))}
                </div>
              </div>
            </div>

            {/* Settings sidebar */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Video preset */}
              <GlassCard padding="lg">
                <h3 style={{ 
                  fontWeight: 600, 
                  marginBottom: '16px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px',
                  color: '#0f172a',
                }}>
                  <Video size={20} style={{ color: '#3b82f6' }} />
                  Video Format
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {VIDEO_PRESETS.map((preset) => (
                    <motion.button
                      key={preset.id}
                      onClick={() => setSelectedPreset(preset.id)}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        padding: '12px 14px',
                        borderRadius: '12px',
                        border: selectedPreset === preset.id 
                          ? '2px solid #3b82f6' 
                          : '1px solid rgba(148, 163, 184, 0.3)',
                        background: selectedPreset === preset.id 
                          ? 'rgba(59, 130, 246, 0.1)' 
                          : 'white',
                        cursor: 'pointer',
                      }}
                      whileHover={{ borderColor: '#3b82f6' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ 
                          fontWeight: 600, 
                          color: selectedPreset === preset.id ? '#3b82f6' : '#0f172a',
                          fontSize: '14px',
                        }}>
                          {preset.name}
                        </span>
                        <span style={{ fontSize: '12px', color: '#64748b' }}>{preset.duration}</span>
                      </div>
                      <p style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                        {preset.resolution} @ {preset.fps}fps
                      </p>
                    </motion.button>
                  ))}
                </div>
              </GlassCard>

              {/* Transition style */}
              <GlassCard gradient="blue" padding="lg">
                <h3 style={{ 
                  fontWeight: 600, 
                  marginBottom: '16px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px',
                  color: '#0f172a',
                }}>
                  <Sparkles size={20} style={{ color: '#3b82f6' }} />
                  Transition Style
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  {TRANSITION_STYLES.map((style) => (
                    <motion.button
                      key={style.id}
                      onClick={() => setSelectedTransition(style.id)}
                      style={{
                        padding: '12px',
                        borderRadius: '12px',
                        border: selectedTransition === style.id 
                          ? '2px solid #3b82f6' 
                          : '1px solid rgba(148, 163, 184, 0.3)',
                        background: selectedTransition === style.id 
                          ? 'rgba(59, 130, 246, 0.1)' 
                          : 'white',
                        cursor: 'pointer',
                        textAlign: 'center',
                      }}
                      whileHover={{ borderColor: '#3b82f6' }}
                    >
                      <span style={{ fontSize: '20px' }}>{style.icon}</span>
                      <p style={{ 
                        fontSize: '12px', 
                        fontWeight: 600, 
                        marginTop: '6px',
                        color: selectedTransition === style.id ? '#3b82f6' : '#0f172a',
                      }}>
                        {style.name}
                      </p>
                    </motion.button>
                  ))}
                </div>
              </GlassCard>

              {/* Voice selection */}
              <GlassCard padding="lg">
                <h3 style={{ fontWeight: 600, marginBottom: '12px', color: '#0f172a' }}>Voice & Theme</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <label className="label">Narration Voice</label>
                    <select
                      className="select"
                      value={selectedVoice}
                      onChange={(e) => setSelectedVoice(e.target.value)}
                    >
                      <option value="adam">Adam - Authoritative</option>
                      <option value="rachel">Rachel - Soothing</option>
                      <option value="josh">Josh - Conversational</option>
                      <option value="antoni">Antoni - Dramatic</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Visual Theme</label>
                    <select
                      className="select"
                      value={selectedTheme}
                      onChange={(e) => setSelectedTheme(e.target.value)}
                    >
                      <option value="scene_portrait">Scene Portrait</option>
                      <option value="oil_contrast">Oil Contrast</option>
                      <option value="golden_dust">Golden Dust</option>
                      <option value="glitch_titans">Glitch Titans</option>
                    </select>
                  </div>
                </div>
              </GlassCard>
            </div>
          </motion.div>
        )}

        {/* Step 1: Script Review */}
        {currentStep === 1 && project && (
          <motion.div
            key="script"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a' }}>{project.name}</h2>
                <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>
                  {slides.length} scenes for video generation
                </p>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <Button
                  variant="secondary"
                  onClick={() => setCurrentStep(0)}
                  icon={<ChevronLeft size={18} />}
                >
                  Back
                </Button>
                <Button
                  variant="gradient-blue"
                  onClick={() => setCurrentStep(2)}
                  icon={<ChevronRight size={18} />}
                  iconPosition="right"
                >
                  Generate Images
                </Button>
              </div>
            </div>

            {/* Video timeline preview */}
            <GlassCard padding="lg">
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                <h3 style={{ fontWeight: 600, color: '#0f172a' }}>Video Timeline</h3>
                <div style={{ flex: 1, height: '1px', background: 'rgba(148, 163, 184, 0.2)' }} />
                <span style={{ fontSize: '14px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={14} />
                  ~{slides.length * 5}s estimated
                </span>
              </div>
              
              <div style={{ display: 'flex', gap: '12px', overflowX: 'auto', paddingBottom: '8px' }}>
                {slides.map((slide, index) => (
                  <motion.div
                    key={slide.id}
                    style={{
                      flexShrink: 0,
                      width: '140px',
                      padding: '14px',
                      background: 'rgba(248, 250, 252, 0.8)',
                      borderRadius: '14px',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                    }}
                    whileHover={{ borderColor: '#3b82f6', y: -4 }}
                  >
                    <div style={{ 
                      aspectRatio: '9/16', 
                      background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)', 
                      borderRadius: '10px', 
                      marginBottom: '10px', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center' 
                    }}>
                      <span style={{ fontSize: '24px', fontWeight: 700, color: '#3b82f6' }}>{index + 1}</span>
                    </div>
                    <p style={{ fontSize: '12px', fontWeight: 600, color: '#0f172a' }} className="truncate">{slide.title || `Scene ${index + 1}`}</p>
                    <p style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>~5s</p>
                  </motion.div>
                ))}
              </div>
            </GlassCard>

            {/* Scene details */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {slides.map((slide, index) => (
                <GlassCard key={slide.id} padding="md">
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                    <motion.div 
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: '12px',
                        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                      whileHover={{ scale: 1.05 }}
                    >
                      <span style={{ fontWeight: 700, color: '#3b82f6' }}>{index + 1}</span>
                    </motion.div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <h4 style={{ fontWeight: 600, color: '#0f172a' }}>{slide.title || `Scene ${index + 1}`}</h4>
                      <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>{slide.visual_description}</p>
                      {slide.narration && (
                        <p style={{ fontSize: '14px', fontStyle: 'italic', color: '#475569', marginTop: '8px', lineHeight: 1.6 }}>
                          "{slide.narration}"
                        </p>
                      )}
                    </div>
                    <span style={{
                      padding: '6px 12px',
                      fontSize: '12px',
                      fontWeight: 600,
                      borderRadius: '16px',
                      background: 'rgba(59, 130, 246, 0.1)',
                      color: '#3b82f6',
                    }}>
                      ~5s
                    </span>
                  </div>
                </GlassCard>
              ))}
            </div>
          </motion.div>
        )}

        {/* Step 2: Image Generation */}
        {currentStep === 2 && project && (
          <motion.div
            key="images"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
          >
            <GlassCard padding="lg">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a' }}>Generating Key Frames</h2>
                  <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>
                    {completedSlides} of {slides.length} frames complete
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <Button
                    variant="secondary"
                    onClick={() => setCurrentStep(1)}
                    icon={<ChevronLeft size={18} />}
                  >
                    Back
                  </Button>
                  <Button
                    variant="gradient-blue"
                    onClick={() => {
                      generateImagesMutation.mutate({
                        projectId: project.id,
                        model: selectedModel,
                        font: selectedFont,
                      });
                    }}
                    loading={generateImagesMutation.isPending}
                  >
                    Generate All Frames
                  </Button>
                </div>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-bar-fill"
                  style={{ 
                    width: `${(completedSlides / slides.length) * 100}%`,
                    background: 'linear-gradient(90deg, #3b82f6, #06b6d4)'
                  }}
                />
              </div>
            </GlassCard>

            {/* Frame grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
              {slides.map((slide, index) => (
                <GlassCard key={slide.id} padding="none" className="overflow-hidden">
                  <div style={{ aspectRatio: '9/16', position: 'relative', background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)' }}>
                    {slide.final_image_path ? (
                      <img
                        src={getSlideImageUrl(slide.final_image_path) || ''}
                        alt={slide.title || 'Frame'}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <motion.div
                          style={{
                            width: '32px',
                            height: '32px',
                            border: '3px solid transparent',
                            borderTopColor: '#3b82f6',
                            borderRadius: '50%',
                          }}
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        />
                      </div>
                    )}
                    <div style={{ 
                      position: 'absolute', 
                      top: '8px', 
                      left: '8px',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      background: 'rgba(59, 130, 246, 0.9)',
                      backdropFilter: 'blur(4px)',
                    }}>
                      <span style={{ fontSize: '11px', fontWeight: 600, color: 'white' }}>Frame {index + 1}</span>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>

            {completedSlides === slides.length && (
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="gradient-blue"
                  size="lg"
                  onClick={() => setCurrentStep(3)}
                  icon={<ChevronRight size={20} />}
                  iconPosition="right"
                >
                  Generate Video Transitions
                </Button>
              </div>
            )}
          </motion.div>
        )}

        {/* Step 3: Video Generation */}
        {currentStep === 3 && project && (
          <motion.div
            key="video"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
          >
            <GlassCard padding="xl">
              <div style={{ textAlign: 'center', padding: '32px 0' }}>
                <motion.div 
                  style={{
                    width: '100px',
                    height: '100px',
                    borderRadius: '28px',
                    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 28px',
                  }}
                  animate={{ scale: [1, 1.05, 1], rotate: [0, 5, -5, 0] }}
                  transition={{ duration: 4, repeat: Infinity }}
                >
                  <Zap size={48} style={{ color: '#3b82f6' }} />
                </motion.div>
                <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                  AI Video Generation
                </h2>
                <p style={{ color: '#64748b', marginBottom: '24px' }}>
                  Using fal.ai Helix model to create smooth transitions
                </p>
                
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '16px', marginBottom: '32px' }}>
                  <div style={{ padding: '12px 20px', background: 'rgba(248, 250, 252, 0.8)', borderRadius: '12px' }}>
                    <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Transition Style</p>
                    <p style={{ fontWeight: 600, color: '#0f172a' }}>{TRANSITION_STYLES.find(t => t.id === selectedTransition)?.name}</p>
                  </div>
                  <div style={{ padding: '12px 20px', background: 'rgba(248, 250, 252, 0.8)', borderRadius: '12px' }}>
                    <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Format</p>
                    <p style={{ fontWeight: 600, color: '#0f172a' }}>{currentPreset?.name}</p>
                  </div>
                  <div style={{ padding: '12px 20px', background: 'rgba(248, 250, 252, 0.8)', borderRadius: '12px' }}>
                    <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Frames</p>
                    <p style={{ fontWeight: 600, color: '#0f172a' }}>{slides.length} scenes</p>
                  </div>
                </div>
                
                <Button
                  variant="gradient-blue"
                  size="lg"
                  icon={<Video size={20} />}
                  loading={processingVideo}
                  onClick={() => {
                    setProcessingVideo(true);
                    setTimeout(() => {
                      setProcessingVideo(false);
                      setCurrentStep(4);
                    }, 3000);
                  }}
                >
                  {processingVideo ? 'Generating Video...' : 'Generate Video with AI Transitions'}
                </Button>
                
                {processingVideo && (
                  <p style={{ fontSize: '14px', color: '#64748b', marginTop: '16px' }}>
                    This may take 2-5 minutes depending on video length...
                  </p>
                )}
              </div>
            </GlassCard>

            {/* Frame sequence preview */}
            <GlassCard padding="lg">
              <h3 style={{ fontWeight: 600, marginBottom: '16px', color: '#0f172a' }}>Frame Sequence</h3>
              <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px' }}>
                {slides.map((slide, index) => (
                  <div key={slide.id} style={{ display: 'flex', alignItems: 'center' }}>
                    <motion.div 
                      style={{ 
                        flexShrink: 0, 
                        width: '100px', 
                        aspectRatio: '9/16', 
                        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)', 
                        borderRadius: '10px', 
                        overflow: 'hidden',
                        border: '2px solid rgba(59, 130, 246, 0.2)',
                      }}
                      whileHover={{ scale: 1.05, borderColor: '#3b82f6' }}
                    >
                      {slide.final_image_path && (
                        <img
                          src={getSlideImageUrl(slide.final_image_path) || ''}
                          alt={`Frame ${index + 1}`}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      )}
                    </motion.div>
                    {index < slides.length - 1 && (
                      <motion.div 
                        style={{ padding: '0 8px' }}
                        animate={{ x: [0, 4, 0] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        <ChevronRight size={20} style={{ color: '#3b82f6' }} />
                      </motion.div>
                    )}
                  </div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        )}

        {/* Step 4: Export */}
        {currentStep === 4 && project && (
          <motion.div
            key="export"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
          >
            <GlassCard padding="xl">
              <div style={{ textAlign: 'center', padding: '32px 0' }}>
                <motion.div 
                  style={{
                    width: '100px',
                    height: '100px',
                    borderRadius: '28px',
                    background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 28px',
                  }}
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Video size={48} style={{ color: '#22c55e' }} />
                </motion.div>
                <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                  Video Ready!
                </h2>
                <p style={{ color: '#64748b', marginBottom: '32px' }}>
                  Your {slides.length}-scene video with AI transitions is complete
                </p>
                
                {/* Video preview placeholder */}
                <motion.div 
                  style={{ 
                    maxWidth: '320px', 
                    margin: '0 auto 32px', 
                    aspectRatio: '9/16', 
                    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', 
                    borderRadius: '20px', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                  }}
                  whileHover={{ scale: 1.02 }}
                >
                  <motion.button 
                    style={{ 
                      width: '72px', 
                      height: '72px', 
                      borderRadius: '50%', 
                      background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)', 
                      border: 'none',
                      cursor: 'pointer',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      boxShadow: '0 8px 32px rgba(59, 130, 246, 0.4)',
                    }}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Play size={28} style={{ color: 'white', marginLeft: '4px' }} />
                  </motion.button>
                </motion.div>
                
                <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
                  <Button
                    variant="secondary"
                    size="lg"
                    icon={<Download size={20} />}
                  >
                    Download MP4
                  </Button>
                  <Button
                    variant="gradient-blue"
                    size="lg"
                    icon={<Video size={20} />}
                  >
                    Share to TikTok
                  </Button>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
