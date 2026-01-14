import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Wand2, 
  Image as ImageIcon, 
  Download, 
  Play,
  ChevronLeft,
  ChevronRight,
  Settings,
  Sparkles,
  RefreshCw,
  Check,
  History
} from 'lucide-react';
import {
  generateScript,
  getProject,
  generateSlideImage,
  generateBatchImages,
  updateSlide,
  deleteSlide,
  duplicateSlide,
  regenerateSlideScript,
  getAvailableModels,
  getProjects,
  getSlideImageUrl,
  getScriptStyles,
  approveScript,
  regenerateEntireScript,
  updateSlideScript,
} from '../api/client';
import type { Slide } from '../api/client';
import GlassCard from '../components/GlassCard';
import Button from '../components/Button';
import StepIndicator from '../components/StepIndicator';
import ScriptReview from '../components/ScriptReview';

const STEPS = [
  { id: 'topic', label: 'Topic', description: 'Enter your topic' },
  { id: 'review', label: 'Review Script', description: 'Review & approve' },
  { id: 'images', label: 'Images', description: 'Generate visuals' },
  { id: 'export', label: 'Export', description: 'Download' },
];

const THEME_OPTIONS = [
  { id: 'glitch_titans', name: 'Glitch Titans', description: 'Cracked glass, digital effects' },
  { id: 'oil_contrast', name: 'Oil Contrast', description: 'Renaissance oil painting style' },
  { id: 'golden_dust', name: 'Golden Dust', description: 'Elegant sepia with gold particles' },
  { id: 'scene_portrait', name: 'Scene Portrait', description: 'Cinematic philosopher scenes' },
];

const SUGGESTED_TOPICS = [
  '5 Stoic Philosophers Who Changed Everything',
  'The Day Socrates Chose Death Over Silence',
  'Marcus Aurelius: The Philosopher King',
  '7 Ancient Ideas That Explain Modern Anxiety',
  'Why Diogenes Lived in a Barrel',
];

// Session storage key for persisting state
const SESSION_KEY = 'static_slideshow_session';

interface SessionState {
  projectId: string | null;
  currentStep: number;
  topic: string;
  selectedTheme: string;
  selectedFont: string;
  selectedModel: string;
}

function loadSession(): SessionState | null {
  try {
    const saved = sessionStorage.getItem(SESSION_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

function saveSession(state: SessionState) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(state));
  } catch {
    // ignore
  }
}

export default function StaticSlideshow() {
  const queryClient = useQueryClient();
  const { projectId: urlProjectId } = useParams<{ projectId?: string }>();
  
  // Load initial state from session
  const savedSession = loadSession();
  
  const [currentStep, setCurrentStep] = useState(savedSession?.currentStep ?? 0);
  const [topic, setTopic] = useState(savedSession?.topic ?? '');
  const [projectId, setProjectId] = useState<string | null>(savedSession?.projectId ?? null);
  const [selectedTheme, setSelectedTheme] = useState(savedSession?.selectedTheme ?? 'golden_dust');
  const [selectedFont, setSelectedFont] = useState(savedSession?.selectedFont ?? 'montserrat');
  const [selectedModel, setSelectedModel] = useState(savedSession?.selectedModel ?? 'gpt15');
  const [selectedContentType, setSelectedContentType] = useState('auto');
  const [numSlides, setNumSlides] = useState(7);
  const [generatingSlideId, setGeneratingSlideId] = useState<string | null>(null);
  const [showRecentProjects, setShowRecentProjects] = useState(false);

  // Load project from URL if provided
  useEffect(() => {
    if (urlProjectId && urlProjectId !== projectId) {
      setProjectId(urlProjectId);
      // We'll determine the correct step once the project loads
    }
  }, [urlProjectId]);

  // Fetch recent projects for quick access
  const { data: recentProjectsData } = useQuery({
    queryKey: ['recent-projects'],
    queryFn: () => getProjects({ content_type: 'slideshow' }),
    staleTime: 30000,
  });
  
  // Extract projects array from response
  const recentProjects = recentProjectsData?.projects || [];

  // Fetch models
  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: getAvailableModels,
  });

  // Fetch script styles
  const { data: scriptStylesData } = useQuery({
    queryKey: ['script-styles'],
    queryFn: getScriptStyles,
    staleTime: Infinity,
  });

  const scriptStyles = scriptStylesData?.styles || [];

  // Fetch project when we have an ID
  const { data: project, refetch: refetchProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
    staleTime: 5000, // Keep data fresh
  });

  // Save session state whenever it changes
  useEffect(() => {
    saveSession({
      projectId,
      currentStep,
      topic,
      selectedTheme,
      selectedFont,
      selectedModel,
    });
  }, [projectId, currentStep, topic, selectedTheme, selectedFont, selectedModel]);
  
  // When project data loads (especially from URL), update step and topic
  useEffect(() => {
    if (project && projectId) {
      // Update topic from project
      if (!topic && project.topic) {
        setTopic(project.topic);
      }
      
      // If we just loaded from URL and step is 0, determine correct step based on project status
      if (urlProjectId && currentStep === 0 && project.slides?.length > 0) {
        if (project.status === 'script_review' || project.script_approved === 'N') {
          setCurrentStep(1); // Script review step
        } else if (project.script_approved === 'Y') {
          const hasImages = project.slides.some(s => s.image_status === 'complete');
          const allImagesComplete = project.slides.every(s => s.image_status === 'complete');
          
          if (allImagesComplete) {
            setCurrentStep(3);
          } else if (hasImages) {
            setCurrentStep(2);
          } else {
            setCurrentStep(2); // Go to images step
          }
        }
      }
    }
  }, [project, projectId, urlProjectId]);

  // Generate script mutation
  const generateScriptMutation = useMutation({
    mutationFn: generateScript,
    onSuccess: (data) => {
      setProjectId(data.project_id);
      setTopic(data.topic);
      setCurrentStep(1); // Go to script review step
      // Invalidate projects list
      queryClient.invalidateQueries({ queryKey: ['recent-projects'] });
    },
  });

  // Approve script mutation
  const approveScriptMutation = useMutation({
    mutationFn: approveScript,
    onSuccess: () => {
      refetchProject();
      setCurrentStep(2); // Go to images step
    },
  });

  // Regenerate entire script mutation
  const regenerateEntireScriptMutation = useMutation({
    mutationFn: ({ projectId, style }: { projectId: string; style?: string }) =>
      regenerateEntireScript(projectId, style),
    onSuccess: () => {
      refetchProject();
    },
  });

  // Update slide script mutation
  const updateSlideScriptMutation = useMutation({
    mutationFn: ({ projectId, slideId, data }: { projectId: string; slideId: string; data: { title?: string | null; subtitle?: string | null; visual_description?: string | null; narration?: string | null } }) =>
      updateSlideScript(projectId, slideId, data),
    onSuccess: () => refetchProject(),
  });

  // Load an existing project
  const loadProject = (proj: any) => {
    setProjectId(proj.id);
    setTopic(proj.topic || proj.name);
    
    // Get slides array safely
    const projSlides = proj.slides || [];
    
    // Determine step based on project state
    if (proj.status === 'script_review' || proj.script_approved === 'N') {
      setCurrentStep(1); // Script review
    } else if (proj.script_approved === 'Y') {
      const hasImages = projSlides.some((s: any) => s.image_status === 'complete');
      const allImagesComplete = projSlides.length > 0 && projSlides.every((s: any) => s.image_status === 'complete');
      
      if (allImagesComplete) {
        setCurrentStep(3); // Export
      } else if (hasImages) {
        setCurrentStep(2); // Images
      } else {
        setCurrentStep(2); // Images (script approved, ready to generate)
      }
    } else if (projSlides.length > 0) {
      setCurrentStep(1); // Has slides but not approved
    } else {
      setCurrentStep(0); // New project
    }
    setShowRecentProjects(false);
  };

  // Generate single image mutation
  const generateImageMutation = useMutation({
    mutationFn: ({ slideId, model, font, theme }: { slideId: string; model: string; font: string; theme: string }) =>
      generateSlideImage(slideId, { model, font, theme }),
    onSuccess: () => {
      refetchProject();
      setGeneratingSlideId(null);
    },
    onError: () => {
      setGeneratingSlideId(null);
    },
  });

  // Generate all images mutation
  const generateAllImagesMutation = useMutation({
    mutationFn: ({ projectId, model, font, theme }: { projectId: string; model: string; font: string; theme: string }) =>
      generateBatchImages(projectId, { model, font, theme }),
    onSuccess: () => {
      const interval = setInterval(() => {
        refetchProject();
      }, 2000);
      setTimeout(() => clearInterval(interval), 60000);
    },
  });

  // Update slide mutation (for future use)
  const _updateSlideMutation = useMutation({
    mutationFn: ({ slideId, data }: { slideId: string; data: Partial<Slide> }) =>
      updateSlide(slideId, data),
    onSuccess: () => refetchProject(),
  });
  void _updateSlideMutation; // suppress unused warning

  // Delete slide mutation (for future use)
  const _deleteSlideMutation = useMutation({
    mutationFn: deleteSlide,
    onSuccess: () => refetchProject(),
  });
  void _deleteSlideMutation; // suppress unused warning

  // Duplicate slide mutation (for future use)
  const _duplicateSlideMutation = useMutation({
    mutationFn: duplicateSlide,
    onSuccess: () => refetchProject(),
  });
  void _duplicateSlideMutation; // suppress unused warning

  // Regenerate single slide script mutation
  const regenerateSingleSlideMutation = useMutation({
    mutationFn: ({ projectId, slideIndex }: { projectId: string; slideIndex: number }) =>
      regenerateSlideScript(projectId, slideIndex),
    onSuccess: () => refetchProject(),
  });

  const handleGenerateScript = () => {
    if (!topic.trim()) return;
    generateScriptMutation.mutate({
      topic,
      content_type: selectedContentType,
      num_slides: numSlides,
    });
  };

  const handleGenerateImage = (slideId: string, options?: { theme?: string; font?: string }) => {
    setGeneratingSlideId(slideId);
    generateImageMutation.mutate({
      slideId,
      model: selectedModel,
      font: options?.font || selectedFont,
      theme: options?.theme || selectedTheme,
    });
  };

  const handleGenerateAllImages = () => {
    if (!projectId) return;
    generateAllImagesMutation.mutate({
      projectId,
      model: selectedModel,
      font: selectedFont,
      theme: selectedTheme,
    });
  };

  const slides = project?.slides || [];
  const completedSlides = slides.filter((s) => s.image_status === 'complete').length;
  const progress = slides.length > 0 ? (completedSlides / slides.length) * 100 : 0;

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
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(102, 126, 234, 0.35)',
            }}
            whileHover={{ scale: 1.05, rotate: 5 }}
          >
            <ImageIcon size={26} style={{ color: 'white' }} />
          </motion.div>
          <div>
            <h1 style={{ 
              fontSize: '28px', 
              fontWeight: 800, 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              Static Slideshow
            </h1>
            <p style={{ color: '#64748b', marginTop: '4px' }}>
              Create and iterate on slideshows until they're perfect
            </p>
          </div>
        </div>
        
        {/* Recent Projects Button */}
        <div style={{ position: 'relative' }}>
          <Button
            variant="secondary"
            onClick={() => setShowRecentProjects(!showRecentProjects)}
            icon={<History size={18} />}
          >
            Recent Projects
          </Button>
          
          {showRecentProjects && recentProjects.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '8px',
                width: '320px',
                background: 'white',
                borderRadius: '16px',
                boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
                border: '1px solid rgba(148, 163, 184, 0.2)',
                zIndex: 50,
                maxHeight: '400px',
                overflowY: 'auto',
              }}
            >
              <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(148, 163, 184, 0.15)' }}>
                <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>Recent Projects</p>
              </div>
              {recentProjects.slice(0, 10).map((proj: any) => (
                <motion.button
                  key={proj.id}
                  onClick={() => loadProject(proj)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '12px 16px',
                    background: proj.id === projectId ? 'rgba(102, 126, 234, 0.08)' : 'transparent',
                    border: 'none',
                    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                    cursor: 'pointer',
                  }}
                  whileHover={{ background: 'rgba(102, 126, 234, 0.05)' }}
                >
                  <p style={{ 
                    fontSize: '14px', 
                    fontWeight: 500, 
                    color: '#0f172a',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {proj.name || proj.topic}
                  </p>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      {proj.slide_count || proj.slides?.length || 0} slides
                    </span>
                    <span style={{ fontSize: '12px', color: '#94a3b8' }}>•</span>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      {proj.slides?.filter((s: Slide) => s.image_status === 'complete').length || 0} images
                    </span>
                  </div>
                </motion.button>
              ))}
            </motion.div>
          )}
        </div>
      </div>

      {/* Step Indicator */}
      <GlassCard padding="lg">
        <StepIndicator
          steps={STEPS}
          currentStep={currentStep}
          onStepClick={(step) => step <= currentStep && setCurrentStep(step)}
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
                      marginBottom: '12px' 
                    }}>
                      What's your topic?
                    </label>
                    <textarea
                      className="textarea"
                      style={{ fontSize: '16px', minHeight: '100px' }}
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="e.g., 5 Stoic Philosophers Who Changed Everything..."
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <label className="label">Number of Slides</label>
                      <select
                        className="select"
                        value={numSlides}
                        onChange={(e) => setNumSlides(Number(e.target.value))}
                      >
                        <option value={5}>5 slides</option>
                        <option value={7}>7 slides</option>
                        <option value={10}>10 slides</option>
                      </select>
                    </div>
                    <div>
                      <label className="label">Script Style</label>
                      <select
                        className="select"
                        value={selectedContentType}
                        onChange={(e) => setSelectedContentType(e.target.value)}
                      >
                        <option value="auto">Auto-detect</option>
                        {scriptStyles.map((style: any) => (
                          <option key={style.id} value={style.id}>
                            {style.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Script style description */}
                  {selectedContentType !== 'auto' && scriptStyles.find((s: any) => s.id === selectedContentType) && (
                    <div style={{ 
                      padding: '12px 16px',
                      background: 'rgba(102, 126, 234, 0.05)',
                      borderRadius: '12px',
                      border: '1px solid rgba(102, 126, 234, 0.1)',
                    }}>
                      <p style={{ fontSize: '13px', color: '#64748b' }}>
                        {scriptStyles.find((s: any) => s.id === selectedContentType)?.description}
                      </p>
                      <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '6px', fontStyle: 'italic' }}>
                        Example: "{scriptStyles.find((s: any) => s.id === selectedContentType)?.example}"
                      </p>
                    </div>
                  )}

                  <Button
                    variant="primary"
                    size="lg"
                    fullWidth
                    onClick={handleGenerateScript}
                    loading={generateScriptMutation.isPending}
                    icon={<Wand2 size={20} />}
                  >
                    Generate Script
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
                  Suggested Topics
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                  {SUGGESTED_TOPICS.map((suggestion) => (
                    <motion.button
                      key={suggestion}
                      onClick={() => setTopic(suggestion)}
                      style={{
                        padding: '10px 16px',
                        fontSize: '14px',
                        background: 'rgba(255, 255, 255, 0.8)',
                        border: '1px solid rgba(148, 163, 184, 0.3)',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        color: '#334155',
                      }}
                      whileHover={{ 
                        borderColor: '#667eea', 
                        background: 'rgba(102, 126, 234, 0.08)',
                        color: '#667eea',
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
              <GlassCard padding="lg">
                <h3 style={{ 
                  fontWeight: 600, 
                  marginBottom: '20px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px',
                  color: '#0f172a',
                }}>
                  <Settings size={20} style={{ color: '#667eea' }} />
                  Generation Settings
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label className="label">Image Model</label>
                    <select
                      className="select"
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                    >
                      {modelsData?.image_models?.map((model: any) => (
                        <option key={model.id} value={model.id}>
                          {model.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">Font Style</label>
                    <select
                      className="select"
                      value={selectedFont}
                      onChange={(e) => setSelectedFont(e.target.value)}
                    >
                      {modelsData?.fonts?.map((font: any) => (
                        <option key={font.id} value={font.id}>
                          {font.name} - {font.style}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </GlassCard>

              {/* Theme preview */}
              <GlassCard gradient="purple" padding="lg">
                <h3 style={{ fontWeight: 600, marginBottom: '12px', color: '#0f172a' }}>Selected Theme</h3>
                <div style={{ 
                  padding: '14px', 
                  background: 'white', 
                  borderRadius: '12px',
                  border: '1px solid rgba(102, 126, 234, 0.2)',
                }}>
                  <p style={{ 
                    fontWeight: 600, 
                    color: '#667eea',
                    fontSize: '15px',
                  }}>
                    {THEME_OPTIONS.find((t) => t.id === selectedTheme)?.name}
                  </p>
                  <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                    {THEME_OPTIONS.find((t) => t.id === selectedTheme)?.description}
                  </p>
                </div>
              </GlassCard>
            </div>
          </motion.div>
        )}

        {/* Step 1: Script Review */}
        {currentStep === 1 && project && (
          <motion.div
            key="review"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <ScriptReview
              project={project}
              onApprove={() => {
                if (projectId) {
                  approveScriptMutation.mutate(projectId);
                }
              }}
              onRegenerateAll={(newStyle) => {
                if (projectId) {
                  regenerateEntireScriptMutation.mutate({ projectId, style: newStyle });
                }
              }}
              onRegenerateSlide={(slideIndex) => {
                if (projectId) {
                  regenerateSingleSlideMutation.mutate({
                    projectId,
                    slideIndex,
                  });
                }
              }}
              onUpdateSlide={(slideId, data) => {
                if (projectId) {
                  updateSlideScriptMutation.mutate({ projectId, slideId, data });
                }
              }}
              scriptStyles={scriptStyles}
              isRegenerating={regenerateEntireScriptMutation.isPending || regenerateSingleSlideMutation.isPending}
              isApproving={approveScriptMutation.isPending}
            />
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
            {/* Progress header */}
            <GlassCard padding="lg">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a' }}>Generate Images</h2>
                  <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>
                    {completedSlides} of {slides.length} slides complete
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <Button
                    variant="secondary"
                    onClick={() => setCurrentStep(1)}
                    icon={<ChevronLeft size={18} />}
                  >
                    Back to Script
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleGenerateAllImages}
                    loading={generateAllImagesMutation.isPending}
                    icon={<Sparkles size={18} />}
                  >
                    Generate All Images
                  </Button>
                </div>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </GlassCard>

            {/* Settings */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              <GlassCard padding="md">
                <label className="label">Image Model</label>
                <select
                  className="select"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  {modelsData?.image_models?.map((model: any) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </GlassCard>
              <GlassCard padding="md">
                <label className="label">Font Style</label>
                <select
                  className="select"
                  value={selectedFont}
                  onChange={(e) => setSelectedFont(e.target.value)}
                >
                  {modelsData?.fonts?.map((font: any) => (
                    <option key={font.id} value={font.id}>
                      {font.name}
                    </option>
                  ))}
                </select>
              </GlassCard>
              <GlassCard padding="md">
                <label className="label">Theme</label>
                <select
                  className="select"
                  value={selectedTheme}
                  onChange={(e) => setSelectedTheme(e.target.value)}
                >
                  {THEME_OPTIONS.map((theme) => (
                    <option key={theme.id} value={theme.id}>
                      {theme.name}
                    </option>
                  ))}
                </select>
              </GlassCard>
            </div>

            {/* Slide grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
              {slides.map((slide, index) => (
                <GlassCard key={slide.id} hover padding="none" className="overflow-hidden">
                  <div style={{ aspectRatio: '9/16', position: 'relative', background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)' }}>
                    {slide.final_image_path ? (
                      <img
                        src={getSlideImageUrl(slide.final_image_path) || ''}
                        alt={slide.title || 'Slide'}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : slide.image_status === 'generating' || generatingSlideId === slide.id ? (
                      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <RefreshCw size={24} style={{ color: '#667eea' }} className="animate-spin" />
                      </div>
                    ) : (
                      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <ImageIcon size={24} style={{ color: '#94a3b8' }} />
                      </div>
                    )}
                    
                    {/* Status badge */}
                    <div style={{ position: 'absolute', top: '8px', left: '8px' }}>
                      <span style={{
                        display: 'inline-flex',
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 600,
                        borderRadius: '16px',
                        background: slide.image_status === 'complete' 
                          ? 'rgba(34, 197, 94, 0.9)' 
                          : slide.image_status === 'generating'
                            ? 'rgba(102, 126, 234, 0.9)'
                            : slide.image_status === 'error'
                              ? 'rgba(239, 68, 68, 0.9)'
                              : 'rgba(255, 255, 255, 0.9)',
                        color: slide.image_status === 'complete' || slide.image_status === 'generating' || slide.image_status === 'error' 
                          ? 'white' 
                          : '#64748b',
                        backdropFilter: 'blur(4px)',
                      }}>
                        {index === 0 ? 'Hook' : index === slides.length - 1 ? 'Outro' : `#${index}`}
                      </span>
                    </div>
                  </div>
                  
                  <div style={{ padding: '12px' }}>
                    <p style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a' }} className="truncate">
                      {slide.title || 'Untitled'}
                    </p>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                      <Button
                        variant="secondary"
                        size="sm"
                        fullWidth
                        onClick={() => handleGenerateImage(slide.id)}
                        loading={generatingSlideId === slide.id}
                        icon={<RefreshCw size={12} />}
                      >
                        {slide.image_status === 'complete' ? 'Regen' : 'Generate'}
                      </Button>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>

            {/* Continue button */}
            {progress === 100 && (
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="primary"
                  size="lg"
                  onClick={() => setCurrentStep(3)}
                  icon={<ChevronRight size={20} />}
                  iconPosition="right"
                >
                  Continue to Export
                </Button>
              </div>
            )}
          </motion.div>
        )}

        {/* Step 3: Export */}
        {currentStep === 3 && project && (
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
                    width: '80px',
                    height: '80px',
                    borderRadius: '24px',
                    background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 24px',
                  }}
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Check size={40} style={{ color: '#22c55e' }} />
                </motion.div>
                <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                  Slideshow Complete!
                </h2>
                <p style={{ color: '#64748b', marginBottom: '32px' }}>
                  All {slides.length} slides have been generated successfully.
                </p>
                
                <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
                  <Button
                    variant="secondary"
                    size="lg"
                    icon={<Download size={20} />}
                  >
                    Download All Images
                  </Button>
                  <Button
                    variant="primary"
                    size="lg"
                    icon={<Play size={20} />}
                  >
                    Preview Slideshow
                  </Button>
                </div>
              </div>
            </GlassCard>

            {/* Preview grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '8px' }}>
              {slides.map((slide) => (
                <motion.div 
                  key={slide.id} 
                  style={{ 
                    aspectRatio: '9/16', 
                    borderRadius: '12px', 
                    overflow: 'hidden', 
                    background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                  }}
                  whileHover={{ scale: 1.05, zIndex: 10 }}
                >
                  {slide.final_image_path && (
                    <img
                      src={getSlideImageUrl(slide.final_image_path) || ''}
                      alt={slide.title || 'Slide'}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
