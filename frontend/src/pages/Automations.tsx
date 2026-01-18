import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import GlassCard from '../components/GlassCard';
import Button from '../components/Button';
import {
  getAutomations,
  getContentTypes,
  getImageStyles,
  createAutomation,
  updateAutomation,
  deleteAutomation,
  startAutomation,
  stopAutomation,
  addAutomationTopic,
  removeAutomationTopic,
  getAutomationRuns,
  postRunNow,
  getAutomationQueue,
  skipQueueItem,
  API_BASE_URL,
} from '../api/client';
import type {
  Automation,
  AutomationRun,
  ContentType,
  ImageStyle,
  AutomationCreate,
} from '../api/client';

// Icons
const PlayIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M8 5v14l11-7z"/>
  </svg>
);

const StopIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <rect x="6" y="6" width="12" height="12"/>
  </svg>
);

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="5" x2="12" y2="19"/>
    <line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);

const TrashIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
);

const ClockIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
);

const MailIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
    <polyline points="22,6 12,13 2,6"/>
  </svg>
);

const HistoryIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
);

const TikTokIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
  </svg>
);

const InstagramIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
  </svg>
);

const SkipIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="5 4 15 12 5 20 5 4"/>
    <line x1="19" y1="5" x2="19" y2="19"/>
  </svg>
);

const QueueIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="8" y1="6" x2="21" y2="6"/>
    <line x1="8" y1="12" x2="21" y2="12"/>
    <line x1="8" y1="18" x2="21" y2="18"/>
    <line x1="3" y1="6" x2="3.01" y2="6"/>
    <line x1="3" y1="12" x2="3.01" y2="12"/>
    <line x1="3" y1="18" x2="3.01" y2="18"/>
  </svg>
);

const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);

const AlertIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
);

const ImageIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
    <circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21 15 16 10 5 21"/>
  </svg>
);

const ChevronDownIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 12 15 18 9"/>
  </svg>
);

const ChevronUpIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="18 15 12 9 6 15"/>
  </svg>
);

// Helper to get automation image URL from path
const getAutomationImageUrl = (imagePath: string): string => {
  if (!imagePath) return '';

  // If it's already a full URL (GCS), use it directly
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath;
  }

  // For automation images, they're stored in generated_slideshows/
  // The static mount is at /static/slideshows/ which maps to generated_slideshows/
  // Path format: generated_slideshows/gpt15/filename.png -> /static/slideshows/gpt15/filename.png
  if (imagePath.includes('generated_slideshows/')) {
    const relativePath = imagePath.replace('generated_slideshows/', '');
    return `${API_BASE_URL}/static/slideshows/${relativePath}`;
  }
  
  // For project slides (generated_slides/)
  if (imagePath.includes('generated_slides/')) {
    const filename = imagePath.split('/').pop();
    return `${API_BASE_URL}/static/slides/${filename}`;
  }
  
  // Fallback: assume it's a relative path under slideshows
  return `${API_BASE_URL}/static/slideshows/${imagePath}`;
};

const DAYS_OF_WEEK = [
  { id: 'monday', label: 'Mon' },
  { id: 'tuesday', label: 'Tue' },
  { id: 'wednesday', label: 'Wed' },
  { id: 'thursday', label: 'Thu' },
  { id: 'friday', label: 'Fri' },
  { id: 'saturday', label: 'Sat' },
  { id: 'sunday', label: 'Sun' },
];

export default function Automations() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAutomation, setSelectedAutomation] = useState<Automation | null>(null);
  const [sampleResult, setSampleResult] = useState<Record<string, unknown> | null>(null);
  const [showSampleModal, setShowSampleModal] = useState(false);
  const [showRunsModal, setShowRunsModal] = useState(false);
  const [runsAutomation, setRunsAutomation] = useState<Automation | null>(null);
  const [showQueueModal, setShowQueueModal] = useState(false);
  const [queueAutomation, setQueueAutomation] = useState<Automation | null>(null);

  // Queries
  const { data: automationsData, isLoading } = useQuery({
    queryKey: ['automations'],
    queryFn: getAutomations,
  });

  const { data: contentTypes } = useQuery({
    queryKey: ['content-types'],
    queryFn: getContentTypes,
  });

  const { data: imageStyles } = useQuery({
    queryKey: ['image-styles'],
    queryFn: getImageStyles,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createAutomation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
      setShowCreateModal(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAutomation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
      setSelectedAutomation(null);
    },
  });

  const startMutation = useMutation({
    mutationFn: startAutomation,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['automations'] }),
  });

  const stopMutation = useMutation({
    mutationFn: stopAutomation,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['automations'] }),
  });

  const automations = automationsData?.automations || [];

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b', marginBottom: '8px' }}>
            Automations
          </h1>
          <p style={{ color: '#64748b', fontSize: '15px' }}>
            Create recipes to automatically generate slideshows on a schedule
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <PlusIcon /> New Automation
        </Button>
      </div>

      {/* Automations Grid */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          Loading automations...
        </div>
      ) : automations.length === 0 ? (
        <GlassCard padding="xl">
          <div style={{ textAlign: 'center', padding: '32px' }}>
            <p style={{ color: '#64748b', marginBottom: '16px', fontSize: '15px' }}>
              No automations yet. Create one to get started!
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon /> Create First Automation
            </Button>
          </div>
        </GlassCard>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '20px' }}>
          {automations.map((automation) => (
            <AutomationCard
              key={automation.id}
              automation={automation}
              contentTypes={contentTypes || []}
              imageStyles={imageStyles || []}
              onSelect={() => setSelectedAutomation(automation)}
              onStart={() => startMutation.mutate(automation.id)}
              onStop={() => stopMutation.mutate(automation.id)}
              onDelete={() => deleteMutation.mutate(automation.id)}
              onShowRuns={() => {
                setRunsAutomation(automation);
                setShowRunsModal(true);
              }}
              onShowQueue={() => {
                setQueueAutomation(automation);
                setShowQueueModal(true);
              }}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <CreateAutomationModal
            contentTypes={contentTypes || []}
            imageStyles={imageStyles || []}
            onClose={() => setShowCreateModal(false)}
            onCreate={(data) => createMutation.mutate(data)}
            isLoading={createMutation.isPending}
          />
        )}
      </AnimatePresence>

      {/* Edit Modal */}
      <AnimatePresence>
        {selectedAutomation && (
          <EditAutomationModal
            automation={selectedAutomation}
            contentTypes={contentTypes || []}
            imageStyles={imageStyles || []}
            onClose={() => setSelectedAutomation(null)}
            onUpdate={(data) => updateAutomation(selectedAutomation.id, data).then(() => {
              queryClient.invalidateQueries({ queryKey: ['automations'] });
              setSelectedAutomation(null);
            })}
          />
        )}
      </AnimatePresence>

      {/* Sample Result Modal */}
      <AnimatePresence>
        {showSampleModal && sampleResult && (
          <SampleResultModal
            result={sampleResult}
            onClose={() => {
              setShowSampleModal(false);
              setSampleResult(null);
            }}
          />
        )}
      </AnimatePresence>

      {/* Runs History Modal */}
      <AnimatePresence>
        {showRunsModal && runsAutomation && (
          <RunsHistoryModal
            automation={runsAutomation}
            onClose={() => {
              setShowRunsModal(false);
              setRunsAutomation(null);
            }}
          />
        )}
      </AnimatePresence>

      {/* Queue Modal */}
      <AnimatePresence>
        {showQueueModal && queueAutomation && (
          <QueueModal
            automation={queueAutomation}
            onClose={() => {
              setShowQueueModal(false);
              setQueueAutomation(null);
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// =============================================================================
// AUTOMATION CARD
// =============================================================================

interface AutomationCardProps {
  automation: Automation;
  contentTypes: ContentType[];
  imageStyles: ImageStyle[];
  onSelect: () => void;
  onStart: () => void;
  onStop: () => void;
  onDelete: () => void;
  onShowRuns: () => void;
  onShowQueue: () => void;
}

function AutomationCard({
  automation,
  contentTypes,
  imageStyles,
  onSelect,
  onStart,
  onStop,
  onDelete,
  onShowRuns,
  onShowQueue,
}: AutomationCardProps) {
  const contentType = contentTypes.find(ct => ct.id === automation.content_type);
  const imageStyle = imageStyles.find(is => is.id === automation.image_style);
  const isRunning = automation.status === 'running';
  const hasProjectQueue = automation.project_ids && automation.project_ids.length > 0;
  const queueCount = hasProjectQueue ? automation.project_ids.length : (automation.topics?.length || 0);
  const queueRemaining = hasProjectQueue 
    ? automation.project_ids.length - automation.current_project_index 
    : automation.topics?.length || 0;

  return (
    <GlassCard padding="lg">
      <div>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 style={{ 
              fontSize: '17px', 
              fontWeight: '600', 
              color: '#1e293b', 
              marginBottom: '8px',
              lineHeight: '1.3',
            }}>
              {automation.name}
            </h3>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <span style={{
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: '500',
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#6366f1',
              }}>
                {contentType?.name || automation.content_type}
              </span>
              <span style={{
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: '500',
                background: 'rgba(236, 72, 153, 0.15)',
                color: '#ec4899',
              }}>
                {imageStyle?.name || automation.image_style}
              </span>
            </div>
          </div>
          <div style={{
            padding: '5px 12px',
            borderRadius: '9999px',
            fontSize: '12px',
            fontWeight: '600',
            background: isRunning ? 'rgba(34, 197, 94, 0.15)' : 'rgba(100, 116, 139, 0.1)',
            color: isRunning ? '#16a34a' : '#64748b',
            marginLeft: '12px',
            flexShrink: 0,
          }}>
            {automation.status}
          </div>
        </div>

        {/* Stats */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(4, 1fr)', 
          gap: '12px', 
          marginBottom: '16px',
          padding: '12px',
          background: 'rgba(148, 163, 184, 0.08)',
          borderRadius: '12px',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: '700', color: hasProjectQueue ? '#8b5cf6' : '#334155' }}>
              {queueRemaining}
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', fontWeight: '500' }}>
              {hasProjectQueue ? 'Projects' : 'Topics'}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#334155' }}>{automation.total_runs}</div>
            <div style={{ fontSize: '10px', color: '#64748b', fontWeight: '500' }}>Total</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#16a34a' }}>{automation.successful_runs}</div>
            <div style={{ fontSize: '10px', color: '#64748b', fontWeight: '500' }}>Success</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#dc2626' }}>{automation.failed_runs}</div>
            <div style={{ fontSize: '10px', color: '#64748b', fontWeight: '500' }}>Failed</div>
          </div>
        </div>

        {/* Queue Mode Badge */}
        {hasProjectQueue && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
            padding: '10px 14px',
            background: 'rgba(139, 92, 246, 0.1)',
            borderRadius: '10px',
            border: '1px solid rgba(139, 92, 246, 0.2)',
          }}>
            <QueueIcon />
            <span style={{ fontSize: '13px', color: '#a78bfa', fontWeight: '500' }}>
              Project Queue Mode
            </span>
            <span style={{ fontSize: '12px', color: 'rgba(167, 139, 250, 0.7)' }}>
              ({automation.current_project_index}/{queueCount} processed)
            </span>
          </div>
        )}

        {/* Schedule Info */}
        {automation.schedule_times && automation.schedule_times.length > 0 && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
            padding: '10px 14px',
            background: 'rgba(99, 102, 241, 0.08)',
            borderRadius: '10px',
            border: '1px solid rgba(99, 102, 241, 0.15)',
          }}>
            <ClockIcon />
            <span style={{ fontSize: '13px', color: '#475569', fontWeight: '500' }}>
              {automation.schedule_times.join(', ')}
            </span>
            {automation.schedule_days && automation.schedule_days.length > 0 && automation.schedule_days.length < 7 && (
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                ({automation.schedule_days.map(d => d.slice(0, 3)).join(', ')})
              </span>
            )}
          </div>
        )}

        {/* Email Info */}
        {automation.email_enabled && automation.email_address && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
            padding: '10px 14px',
            background: 'rgba(34, 197, 94, 0.08)',
            borderRadius: '10px',
            border: '1px solid rgba(34, 197, 94, 0.15)',
          }}>
            <MailIcon />
            <span style={{ fontSize: '13px', color: '#475569' }}>
              {automation.email_address}
            </span>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
          {isRunning ? (
            <Button variant="secondary" onClick={onStop} style={{ flex: '1 1 auto' }}>
              <StopIcon /> Stop
            </Button>
          ) : (
            <Button onClick={onStart} style={{ flex: '1 1 auto' }}>
              <PlayIcon /> Start
            </Button>
          )}
          <Button
            variant="secondary"
            onClick={onShowQueue}
            style={{ flex: '1 1 auto' }}
          >
            <QueueIcon /> Queue
          </Button>
          <Button
            variant="secondary"
            onClick={onShowRuns}
            style={{ flex: '1 1 auto' }}
          >
            <HistoryIcon /> Runs
          </Button>
          <Button variant="secondary" onClick={onSelect} style={{ padding: '8px 12px' }}>
            Edit
          </Button>
          <Button
            variant="secondary"
            onClick={onDelete}
            style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', color: '#dc2626' }}
          >
            <TrashIcon />
          </Button>
        </div>
      </div>
    </GlassCard>
  );
}

// =============================================================================
// CREATE AUTOMATION MODAL
// =============================================================================

interface CreateAutomationModalProps {
  contentTypes: ContentType[];
  imageStyles: ImageStyle[];
  onClose: () => void;
  onCreate: (data: AutomationCreate) => void;
  isLoading: boolean;
}

function CreateAutomationModal({ contentTypes, imageStyles, onClose, onCreate, isLoading }: CreateAutomationModalProps) {
  const [name, setName] = useState('');
  const [contentType, setContentType] = useState('wisdom_slideshow');
  const [imageStyle, setImageStyle] = useState('classical');
  const [topicsInput, setTopicsInput] = useState('');
  const [scheduleTime, setScheduleTime] = useState('09:00');
  const [scheduleDays, setScheduleDays] = useState<string[]>([]);
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [emailAddress, setEmailAddress] = useState('');

  const handleCreate = () => {
    const topics = topicsInput.split('\n').map(t => t.trim()).filter(t => t);
    onCreate({
      name,
      content_type: contentType,
      image_style: imageStyle,
      topics,
      schedule_times: scheduleTime ? [scheduleTime] : [],
      schedule_days: scheduleDays,
      email_enabled: emailEnabled,
      email_address: emailEnabled ? emailAddress : undefined,
    });
  };

  const toggleDay = (day: string) => {
    setScheduleDays(prev =>
      prev.includes(day)
        ? prev.filter(d => d !== day)
        : [...prev, day]
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'linear-gradient(135deg, rgba(30, 30, 50, 0.95), rgba(20, 20, 35, 0.95))',
          borderRadius: '16px',
          padding: '32px',
          maxWidth: '600px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#fff', marginBottom: '24px' }}>
          Create Automation Recipe
        </h2>

        {/* Name */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
            Recipe Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Daily Wisdom Posts"
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
            }}
          />
        </div>

        {/* Content Type */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
            Content Type
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
            {contentTypes.map(ct => (
              <button
                key={ct.id}
                onClick={() => {
                  setContentType(ct.id);
                  setImageStyle(ct.default_image_style);
                }}
                style={{
                  padding: '12px',
                  background: contentType === ct.id ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255,255,255,0.05)',
                  border: contentType === ct.id ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: '500', color: '#fff' }}>{ct.name}</div>
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginTop: '4px' }}>{ct.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Image Style */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
            Image Style
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
            {imageStyles.map(is => (
              <button
                key={is.id}
                onClick={() => setImageStyle(is.id)}
                style={{
                  padding: '10px',
                  background: imageStyle === is.id ? 'rgba(236, 72, 153, 0.3)' : 'rgba(255,255,255,0.05)',
                  border: imageStyle === is.id ? '1px solid rgba(236, 72, 153, 0.5)' : '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: '500', color: '#fff' }}>{is.name}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Topics */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
            Topics Queue (one per line)
          </label>
          <textarea
            value={topicsInput}
            onChange={(e) => setTopicsInput(e.target.value)}
            placeholder="5 Stoic philosophers who changed history\n4 truths about happiness the ancients knew\nWhy your anxiety is actually wisdom"
            rows={5}
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              resize: 'vertical',
            }}
          />
        </div>

        {/* Schedule */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
            Schedule Time
          </label>
          <input
            type="time"
            value={scheduleTime}
            onChange={(e) => setScheduleTime(e.target.value)}
            style={{
              padding: '12px 16px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
            }}
          />
          <div style={{ marginTop: '12px', display: 'flex', gap: '6px' }}>
            {DAYS_OF_WEEK.map(day => (
              <button
                key={day.id}
                onClick={() => toggleDay(day.id)}
                style={{
                  padding: '6px 10px',
                  background: scheduleDays.includes(day.id) ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255,255,255,0.05)',
                  border: scheduleDays.includes(day.id) ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  color: '#fff',
                  fontSize: '12px',
                }}
              >
                {day.label}
              </button>
            ))}
          </div>
          <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '8px' }}>
            Leave all days unselected to run every day
          </p>
        </div>

        {/* Email */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={emailEnabled}
              onChange={(e) => setEmailEnabled(e.target.checked)}
              style={{ width: '16px', height: '16px' }}
            />
            <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.7)' }}>
              Email me when slideshows are ready
            </span>
          </label>
          {emailEnabled && (
            <input
              type="email"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              placeholder="your@email.com"
              style={{
                width: '100%',
                marginTop: '8px',
                padding: '12px 16px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '14px',
              }}
            />
          )}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={!name || isLoading}>
            {isLoading ? 'Creating...' : 'Create Automation'}
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// =============================================================================
// EDIT AUTOMATION MODAL
// =============================================================================

interface EditAutomationModalProps {
  automation: Automation;
  contentTypes: ContentType[];
  imageStyles: ImageStyle[];
  onClose: () => void;
  onUpdate: (data: Partial<AutomationCreate>) => void;
}

function EditAutomationModal({ automation, contentTypes, imageStyles, onClose, onUpdate }: EditAutomationModalProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(automation.name);
  const [contentType, setContentType] = useState(automation.content_type);
  const [imageStyle, setImageStyle] = useState(automation.image_style);
  const [newTopic, setNewTopic] = useState('');
  const [scheduleTimes, setScheduleTimes] = useState(automation.schedule_times || []);
  const [scheduleDays, setScheduleDays] = useState(automation.schedule_days || []);
  const [emailEnabled, setEmailEnabled] = useState(automation.email_enabled);
  const [emailAddress, setEmailAddress] = useState(automation.email_address || '');

  const addTopicMutation = useMutation({
    mutationFn: (topic: string) => addAutomationTopic(automation.id, topic),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
      setNewTopic('');
    },
  });

  const removeTopicMutation = useMutation({
    mutationFn: (index: number) => removeAutomationTopic(automation.id, index),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['automations'] }),
  });

  const handleSave = () => {
    onUpdate({
      name,
      content_type: contentType,
      image_style: imageStyle,
      schedule_times: scheduleTimes,
      schedule_days: scheduleDays,
      email_enabled: emailEnabled,
      email_address: emailEnabled ? emailAddress : undefined,
    });
  };

  const toggleDay = (day: string) => {
    setScheduleDays(prev =>
      prev.includes(day)
        ? prev.filter(d => d !== day)
        : [...prev, day]
    );
  };

  const addScheduleTime = () => {
    const newTime = '12:00';
    if (!scheduleTimes.includes(newTime)) {
      setScheduleTimes([...scheduleTimes, newTime]);
    }
  };

  const updateScheduleTime = (index: number, time: string) => {
    const updated = [...scheduleTimes];
    updated[index] = time;
    setScheduleTimes(updated);
  };

  const removeScheduleTime = (index: number) => {
    setScheduleTimes(scheduleTimes.filter((_, i) => i !== index));
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'linear-gradient(135deg, rgba(30, 30, 50, 0.95), rgba(20, 20, 35, 0.95))',
          borderRadius: '16px',
          padding: '32px',
          maxWidth: '700px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#fff', marginBottom: '24px' }}>
          Edit Automation
        </h2>

        {/* Name */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
            Recipe Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
            }}
          />
        </div>

        {/* Content Type & Image Style side by side */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
              Content Type
            </label>
            <select
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '14px',
              }}
            >
              {contentTypes.map(ct => (
                <option key={ct.id} value={ct.id} style={{ background: '#1a1a2e' }}>
                  {ct.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
              Image Style
            </label>
            <select
              value={imageStyle}
              onChange={(e) => setImageStyle(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '14px',
              }}
            >
              {imageStyles.map(is => (
                <option key={is.id} value={is.id} style={{ background: '#1a1a2e' }}>
                  {is.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Topics Queue */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
            Topics Queue ({automation.topics?.length || 0} topics)
          </label>
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            padding: '12px',
            maxHeight: '200px',
            overflow: 'auto',
          }}>
            {(automation.topics || []).map((topic, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  background: index === automation.current_topic_index ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                  borderRadius: '6px',
                  marginBottom: '4px',
                }}
              >
                <span style={{
                  color: index === automation.current_topic_index ? '#a5b4fc' : 'rgba(255,255,255,0.8)',
                  fontSize: '13px',
                }}>
                  {index === automation.current_topic_index && '▶ '}{topic}
                </span>
                <button
                  onClick={() => removeTopicMutation.mutate(index)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'rgba(255,255,255,0.4)',
                    cursor: 'pointer',
                    padding: '4px',
                  }}
                >
                  ×
                </button>
              </div>
            ))}
            {(!automation.topics || automation.topics.length === 0) && (
              <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', textAlign: 'center', padding: '12px' }}>
                No topics in queue
              </p>
            )}
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <input
              type="text"
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              placeholder="Add a new topic..."
              style={{
                flex: 1,
                padding: '10px 14px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '13px',
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && newTopic.trim()) {
                  addTopicMutation.mutate(newTopic.trim());
                }
              }}
            />
            <Button
              onClick={() => newTopic.trim() && addTopicMutation.mutate(newTopic.trim())}
              disabled={!newTopic.trim() || addTopicMutation.isPending}
            >
              <PlusIcon /> Add
            </Button>
          </div>
        </div>

        {/* Schedule */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px' }}>
            Schedule Times
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
            {scheduleTimes.map((time, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <input
                  type="time"
                  value={time}
                  onChange={(e) => updateScheduleTime(index, e.target.value)}
                  style={{
                    padding: '8px 12px',
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '13px',
                  }}
                />
                <button
                  onClick={() => removeScheduleTime(index)}
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#f87171',
                    cursor: 'pointer',
                    padding: '8px 10px',
                  }}
                >
                  ×
                </button>
              </div>
            ))}
            <button
              onClick={addScheduleTime}
              style={{
                padding: '8px 14px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px dashed rgba(255,255,255,0.2)',
                borderRadius: '8px',
                color: 'rgba(255,255,255,0.6)',
                cursor: 'pointer',
                fontSize: '13px',
              }}
            >
              + Add Time
            </button>
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            {DAYS_OF_WEEK.map(day => (
              <button
                key={day.id}
                onClick={() => toggleDay(day.id)}
                style={{
                  padding: '6px 10px',
                  background: scheduleDays.includes(day.id) ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255,255,255,0.05)',
                  border: scheduleDays.includes(day.id) ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  color: '#fff',
                  fontSize: '12px',
                }}
              >
                {day.label}
              </button>
            ))}
          </div>
        </div>

        {/* Email */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={emailEnabled}
              onChange={(e) => setEmailEnabled(e.target.checked)}
              style={{ width: '16px', height: '16px' }}
            />
            <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.7)' }}>
              Email notifications
            </span>
          </label>
          {emailEnabled && (
            <input
              type="email"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              placeholder="your@email.com"
              style={{
                width: '100%',
                marginTop: '8px',
                padding: '12px 16px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '14px',
              }}
            />
          )}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Changes
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// =============================================================================
// SAMPLE RESULT MODAL
// =============================================================================

interface SampleResultModalProps {
  result: Record<string, unknown>;
  onClose: () => void;
}

function SampleResultModal({ result, onClose }: SampleResultModalProps) {
  const script = result.script as Record<string, unknown> | undefined;
  const slides = (script?.slides as Array<Record<string, unknown>>) || [];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'linear-gradient(135deg, rgba(30, 30, 50, 0.95), rgba(20, 20, 35, 0.95))',
          borderRadius: '16px',
          padding: '32px',
          maxWidth: '800px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#fff' }}>
            Sample Preview
          </h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            <span style={{
              padding: '4px 10px',
              borderRadius: '4px',
              fontSize: '12px',
              background: 'rgba(99, 102, 241, 0.3)',
              color: '#a5b4fc',
            }}>
              {result.content_type as string}
            </span>
            <span style={{
              padding: '4px 10px',
              borderRadius: '4px',
              fontSize: '12px',
              background: 'rgba(236, 72, 153, 0.3)',
              color: '#f9a8d4',
            }}>
              {result.image_style as string}
            </span>
          </div>
        </div>

        <div style={{
          padding: '12px 16px',
          background: 'rgba(34, 197, 94, 0.1)',
          border: '1px solid rgba(34, 197, 94, 0.3)',
          borderRadius: '8px',
          marginBottom: '24px',
        }}>
          <p style={{ color: '#4ade80', fontSize: '13px' }}>
            ✓ {result.message as string}
          </p>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '14px', color: 'rgba(255,255,255,0.6)', marginBottom: '8px' }}>Topic</h3>
          <p style={{ color: '#fff', fontSize: '16px', fontWeight: '500' }}>{result.topic as string}</p>
        </div>

        <div>
          <h3 style={{ fontSize: '14px', color: 'rgba(255,255,255,0.6)', marginBottom: '12px' }}>
            Generated Script ({slides.length} slides)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {slides.map((slide, index) => (
              <div
                key={index}
                style={{
                  padding: '16px',
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: '10px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    background: 'rgba(255,255,255,0.1)',
                    color: 'rgba(255,255,255,0.6)',
                  }}>
                    Slide {slide.slide_number as number} • {slide.slide_type as string}
                  </span>
                </div>
                <p style={{ color: '#fff', fontSize: '14px', whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
                  {String(slide.content || '')}
                </p>
                {typeof slide.visual_description === 'string' && slide.visual_description && (
                  <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '12px', marginTop: '8px', fontStyle: 'italic' }}>
                    Visual: {slide.visual_description}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
          <Button onClick={onClose}>
            Close Preview
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}


// =============================================================================
// RUNS HISTORY MODAL
// =============================================================================

interface RunsHistoryModalProps {
  automation: Automation;
  onClose: () => void;
}

function RunsHistoryModal({ automation, onClose }: RunsHistoryModalProps) {
  const queryClient = useQueryClient();
  const [retryingRunId, _setRetryingRunId] = useState<string | null>(null);
  const [retryMessage, setRetryMessage] = useState<{ runId: string; success: boolean; message: string } | null>(null);
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);

  // Fetch runs for this automation
  const { data: runsData, isLoading } = useQuery({
    queryKey: ['automation-runs', automation.id],
    queryFn: () => getAutomationRuns(automation.id, 20),
  });

  const [postingRunId, setPostingRunId] = useState<string | null>(null);
  const [postingPlatform, setPostingPlatform] = useState<string | null>(null);

  const postNowMutation = useMutation({
    mutationFn: ({ runId, platform }: { runId: string; platform: 'tiktok' | 'instagram' | 'both' }) => 
      postRunNow(automation.id, runId, platform),
    onMutate: ({ runId, platform }) => {
      setPostingRunId(runId);
      setPostingPlatform(platform);
      setRetryMessage(null);
    },
    onSuccess: (data, { runId }) => {
      setPostingRunId(null);
      setPostingPlatform(null);
      
      const tiktokResult = data.results.tiktok;
      const igResult = data.results.instagram;
      
      let message = '';
      if (tiktokResult?.success) message += 'TikTok ✓ ';
      if (tiktokResult && !tiktokResult.success) message += `TikTok failed: ${tiktokResult.error} `;
      if (igResult?.success) message += 'Instagram ✓';
      if (igResult && !igResult.success) message += `Instagram failed: ${igResult.error}`;
      
      setRetryMessage({ 
        runId, 
        success: data.success, 
        message: message || (data.success ? 'Posted!' : 'Failed to post')
      });
      
      queryClient.invalidateQueries({ queryKey: ['automation-runs', automation.id] });
    },
    onError: (error: Error, { runId }) => {
      setPostingRunId(null);
      setPostingPlatform(null);
      setRetryMessage({ runId, success: false, message: error.message });
    },
  });

  const runs = runsData?.runs || [];

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getTikTokStatus = (run: AutomationRun) => {
    if (run.tiktok_posted && run.tiktok_post_status === 'success') {
      return { label: 'Posted', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)' };
    }
    if (run.tiktok_post_status === 'pending' || run.tiktok_post_status === 'processing') {
      return { label: 'Processing', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' };
    }
    if (run.tiktok_post_status === 'failed' || run.tiktok_error) {
      return { label: 'Failed', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' };
    }
    if (run.status === 'completed' && !run.tiktok_posted) {
      return { label: 'Not Posted', color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.15)' };
    }
    return { label: '-', color: '#64748b', bg: 'transparent' };
  };

  const getInstagramStatus = (run: AutomationRun) => {
    if (run.instagram_posted && run.instagram_post_status === 'posted') {
      return { label: 'Posted', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)' };
    }
    if (run.instagram_post_status === 'pending') {
      return { label: 'Processing', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' };
    }
    if (run.instagram_post_status === 'failed' || run.instagram_error) {
      return { label: 'Failed', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' };
    }
    if (run.status === 'completed' && !run.instagram_posted) {
      return { label: 'Not Posted', color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.15)' };
    }
    return { label: '-', color: '#64748b', bg: 'transparent' };
  };

  const canRetry = (run: AutomationRun) => {
    // Can retry if completed/posted but TikTok failed or wasn't attempted
    return (
      (run.status === 'completed' || run.status === 'posted') &&
      run.image_paths &&
      run.image_paths.length >= 2 &&
      (run.tiktok_post_status === 'failed' || !run.tiktok_posted)
    );
  };

  const canPostInstagram = (run: AutomationRun) => {
    return (
      (run.status === 'completed' || run.status === 'posted') &&
      run.image_paths &&
      run.image_paths.length >= 2 &&
      (run.instagram_post_status === 'failed' || !run.instagram_posted)
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'linear-gradient(135deg, rgba(30, 30, 50, 0.95), rgba(20, 20, 35, 0.95))',
          borderRadius: '16px',
          padding: '32px',
          maxWidth: '900px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#fff', marginBottom: '4px' }}>
              Run History
            </h2>
            <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.5)' }}>
              {automation.name}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.1)',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 12px',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>

        {/* Info banner about TikTok limits */}
        <div style={{
          padding: '12px 16px',
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          borderRadius: '8px',
          marginBottom: '24px',
        }}>
          <p style={{ color: '#a5b4fc', fontSize: '13px', lineHeight: '1.5' }}>
            <strong>💡 TikTok Limit:</strong> Max 5 pending drafts per 24 hours. 
            If "Retry" fails with <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: '4px' }}>spam_risk_too_many_pending_share</code>, 
            open TikTok and publish/delete some drafts first.
          </p>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'rgba(255,255,255,0.5)' }}>
            Loading runs...
          </div>
        ) : runs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'rgba(255,255,255,0.5)' }}>
            No runs yet. Start the automation to generate slideshows.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {runs.map((run) => {
              const tiktokStatus = getTikTokStatus(run);
              const instagramStatus = getInstagramStatus(run);
              const showRetry = canRetry(run);
              const showPostInstagram = canPostInstagram(run);
              const isRetrying = retryingRunId === run.id;
              const isPosting = postingRunId === run.id;
              const messageForRun = retryMessage?.runId === run.id ? retryMessage : null;

              return (
                <div
                  key={run.id}
                  style={{
                    padding: '16px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                    {/* Left: Topic and info */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ 
                        color: '#fff', 
                        fontSize: '14px', 
                        fontWeight: '500', 
                        marginBottom: '8px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}>
                        {run.topic}
                      </p>
                      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                          {formatDate(run.started_at)}
                        </span>
                        <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                          ⏱ {formatDuration(run.duration_seconds)}
                        </span>
                        <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                          📊 {run.slides_count} slides
                        </span>
                      </div>
                    </div>

                    {/* Right: Status */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0, flexWrap: 'wrap' }}>
                      {/* Run Status */}
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '500',
                        background: run.status === 'completed' || run.status === 'posted'
                          ? 'rgba(34, 197, 94, 0.15)' 
                          : run.status === 'failed'
                            ? 'rgba(239, 68, 68, 0.15)'
                            : 'rgba(245, 158, 11, 0.15)',
                        color: run.status === 'completed' || run.status === 'posted'
                          ? '#22c55e'
                          : run.status === 'failed'
                            ? '#ef4444'
                            : '#f59e0b',
                      }}>
                        {run.status}
                      </span>

                      {/* TikTok Status */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <TikTokIcon />
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '6px',
                          fontSize: '10px',
                          fontWeight: '500',
                          background: tiktokStatus.bg,
                          color: tiktokStatus.color,
                        }}>
                          {tiktokStatus.label}
                        </span>
                      </div>

                      {/* Instagram Status */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <InstagramIcon />
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '6px',
                          fontSize: '10px',
                          fontWeight: '500',
                          background: instagramStatus.bg,
                          color: instagramStatus.color,
                        }}>
                          {instagramStatus.label}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Post Now Buttons */}
                  {(showRetry || showPostInstagram) && (
                    <div style={{ display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
                      {showRetry && (
                        <Button
                          variant="secondary"
                          onClick={() => postNowMutation.mutate({ runId: run.id, platform: 'tiktok' })}
                          disabled={isPosting || isRetrying}
                          style={{
                            padding: '6px 12px',
                            fontSize: '11px',
                            background: 'rgba(0, 0, 0, 0.3)',
                            border: '1px solid rgba(255,255,255,0.2)',
                          }}
                        >
                          {isPosting && postingPlatform === 'tiktok' ? (
                            <>Posting...</>
                          ) : (
                            <><TikTokIcon /> Post to TikTok</>
                          )}
                        </Button>
                      )}
                      {showPostInstagram && (
                        <Button
                          variant="secondary"
                          onClick={() => postNowMutation.mutate({ runId: run.id, platform: 'instagram' })}
                          disabled={isPosting || isRetrying}
                          style={{
                            padding: '6px 12px',
                            fontSize: '11px',
                            background: 'rgba(225, 48, 108, 0.15)',
                            border: '1px solid rgba(225, 48, 108, 0.3)',
                          }}
                        >
                          {isPosting && postingPlatform === 'instagram' ? (
                            <>Posting...</>
                          ) : (
                            <><InstagramIcon /> Post to Instagram</>
                          )}
                        </Button>
                      )}
                      {showRetry && showPostInstagram && (
                        <Button
                          variant="secondary"
                          onClick={() => postNowMutation.mutate({ runId: run.id, platform: 'both' })}
                          disabled={isPosting || isRetrying}
                          style={{
                            padding: '6px 12px',
                            fontSize: '11px',
                            background: 'rgba(99, 102, 241, 0.2)',
                            border: '1px solid rgba(99, 102, 241, 0.4)',
                          }}
                        >
                          {isPosting && postingPlatform === 'both' ? (
                            <>Posting...</>
                          ) : (
                            <>Post to Both</>
                          )}
                        </Button>
                      )}
                    </div>
                  )}

                  {/* View Slides Button */}
                  {run.image_paths && run.image_paths.length > 0 && (
                    <button
                      onClick={() => setExpandedRunId(expandedRunId === run.id ? null : run.id)}
                      style={{
                        marginTop: '12px',
                        padding: '10px 14px',
                        background: expandedRunId === run.id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        width: '100%',
                        color: '#fff',
                      }}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                        <ImageIcon />
                        View {run.image_paths.length} Generated Slides
                      </span>
                      {expandedRunId === run.id ? <ChevronUpIcon /> : <ChevronDownIcon />}
                    </button>
                  )}

                  {/* Expanded Image Gallery */}
                  <AnimatePresence>
                    {expandedRunId === run.id && run.image_paths && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        style={{ overflow: 'hidden' }}
                      >
                        <div style={{
                          marginTop: '12px',
                          padding: '16px',
                          background: 'rgba(0,0,0,0.3)',
                          borderRadius: '12px',
                          border: '1px solid rgba(255,255,255,0.1)',
                        }}>
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
                            gap: '12px',
                          }}>
                            {run.image_paths.map((imagePath, imgIndex) => (
                              <div
                                key={imgIndex}
                                onClick={() => setLightboxImage(getAutomationImageUrl(imagePath))}
                                style={{
                                  cursor: 'pointer',
                                  borderRadius: '8px',
                                  overflow: 'hidden',
                                  aspectRatio: '9/16',
                                  background: 'rgba(255,255,255,0.05)',
                                  position: 'relative',
                                }}
                              >
                                <img
                                  src={getAutomationImageUrl(imagePath)}
                                  alt={`Slide ${imgIndex + 1}`}
                                  style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover',
                                  }}
                                  onError={(e) => {
                                    (e.target as HTMLImageElement).style.display = 'none';
                                  }}
                                />
                                <div style={{
                                  position: 'absolute',
                                  bottom: '4px',
                                  left: '4px',
                                  padding: '2px 6px',
                                  background: 'rgba(0,0,0,0.7)',
                                  borderRadius: '4px',
                                  fontSize: '10px',
                                  color: '#fff',
                                }}>
                                  {imgIndex + 1}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Error message */}
                  {run.tiktok_error && !messageForRun && (
                    <div style={{
                      marginTop: '12px',
                      padding: '8px 12px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}>
                      <AlertIcon />
                      <span style={{ fontSize: '12px', color: '#f87171' }}>
                        {run.tiktok_error}
                      </span>
                    </div>
                  )}

                  {/* Retry result message */}
                  {messageForRun && (
                    <div style={{
                      marginTop: '12px',
                      padding: '8px 12px',
                      background: messageForRun.success
                        ? 'rgba(34, 197, 94, 0.1)'
                        : 'rgba(239, 68, 68, 0.1)',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}>
                      {messageForRun.success ? <CheckIcon /> : <AlertIcon />}
                      <span style={{
                        fontSize: '12px',
                        color: messageForRun.success ? '#4ade80' : '#f87171'
                      }}>
                        {messageForRun.message}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
          <Button onClick={onClose}>
            Close
          </Button>
        </div>
      </motion.div>

      {/* Lightbox for full-size image */}
      <AnimatePresence>
        {lightboxImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLightboxImage(null)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.95)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 2000,
              padding: '24px',
              cursor: 'zoom-out',
            }}
          >
            <motion.img
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              src={lightboxImage}
              alt="Full size slide"
              style={{
                maxWidth: '90vw',
                maxHeight: '90vh',
                objectFit: 'contain',
                borderRadius: '12px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
              }}
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setLightboxImage(null)}
              style={{
                position: 'absolute',
                top: '24px',
                right: '24px',
                background: 'rgba(255,255,255,0.1)',
                border: 'none',
                borderRadius: '50%',
                width: '48px',
                height: '48px',
                color: '#fff',
                fontSize: '24px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              ✕
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}


// =============================================================================
// QUEUE MODAL
// =============================================================================

interface QueueModalProps {
  automation: Automation;
  onClose: () => void;
}

function QueueModal({ automation, onClose }: QueueModalProps) {
  const queryClient = useQueryClient();

  // Fetch queue status
  const { data: queueData, isLoading } = useQuery({
    queryKey: ['automation-queue', automation.id],
    queryFn: () => getAutomationQueue(automation.id),
  });

  const skipMutation = useMutation({
    mutationFn: () => skipQueueItem(automation.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automation-queue', automation.id] });
      queryClient.invalidateQueries({ queryKey: ['automations'] });
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <span style={{ color: '#22c55e' }}>✓</span>;
      case 'current':
        return <span style={{ color: '#f59e0b' }}>▶</span>;
      default:
        return <span style={{ color: '#64748b' }}>○</span>;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return { bg: 'rgba(34, 197, 94, 0.1)', border: 'rgba(34, 197, 94, 0.3)' };
      case 'current':
        return { bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.4)' };
      default:
        return { bg: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.08)' };
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'linear-gradient(135deg, rgba(30, 30, 50, 0.95), rgba(20, 20, 35, 0.95))',
          borderRadius: '16px',
          padding: '32px',
          maxWidth: '700px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#fff', marginBottom: '4px' }}>
              Queue
            </h2>
            <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.5)' }}>
              {automation.name}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.1)',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 12px',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>

        {/* Queue Stats */}
        {queueData && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '12px',
            marginBottom: '24px',
            padding: '16px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '12px',
            border: '1px solid rgba(255,255,255,0.08)',
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginBottom: '4px' }}>Mode</div>
              <div style={{ 
                fontSize: '13px', 
                fontWeight: '600', 
                color: queueData.queue_mode === 'projects' ? '#a78bfa' : '#60a5fa',
                textTransform: 'capitalize',
              }}>
                {queueData.queue_mode}
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginBottom: '4px' }}>Total</div>
              <div style={{ fontSize: '20px', fontWeight: '700', color: '#fff' }}>{queueData.total_items}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginBottom: '4px' }}>Current</div>
              <div style={{ fontSize: '20px', fontWeight: '700', color: '#f59e0b' }}>{queueData.current_index + 1}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginBottom: '4px' }}>Remaining</div>
              <div style={{ fontSize: '20px', fontWeight: '700', color: '#22c55e' }}>{queueData.remaining}</div>
            </div>
          </div>
        )}

        {/* Queue Exhausted Warning */}
        {queueData?.is_exhausted && (
          <div style={{
            padding: '12px 16px',
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '8px',
            marginBottom: '24px',
          }}>
            <p style={{ color: '#fbbf24', fontSize: '13px' }}>
              ⚠️ Queue exhausted. Add more {queueData.queue_mode} to continue automation.
            </p>
          </div>
        )}

        {/* Skip Button */}
        {queueData && !queueData.is_exhausted && (
          <div style={{ marginBottom: '24px' }}>
            <Button
              variant="secondary"
              onClick={() => skipMutation.mutate()}
              disabled={skipMutation.isPending}
              style={{ 
                background: 'rgba(99, 102, 241, 0.15)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
              }}
            >
              <SkipIcon /> {skipMutation.isPending ? 'Skipping...' : 'Skip Current Item'}
            </Button>
          </div>
        )}

        {/* Queue Items */}
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'rgba(255,255,255,0.5)' }}>
            Loading queue...
          </div>
        ) : queueData?.items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'rgba(255,255,255,0.5)' }}>
            No items in queue. Add topics or projects to get started.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {queueData?.items.map((item) => {
              const statusColors = getStatusColor(item.status);
              return (
                <div
                  key={item.index}
                  style={{
                    padding: '14px 16px',
                    background: statusColors.bg,
                    border: `1px solid ${statusColors.border}`,
                    borderRadius: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                  }}
                >
                  <span style={{ fontSize: '16px', width: '24px', textAlign: 'center' }}>
                    {getStatusIcon(item.status)}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{
                      color: item.status === 'current' ? '#fbbf24' : '#fff',
                      fontSize: '14px',
                      fontWeight: item.status === 'current' ? '600' : '400',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}>
                      {item.title}
                    </p>
                    {item.type === 'project' && item.id && (
                      <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '2px' }}>
                        Project ID: {item.id.slice(0, 8)}...
                      </p>
                    )}
                  </div>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '6px',
                    fontSize: '10px',
                    fontWeight: '600',
                    textTransform: 'uppercase',
                    background: item.status === 'completed' ? 'rgba(34, 197, 94, 0.2)' :
                               item.status === 'current' ? 'rgba(245, 158, 11, 0.2)' :
                               'rgba(100, 116, 139, 0.2)',
                    color: item.status === 'completed' ? '#4ade80' :
                           item.status === 'current' ? '#fbbf24' :
                           '#94a3b8',
                  }}>
                    {item.status}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
          <Button onClick={onClose}>
            Close
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}
