import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle2, 
  RefreshCw, 
  Edit3, 
  Eye, 
  ChevronDown,
  ChevronUp,
  AlertCircle
} from 'lucide-react';
import type { Project, Slide } from '../api/client';
import GlassCard from './GlassCard';
import Button from './Button';

interface ScriptReviewProps {
  project: Project;
  onApprove: () => void;
  onRegenerateAll: (newStyle?: string) => void;
  onRegenerateSlide: (slideIndex: number) => void;
  onUpdateSlide: (slideId: string, data: { title?: string | null; subtitle?: string | null; visual_description?: string | null; narration?: string | null }) => void;
  scriptStyles?: Array<{ id: string; name: string; description: string; example: string }>;
  isRegenerating?: boolean;
  isApproving?: boolean;
}

export default function ScriptReview({
  project,
  onApprove,
  onRegenerateAll,
  onRegenerateSlide,
  onUpdateSlide,
  scriptStyles = [],
  isRegenerating = false,
  isApproving = false,
}: ScriptReviewProps) {
  const [expandedSlideId, setExpandedSlideId] = useState<string | null>(null);
  const [editingSlideId, setEditingSlideId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<Slide>>({});
  const [showStyleSelector, setShowStyleSelector] = useState(false);

  const slides = project.slides || [];

  const handleEditSlide = (slide: Slide) => {
    setEditingSlideId(slide.id);
    setEditForm({
      title: slide.title || '',
      subtitle: slide.subtitle || '',
      visual_description: slide.visual_description || '',
      narration: slide.narration || '',
    });
  };

  const handleSaveEdit = () => {
    if (editingSlideId && editForm) {
      onUpdateSlide(editingSlideId, editForm);
      setEditingSlideId(null);
      setEditForm({});
    }
  };

  const handleCancelEdit = () => {
    setEditingSlideId(null);
    setEditForm({});
  };

  const currentStyle = scriptStyles.find(s => s.id === project.script_style);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <GlassCard gradient="blue" padding="lg">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <Eye size={24} style={{ color: '#667eea' }} />
              <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }}>
                Review Your Script
              </h2>
            </div>
            <p style={{ fontSize: '15px', color: '#64748b', marginBottom: '12px' }}>
              Review the generated script below. You can edit individual slides, regenerate specific ones, or regenerate the entire script with a different style.
            </p>
            {currentStyle && (
              <div style={{ 
                display: 'inline-flex', 
                alignItems: 'center', 
                gap: '8px',
                padding: '8px 14px',
                background: 'rgba(102, 126, 234, 0.1)',
                borderRadius: '12px',
                border: '1px solid rgba(102, 126, 234, 0.2)',
              }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#667eea' }}>
                  Style: {currentStyle.name}
                </span>
              </div>
            )}
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ position: 'relative' }}>
              <Button
                variant="secondary"
                onClick={() => setShowStyleSelector(!showStyleSelector)}
                icon={<RefreshCw size={18} />}
                loading={isRegenerating}
              >
                Change Style
              </Button>
              
              {showStyleSelector && (
                <AnimatePresence>
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
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
                      overflow: 'hidden',
                    }}
                  >
                    {scriptStyles.map((style) => (
                      <motion.button
                        key={style.id}
                        onClick={() => {
                          onRegenerateAll(style.id);
                          setShowStyleSelector(false);
                        }}
                        style={{
                          width: '100%',
                          textAlign: 'left',
                          padding: '14px 16px',
                          background: style.id === project.script_style ? 'rgba(102, 126, 234, 0.08)' : 'transparent',
                          border: 'none',
                          borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                          cursor: 'pointer',
                        }}
                        whileHover={{ background: 'rgba(102, 126, 234, 0.05)' }}
                      >
                        <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '4px' }}>
                          {style.name}
                        </p>
                        <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '6px' }}>
                          {style.description}
                        </p>
                        <p style={{ fontSize: '11px', color: '#94a3b8', fontStyle: 'italic' }}>
                          e.g., "{style.example}"
                        </p>
                      </motion.button>
                    ))}
                  </motion.div>
                </AnimatePresence>
              )}
            </div>
            <Button
              variant="primary"
              onClick={onApprove}
              icon={<CheckCircle2 size={20} />}
              loading={isApproving}
            >
              Approve & Continue
            </Button>
          </div>
        </div>
      </GlassCard>

      {/* Script Overview */}
      <GlassCard padding="lg">
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
            Full Script Overview
          </h3>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', color: '#64748b' }}>Total Slides:</span>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>{slides.length}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', color: '#64748b' }}>Topic:</span>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>{project.topic}</span>
            </div>
          </div>
        </div>

        {/* Slides list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {slides.map((slide, index) => {
            const isExpanded = expandedSlideId === slide.id;
            const isEditing = editingSlideId === slide.id;

            return (
              <motion.div
                key={slide.id}
                layout
                style={{
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  background: isExpanded ? 'rgba(102, 126, 234, 0.02)' : 'white',
                }}
              >
                {/* Slide header */}
                <div
                  style={{
                    padding: '16px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    background: 'transparent',
                  }}
                  onClick={() => setExpandedSlideId(isExpanded ? null : slide.id)}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        background: index === 0 
                          ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                          : index === slides.length - 1
                            ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                            : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        fontSize: '13px',
                        fontWeight: 700,
                      }}>
                        {index === 0 ? 'H' : index === slides.length - 1 ? 'O' : index}
                      </span>
                      <div>
                        <p style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a' }}>
                          {slide.title || 'Untitled Slide'}
                        </p>
                        {slide.subtitle && (
                          <p style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
                            {slide.subtitle.substring(0, 80)}{slide.subtitle.length > 80 ? '...' : ''}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Button
                      variant="ghost"
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
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e?.stopPropagation();
                        onRegenerateSlide(index);
                      }}
                      icon={<RefreshCw size={14} />}
                    >
                      Regenerate
                    </Button>
                    {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </div>

                {/* Expanded content */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      style={{ overflow: 'hidden' }}
                    >
                      <div style={{ 
                        padding: '20px', 
                        borderTop: '1px solid rgba(148, 163, 184, 0.1)',
                        background: 'white',
                      }}>
                        {isEditing ? (
                          // Edit mode
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
                              <label className="label">Subtitle</label>
                              <textarea
                                className="textarea"
                                value={editForm.subtitle || ''}
                                onChange={(e) => setEditForm({ ...editForm, subtitle: e.target.value })}
                                rows={2}
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
                            {editForm.narration !== undefined && (
                              <div>
                                <label className="label">Narration</label>
                                <textarea
                                  className="textarea"
                                  value={editForm.narration || ''}
                                  onChange={(e) => setEditForm({ ...editForm, narration: e.target.value })}
                                  rows={2}
                                />
                              </div>
                            )}
                            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                              <Button variant="secondary" onClick={handleCancelEdit}>
                                Cancel
                              </Button>
                              <Button variant="primary" onClick={handleSaveEdit} icon={<CheckCircle2 size={16} />}>
                                Save Changes
                              </Button>
                            </div>
                          </div>
                        ) : (
                          // View mode
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {slide.title && (
                              <div>
                                <p style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
                                  TITLE
                                </p>
                                <p style={{ fontSize: '14px', color: '#0f172a' }}>
                                  {slide.title}
                                </p>
                              </div>
                            )}
                            {slide.subtitle && (
                              <div>
                                <p style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
                                  SUBTITLE
                                </p>
                                <p style={{ fontSize: '14px', color: '#0f172a' }}>
                                  {slide.subtitle}
                                </p>
                              </div>
                            )}
                            {slide.visual_description && (
                              <div>
                                <p style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
                                  VISUAL DESCRIPTION
                                </p>
                                <p style={{ fontSize: '14px', color: '#64748b' }}>
                                  {slide.visual_description}
                                </p>
                              </div>
                            )}
                            {slide.narration && (
                              <div>
                                <p style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
                                  NARRATION
                                </p>
                                <p style={{ fontSize: '14px', color: '#64748b', fontStyle: 'italic' }}>
                                  "{slide.narration}"
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </GlassCard>

      {/* Warning */}
      <GlassCard gradient="orange" padding="md">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertCircle size={20} style={{ color: '#f59e0b' }} />
          <div>
            <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>
              Review carefully before approving
            </p>
            <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
              Once approved, the script will be locked and image generation will begin. You can still edit individual slides later, but major changes will require regeneration.
            </p>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
