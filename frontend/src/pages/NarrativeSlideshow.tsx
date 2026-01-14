import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, 
  Wand2, 
  Play,
  Volume2,
  ChevronLeft,
  ChevronRight,
  Settings,
  Download,
  Video,
  Clock
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
  { id: 'topic', label: 'Topic', description: 'Enter your story' },
  { id: 'script', label: 'Script', description: 'Narrative & voice' },
  { id: 'visuals', label: 'Visuals', description: 'Generate images' },
  { id: 'audio', label: 'Audio', description: 'Generate voiceover' },
  { id: 'export', label: 'Export', description: 'Create video' },
];

const VOICE_OPTIONS = [
  { id: 'adam', name: 'Adam', description: 'Deep, authoritative male voice', preview: true },
  { id: 'rachel', name: 'Rachel', description: 'Calm, soothing female voice', preview: true },
  { id: 'josh', name: 'Josh', description: 'Friendly, conversational male', preview: true },
  { id: 'bella', name: 'Bella', description: 'Warm, engaging female voice', preview: true },
  { id: 'antoni', name: 'Antoni', description: 'Narrative, dramatic male', preview: true },
  { id: 'arnold', name: 'Arnold', description: 'Rich, mature male voice', preview: true },
];

const SUGGESTED_STORIES = [
  'The Day Socrates Chose Death Over Silence',
  'How Marcus Aurelius Found Peace in Chaos',
  'The Slave Who Became a Philosopher: Epictetus',
  'Diogenes and the Search for an Honest Man',
  'The Last Days of Seneca',
];

export default function NarrativeSlideshow() {
  const [currentStep, setCurrentStep] = useState(0);
  const [topic, setTopic] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [selectedVoice, setSelectedVoice] = useState('adam');
  const [selectedTheme, setSelectedTheme] = useState('oil_contrast');
  const [selectedModel] = useState('gpt15');
  const [selectedFont, setSelectedFont] = useState('cinzel');

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
      num_slides: 10,
    });
  };

  const slides = project?.slides || [];
  const completedSlides = slides.filter((s) => s.image_status === 'complete').length;
  const totalNarrationWords = slides.reduce((acc, s) => acc + (s.narration?.split(' ').length || 0), 0);
  const estimatedDuration = Math.ceil(totalNarrationWords / 2.5);

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
              background: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(168, 85, 247, 0.35)',
            }}
            whileHover={{ scale: 1.05, rotate: 5 }}
          >
            <Mic size={26} style={{ color: 'white' }} />
          </motion.div>
          <div>
            <h1 style={{ 
              fontSize: '28px', 
              fontWeight: 800, 
              background: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              Narrative Slideshow
            </h1>
            <p style={{ color: '#64748b', marginTop: '4px' }}>
              Create story-driven slideshows with AI voiceover
            </p>
          </div>
        </div>
      </div>

      {/* Step Indicator */}
      <GlassCard padding="lg">
        <StepIndicator
          steps={STEPS}
          currentStep={currentStep}
          onStepClick={(step) => step <= currentStep && setCurrentStep(step)}
          variant="purple"
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
                      Tell a Story
                    </label>
                    <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '12px' }}>
                      Describe the philosophical story or concept you want to narrate
                    </p>
                    <textarea
                      className="textarea"
                      style={{ fontSize: '16px', minHeight: '120px' }}
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="e.g., The story of how Socrates faced his death with calm acceptance, teaching his students one final lesson about the nature of the soul..."
                    />
                  </div>

                  <Button
                    variant="gradient-purple"
                    size="lg"
                    fullWidth
                    onClick={handleGenerateScript}
                    loading={generateScriptMutation.isPending}
                    icon={<Wand2 size={20} />}
                  >
                    Generate Narrative Script
                  </Button>
                </div>
              </GlassCard>

              {/* Suggested stories */}
              <div>
                <h3 style={{ 
                  fontSize: '14px', 
                  fontWeight: 600, 
                  color: '#64748b', 
                  marginBottom: '12px' 
                }}>
                  Story Ideas
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {SUGGESTED_STORIES.map((story) => (
                    <motion.button
                      key={story}
                      onClick={() => setTopic(story)}
                      style={{
                        width: '100%',
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
                        borderColor: '#a855f7', 
                        background: 'rgba(168, 85, 247, 0.08)',
                        color: '#a855f7',
                      }}
                    >
                      {story}
                    </motion.button>
                  ))}
                </div>
              </div>
            </div>

            {/* Voice selection sidebar */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <GlassCard padding="lg">
                <h3 style={{ 
                  fontWeight: 600, 
                  marginBottom: '16px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px',
                  color: '#0f172a',
                }}>
                  <Volume2 size={20} style={{ color: '#a855f7' }} />
                  Voice Selection
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {VOICE_OPTIONS.map((voice) => (
                    <motion.button
                      key={voice.id}
                      onClick={() => setSelectedVoice(voice.id)}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        padding: '12px 14px',
                        borderRadius: '12px',
                        border: selectedVoice === voice.id 
                          ? '2px solid #a855f7' 
                          : '1px solid rgba(148, 163, 184, 0.3)',
                        background: selectedVoice === voice.id 
                          ? 'rgba(168, 85, 247, 0.1)' 
                          : 'white',
                        cursor: 'pointer',
                      }}
                      whileHover={{ borderColor: '#a855f7' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div>
                          <p style={{ 
                            fontWeight: 600, 
                            color: selectedVoice === voice.id ? '#a855f7' : '#0f172a',
                            fontSize: '14px',
                          }}>
                            {voice.name}
                          </p>
                          <p style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                            {voice.description}
                          </p>
                        </div>
                        {voice.preview && (
                          <motion.button
                            onClick={(e) => {
                              e.stopPropagation();
                            }}
                            style={{
                              padding: '8px',
                              borderRadius: '50%',
                              background: 'rgba(168, 85, 247, 0.1)',
                              border: 'none',
                              cursor: 'pointer',
                            }}
                            whileHover={{ background: 'rgba(168, 85, 247, 0.2)' }}
                          >
                            <Play size={12} style={{ color: '#a855f7' }} />
                          </motion.button>
                        )}
                      </div>
                    </motion.button>
                  ))}
                </div>
              </GlassCard>

              <GlassCard gradient="pink" padding="lg">
                <h3 style={{ 
                  fontWeight: 600, 
                  marginBottom: '16px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px',
                  color: '#0f172a',
                }}>
                  <Settings size={18} />
                  Visual Settings
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <label className="label">Theme</label>
                    <select
                      className="select"
                      value={selectedTheme}
                      onChange={(e) => setSelectedTheme(e.target.value)}
                    >
                      <option value="oil_contrast">Oil Contrast - Renaissance</option>
                      <option value="scene_portrait">Scene Portrait - Cinematic</option>
                      <option value="golden_dust">Golden Dust - Elegant</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Font</label>
                    <select
                      className="select"
                      value={selectedFont}
                      onChange={(e) => setSelectedFont(e.target.value)}
                    >
                      <option value="cinzel">Cinzel - Classical</option>
                      <option value="cormorant">Cormorant - Literary</option>
                      <option value="montserrat">Montserrat - Modern</option>
                    </select>
                  </div>
                </div>
              </GlassCard>
            </div>
          </motion.div>
        )}

        {/* Step 1: Script Review with Narration */}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '8px', fontSize: '14px', color: '#64748b' }}>
                  <span>{slides.length} scenes</span>
                  <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#94a3b8' }} />
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock size={14} />
                    ~{estimatedDuration}s estimated
                  </span>
                  <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#94a3b8' }} />
                  <span>{totalNarrationWords} words</span>
                </div>
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
                  variant="gradient-purple"
                  onClick={() => setCurrentStep(2)}
                  icon={<ChevronRight size={18} />}
                  iconPosition="right"
                >
                  Generate Visuals
                </Button>
              </div>
            </div>

            {/* Script timeline */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {slides.map((slide, index) => (
                <GlassCard key={slide.id} padding="lg">
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                    {/* Scene number */}
                    <motion.div 
                      style={{
                        flexShrink: 0,
                        width: '48px',
                        height: '48px',
                        borderRadius: '14px',
                        background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                      whileHover={{ scale: 1.05 }}
                    >
                      <span style={{ fontSize: '18px', fontWeight: 700, color: '#a855f7' }}>
                        {index + 1}
                      </span>
                    </motion.div>
                    
                    {/* Content */}
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <h3 style={{ fontWeight: 600, color: '#0f172a' }}>{slide.title || `Scene ${index + 1}`}</h3>
                        <span style={{ fontSize: '12px', color: '#64748b' }}>
                          {slide.narration?.split(' ').length || 0} words
                        </span>
                      </div>
                      
                      {/* Visual description */}
                      <div style={{ padding: '12px 14px', background: 'rgba(248, 250, 252, 0.8)', borderRadius: '10px' }}>
                        <p style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Visual</p>
                        <p style={{ fontSize: '14px', color: '#475569' }}>{slide.visual_description || 'No visual description'}</p>
                      </div>
                      
                      {/* Narration */}
                      <div style={{ 
                        padding: '12px 14px', 
                        background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.08) 0%, rgba(236, 72, 153, 0.08) 100%)', 
                        borderRadius: '10px',
                        border: '1px solid rgba(168, 85, 247, 0.2)',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <p style={{ fontSize: '11px', color: '#a855f7', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Narration</p>
                          <motion.button 
                            style={{ 
                              padding: '4px', 
                              borderRadius: '50%', 
                              background: 'transparent', 
                              border: 'none', 
                              cursor: 'pointer' 
                            }}
                            whileHover={{ background: 'rgba(168, 85, 247, 0.1)' }}
                          >
                            <Play size={12} style={{ color: '#a855f7' }} />
                          </motion.button>
                        </div>
                        <p style={{ fontSize: '14px', fontStyle: 'italic', color: '#475569', lineHeight: 1.6 }}>
                          "{slide.narration || 'No narration'}"
                        </p>
                      </div>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>
          </motion.div>
        )}

        {/* Step 2: Visual Generation */}
        {currentStep === 2 && project && (
          <motion.div
            key="visuals"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
          >
            <GlassCard padding="lg">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a' }}>Generating Visuals</h2>
                  <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>
                    {completedSlides} of {slides.length} scenes rendered
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
                    variant="gradient-purple"
                    onClick={() => {
                      generateImagesMutation.mutate({
                        projectId: project.id,
                        model: selectedModel,
                        font: selectedFont,
                      });
                    }}
                    loading={generateImagesMutation.isPending}
                  >
                    Generate All
                  </Button>
                </div>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-bar-fill"
                  style={{ 
                    width: `${(completedSlides / slides.length) * 100}%`,
                    background: 'linear-gradient(90deg, #a855f7, #ec4899)'
                  }}
                />
              </div>
            </GlassCard>

            {/* Scene grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px' }}>
              {slides.map((slide, index) => (
                <GlassCard key={slide.id} padding="none" className="overflow-hidden">
                  <div style={{ aspectRatio: '9/16', position: 'relative', background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)' }}>
                    {slide.final_image_path ? (
                      <img
                        src={getSlideImageUrl(slide.final_image_path) || ''}
                        alt={slide.title || 'Scene'}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <motion.div
                          style={{
                            width: '32px',
                            height: '32px',
                            border: '3px solid transparent',
                            borderTopColor: '#a855f7',
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
                      background: 'rgba(168, 85, 247, 0.9)',
                      backdropFilter: 'blur(4px)',
                    }}>
                      <span style={{ fontSize: '11px', fontWeight: 600, color: 'white' }}>Scene {index + 1}</span>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>

            {completedSlides === slides.length && (
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="gradient-purple"
                  size="lg"
                  onClick={() => setCurrentStep(3)}
                  icon={<ChevronRight size={20} />}
                  iconPosition="right"
                >
                  Generate Voiceover
                </Button>
              </div>
            )}
          </motion.div>
        )}

        {/* Step 3: Audio Generation */}
        {currentStep === 3 && project && (
          <motion.div
            key="audio"
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
                    background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 24px',
                  }}
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Mic size={40} style={{ color: '#a855f7' }} />
                </motion.div>
                <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                  Generate Voiceover
                </h2>
                <p style={{ color: '#64748b', marginBottom: '8px' }}>
                  Using ElevenLabs with voice: <strong style={{ color: '#a855f7' }}>{selectedVoice}</strong>
                </p>
                <p style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '32px' }}>
                  Estimated duration: ~{estimatedDuration} seconds
                </p>
                
                <Button
                  variant="gradient-purple"
                  size="lg"
                  icon={<Volume2 size={20} />}
                  onClick={() => {
                    setCurrentStep(4);
                  }}
                >
                  Generate Voiceover
                </Button>
              </div>
            </GlassCard>

            {/* Script preview */}
            <GlassCard padding="lg">
              <h3 style={{ fontWeight: 600, marginBottom: '16px', color: '#0f172a' }}>Full Narration Script</h3>
              <div style={{ 
                padding: '20px', 
                background: 'rgba(248, 250, 252, 0.8)', 
                borderRadius: '12px', 
                maxHeight: '256px', 
                overflowY: 'auto' 
              }}>
                {slides.map((slide, index) => (
                  <p key={slide.id} style={{ marginBottom: '16px', fontSize: '14px', lineHeight: 1.7 }}>
                    <span style={{ color: '#a855f7', fontWeight: 600 }}>[Scene {index + 1}]</span>{' '}
                    <span style={{ color: '#475569' }}>{slide.narration}</span>
                  </p>
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
                    width: '80px',
                    height: '80px',
                    borderRadius: '24px',
                    background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 24px',
                  }}
                  animate={{ rotate: [0, 5, -5, 0] }}
                  transition={{ duration: 4, repeat: Infinity }}
                >
                  <Video size={40} style={{ color: '#a855f7' }} />
                </motion.div>
                <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                  Create Video
                </h2>
                <p style={{ color: '#64748b', marginBottom: '32px' }}>
                  Combine your {slides.length} scenes with voiceover into a video
                </p>
                
                <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
                  <Button
                    variant="secondary"
                    size="lg"
                    icon={<Download size={20} />}
                  >
                    Download Audio
                  </Button>
                  <Button
                    variant="gradient-purple"
                    size="lg"
                    icon={<Video size={20} />}
                  >
                    Export Video
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
