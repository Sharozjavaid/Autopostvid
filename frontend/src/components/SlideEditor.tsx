import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  RefreshCw, 
  Trash2, 
  Copy, 
  Image as ImageIcon,
  Loader2,
  AlertCircle,
  ChevronUp,
  ChevronDown,
  Sparkles,
  Check,
  Palette,
  Type,
  History,
  ChevronRight,
  X
} from 'lucide-react';
import type { Slide, SlideVersion } from '../api/client';
import { reapplyTextOverlay, getSlideVersions, revertToVersion, getSlideImageUrl } from '../api/client';
import GlassCard from './GlassCard';
import Button from './Button';

const THEME_OPTIONS = [
  { id: 'glitch_titans', name: 'Glitch Titans', description: 'Cracked glass, digital effects' },
  { id: 'oil_contrast', name: 'Oil Contrast', description: 'Renaissance oil painting' },
  { id: 'golden_dust', name: 'Golden Dust', description: 'Elegant sepia with gold' },
  { id: 'scene_portrait', name: 'Scene Portrait', description: 'Cinematic philosopher scenes' },
];

const FONT_OPTIONS = [
  { id: 'social', name: 'Social', style: 'Clean, Modern' },
  { id: 'bebas', name: 'Bebas Neue', style: 'Bold, Impact' },
  { id: 'montserrat', name: 'Montserrat', style: 'Modern, Clean' },
  { id: 'cinzel', name: 'Cinzel', style: 'Classical, Roman' },
  { id: 'oswald', name: 'Oswald', style: 'Condensed, Strong' },
  { id: 'cormorant', name: 'Cormorant', style: 'Elegant, Serif' },
];

interface PreviousVersion {
  imagePath: string;
  theme: string;
  font: string;
  subtitle: string;
  timestamp: number;
}

interface SlideEditorProps {
  slide: Slide;
  index: number;
  totalSlides: number;
  onUpdate: (slideId: string, data: Partial<Slide>) => void;
  onRegenerate: (slideId: string) => void;
  onGenerateImage: (slideId: string, options?: { theme?: string; font?: string }) => void;
  onDelete: (slideId: string) => void;
  onDuplicate: (slideId: string) => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  isGenerating?: boolean;
  defaultTheme?: string;
  defaultFont?: string;
  onRefetch?: () => void; // Callback to refetch project data after changes
}

export default function SlideEditor({
  slide,
  index,
  totalSlides,
  onUpdate,
  onRegenerate,
  onGenerateImage,
  onDelete,
  onDuplicate,
  onMoveUp,
  onMoveDown,
  isGenerating = false,
  defaultTheme = 'golden_dust',
  defaultFont = 'montserrat',
  onRefetch,
}: SlideEditorProps) {
  // Local state for this slide's settings
  const [selectedTheme, setSelectedTheme] = useState(defaultTheme);
  const [selectedFont, setSelectedFont] = useState(defaultFont);
  const [showSettings, setShowSettings] = useState(false);
  
  // Previous version tracking
  const [previousVersion, setPreviousVersion] = useState<PreviousVersion | null>(null);
  const [showPreviousVersion, setShowPreviousVersion] = useState(false);
  const [expandedPrevious, setExpandedPrevious] = useState(false);
  
  // Track what settings were used for current image
  const [currentImageSettings, setCurrentImageSettings] = useState<{theme: string; font: string; subtitle: string} | null>(null);
  
  // Cache buster to force image reload after reapply
  const [imageCacheBuster, setImageCacheBuster] = useState<number>(Date.now());
  
  // Version history
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [versions, setVersions] = useState<SlideVersion[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [revertingVersion, setRevertingVersion] = useState<number | null>(null);
  
  // Editable fields - always in edit mode now
  const [editData, setEditData] = useState({
    title: slide.title || '',
    subtitle: slide.subtitle || '',
    visual_description: slide.visual_description || '',
    narration: slide.narration || '',
  });
  
  // Track if there are unsaved changes
  const [hasChanges, setHasChanges] = useState(false);
  
  // Debounce timer ref for auto-save
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Sync with slide prop changes
  useEffect(() => {
    setEditData({
      title: slide.title || '',
      subtitle: slide.subtitle || '',
      visual_description: slide.visual_description || '',
      narration: slide.narration || '',
    });
    setHasChanges(false);
  }, [slide.title, slide.subtitle, slide.visual_description, slide.narration]);
  
  // When image completes, store the settings that were used
  useEffect(() => {
    if (slide.image_status === 'complete' && slide.final_image_path) {
      setCurrentImageSettings({
        theme: selectedTheme,
        font: selectedFont,
        subtitle: slide.subtitle || '',
      });
    }
  }, [slide.image_status, slide.final_image_path]);

  const handleFieldChange = (field: string, value: string) => {
    setEditData(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
    
    // Auto-save after 1 second of no typing
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }
    autoSaveTimerRef.current = setTimeout(() => {
      onUpdate(slide.id, { ...editData, [field]: value });
    }, 1000);
  };

  const handleSave = () => {
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }
    onUpdate(slide.id, editData);
    setHasChanges(false);
  };
  
  // Save previous version before regenerating
  const savePreviousVersion = useCallback(() => {
    if (slide.final_image_path && currentImageSettings) {
      setPreviousVersion({
        imagePath: slide.final_image_path,
        theme: currentImageSettings.theme,
        font: currentImageSettings.font,
        subtitle: currentImageSettings.subtitle,
        timestamp: Date.now(),
      });
      setShowPreviousVersion(true);
    }
  }, [slide.final_image_path, currentImageSettings]);

  const handleGenerateWithOptions = () => {
    // Save current as previous version before regenerating
    savePreviousVersion();
    
    // Save any pending changes first
    if (hasChanges) {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
      onUpdate(slide.id, editData);
      setHasChanges(false);
    }
    onGenerateImage(slide.id, { theme: selectedTheme, font: selectedFont });
  };
  
  // Track if we're reapplying text
  const [isReapplyingText, setIsReapplyingText] = useState(false);

  // Theme change requires regenerating the background (full generation)
  const handleThemeChange = (newTheme: string) => {
    setSelectedTheme(newTheme);
    if (slide.final_image_path && slide.image_status === 'complete') {
      // Save current as previous
      savePreviousVersion();
      // Trigger full regeneration with new theme (background needs to change)
      setTimeout(() => {
        onGenerateImage(slide.id, { theme: newTheme, font: selectedFont });
      }, 100);
    }
  };
  
  // Font change only reapplies text overlay (fast, no AI generation needed)
  const handleFontChange = async (newFont: string) => {
    const oldFont = selectedFont;
    setSelectedFont(newFont);
    
    // Only reapply if we have an existing image (check both background and final paths)
    const hasExistingImage = slide.background_image_path || slide.final_image_path;
    console.log('[SlideEditor] Font change:', { 
      newFont, 
      hasExistingImage, 
      background: slide.background_image_path, 
      final: slide.final_image_path,
      slideId: slide.id 
    });
    
    if (hasExistingImage) {
      // Save current as previous
      savePreviousVersion();
      
      setIsReapplyingText(true);
      try {
        console.log('[SlideEditor] Calling reapplyTextOverlay...');
        const result = await reapplyTextOverlay(slide.id, newFont);
        console.log('[SlideEditor] Reapply result:', result);
        // Update cache buster to force image reload
        setImageCacheBuster(Date.now());
        // Also trigger refetch to get updated slide data
        if (onRefetch) {
          onRefetch();
        }
      } catch (error: any) {
        console.error('[SlideEditor] Failed to reapply text:', error);
        console.error('[SlideEditor] Error details:', error?.response?.data || error?.message);
        // Revert font selection on error
        setSelectedFont(oldFont);
        // Show error to user
        alert(`Failed to apply font: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`);
      } finally {
        setIsReapplyingText(false);
      }
    }
  };

  // Load version history
  const loadVersionHistory = async () => {
    setLoadingVersions(true);
    try {
      const data = await getSlideVersions(slide.id);
      setVersions(data.versions);
      setShowVersionHistory(true);
    } catch (error) {
      console.error('Failed to load versions:', error);
    } finally {
      setLoadingVersions(false);
    }
  };
  
  // Revert to a specific version
  const handleRevertToVersion = async (versionNumber: number) => {
    setRevertingVersion(versionNumber);
    try {
      await revertToVersion(slide.id, versionNumber);
      setImageCacheBuster(Date.now());
      if (onRefetch) {
        onRefetch();
      }
      // Reload versions to show the new revert entry
      await loadVersionHistory();
    } catch (error: any) {
      console.error('Failed to revert:', error);
      alert(`Failed to revert: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`);
    } finally {
      setRevertingVersion(null);
    }
  };

  const getSlideType = () => {
    if (index === 0) return 'Hook';
    if (index === totalSlides - 1) return 'Outro';
    return `Slide ${index}`;
  };

  const getStatusBadge = () => {
    switch (slide.image_status) {
      case 'complete':
        return (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '6px 12px',
            fontSize: '12px',
            fontWeight: 600,
            borderRadius: '20px',
            background: 'rgba(34, 197, 94, 0.1)',
            color: '#16a34a',
          }}>
            <Check size={12} /> Complete
          </span>
        );
      case 'generating':
        return (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '6px 12px',
            fontSize: '12px',
            fontWeight: 600,
            borderRadius: '20px',
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
            color: '#667eea',
          }}>
            <Loader2 size={12} className="animate-spin" /> Generating
          </span>
        );
      case 'error':
        return (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '6px 12px',
            fontSize: '12px',
            fontWeight: 600,
            borderRadius: '20px',
            background: 'rgba(239, 68, 68, 0.1)',
            color: '#dc2626',
          }}>
            <AlertCircle size={12} /> Error
          </span>
        );
      default:
        return (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '6px 12px',
            fontSize: '12px',
            fontWeight: 600,
            borderRadius: '20px',
            background: 'rgba(148, 163, 184, 0.1)',
            color: '#64748b',
          }}>
            Pending
          </span>
        );
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <GlassCard padding="none" className="overflow-hidden">
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid rgba(148, 163, 184, 0.15)',
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <motion.div 
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
              }}
              whileHover={{ scale: 1.05 }}
            >
              <span style={{ fontSize: '14px', fontWeight: 700, color: 'white' }}>
                {index + 1}
              </span>
            </motion.div>
            <div>
              <h3 style={{ fontWeight: 600, color: '#0f172a', fontSize: '16px' }}>{getSlideType()}</h3>
              <p style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
                {editData.title || 'No title'}
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {hasChanges && (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleSave}
                  icon={<Check size={14} />}
                >
                  Save
                </Button>
                {slide.final_image_path && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleGenerateWithOptions}
                    loading={isGenerating}
                    icon={<RefreshCw size={14} />}
                  >
                    Save & Regenerate
                  </Button>
                )}
              </>
            )}
            {getStatusBadge()}
            {/* Version history button */}
            {slide.current_version > 0 && (
              <motion.button
                onClick={loadVersionHistory}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '6px 10px',
                  fontSize: '12px',
                  fontWeight: 500,
                  color: '#64748b',
                  background: 'transparent',
                  border: '1px solid rgba(148, 163, 184, 0.3)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  marginLeft: '8px',
                }}
                whileHover={{ borderColor: '#667eea', color: '#667eea' }}
              >
                <History size={14} />
                v{slide.current_version}
              </motion.button>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '8px' }}>
              {onMoveUp && index > 0 && (
                <motion.button
                  onClick={onMoveUp}
                  style={{
                    padding: '8px',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'transparent',
                    color: '#64748b',
                    cursor: 'pointer',
                  }}
                  whileHover={{ background: 'rgba(102, 126, 234, 0.1)', color: '#667eea' }}
                >
                  <ChevronUp size={18} />
                </motion.button>
              )}
              {onMoveDown && index < totalSlides - 1 && (
                <motion.button
                  onClick={onMoveDown}
                  style={{
                    padding: '8px',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'transparent',
                    color: '#64748b',
                    cursor: 'pointer',
                  }}
                  whileHover={{ background: 'rgba(102, 126, 234, 0.1)', color: '#667eea' }}
                >
                  <ChevronDown size={18} />
                </motion.button>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div style={{ 
          padding: '20px', 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr', 
          gap: '24px',
        }}>
          {/* Text content - Always editable */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '12px', 
                fontWeight: 600, 
                color: '#64748b', 
                marginBottom: '8px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>Title</label>
              <input
                type="text"
                className="input"
                value={editData.title}
                onChange={(e) => handleFieldChange('title', e.target.value)}
                placeholder="Slide title..."
                style={{ fontSize: '15px' }}
              />
            </div>
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '12px', 
                fontWeight: 600, 
                color: '#64748b', 
                marginBottom: '8px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>Subtitle / Content</label>
              <textarea
                className="textarea"
                value={editData.subtitle}
                onChange={(e) => handleFieldChange('subtitle', e.target.value)}
                placeholder="Main content text that appears on the slide..."
                rows={3}
                style={{ fontSize: '14px' }}
              />
            </div>
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '12px', 
                fontWeight: 600, 
                color: '#64748b', 
                marginBottom: '8px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>Visual Description (Image Prompt)</label>
              <textarea
                className="textarea"
                value={editData.visual_description}
                onChange={(e) => handleFieldChange('visual_description', e.target.value)}
                placeholder="Describe the visual for AI image generation... e.g., 'A dramatic marble bust of Socrates with golden dust particles floating in warm amber light'"
                rows={4}
                style={{ 
                  fontSize: '14px',
                  background: 'rgba(102, 126, 234, 0.03)',
                  border: '1px solid rgba(102, 126, 234, 0.2)',
                }}
              />
              <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px' }}>
                This prompt is combined with the selected theme to generate the background image.
              </p>
            </div>
            {(index === totalSlides - 1 || slide.narration) && (
              <div>
                <label style={{ 
                  display: 'block', 
                  fontSize: '12px', 
                  fontWeight: 600, 
                  color: '#64748b', 
                  marginBottom: '8px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}>Narration (for video)</label>
                <textarea
                  className="textarea"
                  value={editData.narration}
                  onChange={(e) => handleFieldChange('narration', e.target.value)}
                  placeholder="Voice-over narration text..."
                  rows={2}
                  style={{ fontSize: '14px', fontStyle: 'italic' }}
                />
              </div>
            )}
          </div>

          {/* Image preview + settings */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <label style={{ 
                fontSize: '12px', 
                fontWeight: 600, 
                color: '#64748b',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>Generated Image</label>
              <motion.button
                onClick={() => setShowSettings(!showSettings)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  fontSize: '12px',
                  fontWeight: 500,
                  color: showSettings ? '#667eea' : '#64748b',
                  background: showSettings ? 'rgba(102, 126, 234, 0.1)' : 'transparent',
                  border: '1px solid',
                  borderColor: showSettings ? 'rgba(102, 126, 234, 0.3)' : 'rgba(148, 163, 184, 0.3)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                }}
                whileHover={{ borderColor: '#667eea', color: '#667eea' }}
              >
                <Palette size={14} />
                Theme & Font
              </motion.button>
            </div>

            {/* Per-slide settings panel */}
            <AnimatePresence>
              {showSettings && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  style={{
                    padding: '16px',
                    background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
                    borderRadius: '12px',
                    border: '1px solid rgba(102, 126, 234, 0.15)',
                  }}
                >
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ 
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '12px', 
                        fontWeight: 600, 
                        color: '#0f172a', 
                        marginBottom: '8px' 
                      }}>
                        <Palette size={14} style={{ color: '#667eea' }} />
                        Theme
                      </label>
                      <select
                        className="select"
                        value={selectedTheme}
                        onChange={(e) => handleThemeChange(e.target.value)}
                        style={{ fontSize: '13px' }}
                        disabled={isGenerating || slide.image_status === 'generating'}
                      >
                        {THEME_OPTIONS.map((theme) => (
                          <option key={theme.id} value={theme.id}>
                            {theme.name}
                          </option>
                        ))}
                      </select>
                      <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                        {THEME_OPTIONS.find(t => t.id === selectedTheme)?.description}
                      </p>
                    </div>
                  <div>
                    <label style={{ 
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontSize: '12px', 
                      fontWeight: 600, 
                      color: '#0f172a', 
                      marginBottom: '8px' 
                    }}>
                      <Type size={14} style={{ color: '#667eea' }} />
                      Font
                      {isReapplyingText && (
                        <Loader2 size={12} className="animate-spin" style={{ marginLeft: '4px', color: '#667eea' }} />
                      )}
                    </label>
                    <select
                      className="select"
                      value={selectedFont}
                      onChange={(e) => handleFontChange(e.target.value)}
                      style={{ fontSize: '13px' }}
                      disabled={isGenerating || isReapplyingText || slide.image_status === 'generating'}
                    >
                      {FONT_OPTIONS.map((font) => (
                        <option key={font.id} value={font.id}>
                          {font.name} - {font.style}
                        </option>
                      ))}
                    </select>
                    {isReapplyingText && (
                      <p style={{ fontSize: '11px', color: '#667eea', marginTop: '4px' }}>
                        Applying new font...
                      </p>
                    )}
                  </div>
                  </div>
                  {slide.final_image_path && (
                    <div style={{ marginTop: '10px', fontSize: '11px', color: '#64748b' }}>
                      <p style={{ marginBottom: '4px' }}>
                        <span style={{ color: '#22c55e' }}>⚡ Font change:</span> Instant (reuses background)
                      </p>
                      <p>
                        <span style={{ color: '#f59e0b' }}>🎨 Theme change:</span> Regenerates background
                      </p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div 
              style={{
                aspectRatio: '9/16',
                background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                borderRadius: '16px',
                overflow: 'hidden',
                position: 'relative',
                border: '2px solid rgba(148, 163, 184, 0.2)',
              }}
              whileHover={{ borderColor: 'rgba(102, 126, 234, 0.4)' }}
            >
              {slide.final_image_path ? (
                <img
                  src={getSlideImageUrl(slide.final_image_path, imageCacheBuster) || ''}
                  alt={slide.title || 'Slide'}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : slide.image_status === 'generating' || isGenerating || isReapplyingText ? (
                <div style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                }}>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  >
                    <Sparkles size={32} style={{ color: '#667eea' }} />
                  </motion.div>
                  <p style={{ fontSize: '14px', color: '#667eea', marginTop: '12px', fontWeight: 500 }}>Generating...</p>
                </div>
              ) : (
                <div style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <ImageIcon size={32} style={{ color: '#94a3b8' }} />
                  <p style={{ fontSize: '14px', color: '#94a3b8', marginTop: '8px' }}>No image yet</p>
                </div>
              )}
              {slide.error_message && (
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  padding: '12px',
                  background: 'rgba(239, 68, 68, 0.95)',
                  backdropFilter: 'blur(10px)',
                }}>
                  <p style={{ fontSize: '12px', color: 'white' }}>{slide.error_message}</p>
                </div>
              )}
            </motion.div>
            
            {/* Previous Version Section */}
            <AnimatePresence>
              {showPreviousVersion && previousVersion && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  style={{
                    marginTop: '12px',
                    padding: '12px',
                    background: 'linear-gradient(135deg, rgba(148, 163, 184, 0.08) 0%, rgba(100, 116, 139, 0.08) 100%)',
                    borderRadius: '12px',
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                  }}
                >
                  <div 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                    }}
                    onClick={() => setExpandedPrevious(!expandedPrevious)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <History size={14} style={{ color: '#64748b' }} />
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b' }}>
                        Previous Version
                      </span>
                      <span style={{ 
                        fontSize: '11px', 
                        color: '#94a3b8',
                        background: 'rgba(148, 163, 184, 0.15)',
                        padding: '2px 8px',
                        borderRadius: '10px',
                      }}>
                        {FONT_OPTIONS.find(f => f.id === previousVersion.font)?.name || previousVersion.font} • {THEME_OPTIONS.find(t => t.id === previousVersion.theme)?.name || previousVersion.theme}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <motion.div
                        animate={{ rotate: expandedPrevious ? 90 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronRight size={16} style={{ color: '#64748b' }} />
                      </motion.div>
                      <motion.button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowPreviousVersion(false);
                          setPreviousVersion(null);
                        }}
                        style={{
                          padding: '4px',
                          borderRadius: '6px',
                          border: 'none',
                          background: 'transparent',
                          color: '#94a3b8',
                          cursor: 'pointer',
                        }}
                        whileHover={{ background: 'rgba(148, 163, 184, 0.2)', color: '#64748b' }}
                      >
                        <X size={14} />
                      </motion.button>
                    </div>
                  </div>
                  
                  <AnimatePresence>
                    {expandedPrevious && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        style={{ overflow: 'hidden' }}
                      >
                        <div style={{ 
                          display: 'grid', 
                          gridTemplateColumns: '120px 1fr', 
                          gap: '12px',
                          marginTop: '12px',
                          paddingTop: '12px',
                          borderTop: '1px solid rgba(148, 163, 184, 0.15)',
                        }}>
                          {/* Thumbnail */}
                          <motion.div 
                            style={{
                              aspectRatio: '9/16',
                              borderRadius: '8px',
                              overflow: 'hidden',
                              border: '1px solid rgba(148, 163, 184, 0.2)',
                              cursor: 'pointer',
                            }}
                            whileHover={{ scale: 1.02 }}
                          >
                            <img
                              src={getSlideImageUrl(previousVersion.imagePath) || ''}
                              alt="Previous version"
                              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            />
                          </motion.div>
                          
                          {/* Details */}
                          <div style={{ fontSize: '12px', color: '#64748b' }}>
                            <div style={{ marginBottom: '8px' }}>
                              <span style={{ fontWeight: 600, color: '#475569' }}>Font: </span>
                              {FONT_OPTIONS.find(f => f.id === previousVersion.font)?.name || previousVersion.font}
                              <span style={{ color: '#94a3b8' }}> ({FONT_OPTIONS.find(f => f.id === previousVersion.font)?.style})</span>
                            </div>
                            <div style={{ marginBottom: '8px' }}>
                              <span style={{ fontWeight: 600, color: '#475569' }}>Theme: </span>
                              {THEME_OPTIONS.find(t => t.id === previousVersion.theme)?.name || previousVersion.theme}
                            </div>
                            {previousVersion.subtitle && (
                              <div>
                                <span style={{ fontWeight: 600, color: '#475569' }}>Text: </span>
                                <span style={{ 
                                  display: 'block', 
                                  marginTop: '4px',
                                  fontSize: '11px',
                                  color: '#94a3b8',
                                  fontStyle: 'italic',
                                  maxHeight: '40px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                }}>
                                  "{previousVersion.subtitle.substring(0, 100)}{previousVersion.subtitle.length > 100 ? '...' : ''}"
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  {/* Collapsed thumbnail preview */}
                  {!expandedPrevious && (
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      marginTop: '8px',
                    }}>
                      <div style={{
                        width: '40px',
                        height: '71px',
                        borderRadius: '4px',
                        overflow: 'hidden',
                        border: '1px solid rgba(148, 163, 184, 0.2)',
                      }}>
                        <img
                          src={getSlideImageUrl(previousVersion.imagePath) || ''}
                          alt="Previous version thumbnail"
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      </div>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                        Click to expand
                      </span>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Version History Panel */}
        <AnimatePresence>
          {showVersionHistory && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              style={{
                borderTop: '1px solid rgba(148, 163, 184, 0.15)',
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%)',
              }}
            >
              <div style={{ padding: '16px 20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <History size={16} style={{ color: '#667eea' }} />
                    <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>
                      Version History ({versions.length} versions)
                    </h4>
                  </div>
                  <motion.button
                    onClick={() => setShowVersionHistory(false)}
                    style={{
                      padding: '4px',
                      borderRadius: '6px',
                      border: 'none',
                      background: 'transparent',
                      color: '#94a3b8',
                      cursor: 'pointer',
                    }}
                    whileHover={{ background: 'rgba(148, 163, 184, 0.2)', color: '#64748b' }}
                  >
                    <X size={16} />
                  </motion.button>
                </div>
                
                {loadingVersions ? (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
                    <Loader2 size={20} className="animate-spin" style={{ color: '#667eea' }} />
                  </div>
                ) : versions.length === 0 ? (
                  <p style={{ fontSize: '13px', color: '#64748b', textAlign: 'center', padding: '20px' }}>
                    No version history yet
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
                    {versions.map((version) => (
                      <motion.div
                        key={version.id}
                        style={{
                          display: 'grid',
                          gridTemplateColumns: '60px 1fr auto',
                          gap: '12px',
                          padding: '12px',
                          background: 'white',
                          borderRadius: '10px',
                          border: '1px solid rgba(148, 163, 184, 0.15)',
                          alignItems: 'center',
                        }}
                        whileHover={{ borderColor: 'rgba(102, 126, 234, 0.3)' }}
                      >
                        {/* Thumbnail */}
                        <div style={{
                          width: '60px',
                          height: '106px',
                          borderRadius: '6px',
                          overflow: 'hidden',
                          background: '#f1f5f9',
                        }}>
                          {version.final_image_path && (
                            <img
                              src={getSlideImageUrl(version.final_image_path) || ''}
                              alt={`Version ${version.version_number}`}
                              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                            />
                          )}
                        </div>
                        
                        {/* Details */}
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <span style={{ 
                              fontSize: '12px', 
                              fontWeight: 600, 
                              color: '#667eea',
                              background: 'rgba(102, 126, 234, 0.1)',
                              padding: '2px 8px',
                              borderRadius: '10px',
                            }}>
                              v{version.version_number}
                            </span>
                            <span style={{
                              fontSize: '11px',
                              color: '#64748b',
                              background: 'rgba(148, 163, 184, 0.1)',
                              padding: '2px 8px',
                              borderRadius: '10px',
                            }}>
                              {version.change_type.replace('_', ' ')}
                            </span>
                          </div>
                          <p style={{ fontSize: '12px', color: '#475569', marginBottom: '4px' }}>
                            {version.change_description || 'No description'}
                          </p>
                          <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: '#94a3b8' }}>
                            {version.font && <span>Font: {version.font}</span>}
                            {version.theme && <span>Theme: {version.theme}</span>}
                          </div>
                          {version.created_at && (
                            <p style={{ fontSize: '10px', color: '#cbd5e1', marginTop: '4px' }}>
                              {new Date(version.created_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                        
                        {/* Revert button */}
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleRevertToVersion(version.version_number)}
                          loading={revertingVersion === version.version_number}
                          disabled={version.version_number === slide.current_version}
                        >
                          {version.version_number === slide.current_version ? 'Current' : 'Revert'}
                        </Button>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Actions */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderTop: '1px solid rgba(148, 163, 184, 0.15)',
          background: 'rgba(248, 250, 252, 0.5)',
        }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRegenerate(slide.id)}
              icon={<RefreshCw size={14} />}
            >
              Regenerate Script
            </Button>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              variant="primary"
              size="sm"
              onClick={handleGenerateWithOptions}
              loading={isGenerating}
              icon={<ImageIcon size={14} />}
            >
              {slide.image_status === 'complete' ? 'Regenerate Image' : 'Generate Image'}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onDuplicate(slide.id)}
              icon={<Copy size={14} />}
            >
              Duplicate
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => onDelete(slide.id)}
              icon={<Trash2 size={14} />}
            >
              Delete
            </Button>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}
