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
  generateAutomationSample,
  addAutomationTopic,
  removeAutomationTopic,
} from '../api/client';
import type {
  Automation,
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

const SampleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
    <circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21 15 16 10 5 21"/>
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

  const sampleMutation = useMutation({
    mutationFn: generateAutomationSample,
    onSuccess: (data) => {
      setSampleResult(data);
      setShowSampleModal(true);
    },
  });

  const automations = automationsData?.automations || [];

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '600', color: '#fff', marginBottom: '8px' }}>
            Automations
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.6)' }}>
            Create recipes to automatically generate slideshows on a schedule
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <PlusIcon /> New Automation
        </Button>
      </div>

      {/* Automations Grid */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'rgba(255,255,255,0.6)' }}>
          Loading automations...
        </div>
      ) : automations.length === 0 ? (
        <GlassCard>
          <div style={{ textAlign: 'center', padding: '48px' }}>
            <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '16px' }}>
              No automations yet. Create one to get started!
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon /> Create First Automation
            </Button>
          </div>
        </GlassCard>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '20px' }}>
          {automations.map((automation) => (
            <AutomationCard
              key={automation.id}
              automation={automation}
              contentTypes={contentTypes || []}
              imageStyles={imageStyles || []}
              onSelect={() => setSelectedAutomation(automation)}
              onStart={() => startMutation.mutate(automation.id)}
              onStop={() => stopMutation.mutate(automation.id)}
              onSample={() => sampleMutation.mutate(automation.id)}
              onDelete={() => deleteMutation.mutate(automation.id)}
              isLoading={sampleMutation.isPending && sampleMutation.variables === automation.id}
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
  onSample: () => void;
  onDelete: () => void;
  isLoading: boolean;
}

function AutomationCard({
  automation,
  contentTypes,
  imageStyles,
  onSelect,
  onStart,
  onStop,
  onSample,
  onDelete,
  isLoading,
}: AutomationCardProps) {
  const contentType = contentTypes.find(ct => ct.id === automation.content_type);
  const imageStyle = imageStyles.find(is => is.id === automation.image_style);
  const isRunning = automation.status === 'running';

  return (
    <GlassCard>
      <div style={{ padding: '4px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#fff', marginBottom: '4px' }}>
              {automation.name}
            </h3>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                background: 'rgba(99, 102, 241, 0.3)',
                color: '#a5b4fc',
              }}>
                {contentType?.name || automation.content_type}
              </span>
              <span style={{
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                background: 'rgba(236, 72, 153, 0.3)',
                color: '#f9a8d4',
              }}>
                {imageStyle?.name || automation.image_style}
              </span>
            </div>
          </div>
          <div style={{
            padding: '4px 10px',
            borderRadius: '9999px',
            fontSize: '12px',
            fontWeight: '500',
            background: isRunning ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255, 255, 255, 0.1)',
            color: isRunning ? '#4ade80' : 'rgba(255,255,255,0.5)',
          }}>
            {automation.status}
          </div>
        </div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: '600', color: '#fff' }}>{automation.topics?.length || 0}</div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>Topics</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: '600', color: '#4ade80' }}>{automation.successful_runs}</div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>Completed</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: '600', color: '#f87171' }}>{automation.failed_runs}</div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>Failed</div>
          </div>
        </div>

        {/* Schedule Info */}
        {automation.schedule_times && automation.schedule_times.length > 0 && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
            padding: '8px 12px',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '8px',
          }}>
            <ClockIcon />
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.7)' }}>
              {automation.schedule_times.join(', ')}
            </span>
            {automation.schedule_days && automation.schedule_days.length > 0 && automation.schedule_days.length < 7 && (
              <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>
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
            padding: '8px 12px',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '8px',
          }}>
            <MailIcon />
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.7)' }}>
              {automation.email_address}
            </span>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
          {isRunning ? (
            <Button variant="secondary" onClick={onStop} style={{ flex: 1 }}>
              <StopIcon /> Stop
            </Button>
          ) : (
            <Button onClick={onStart} style={{ flex: 1 }}>
              <PlayIcon /> Start
            </Button>
          )}
          <Button
            variant="secondary"
            onClick={onSample}
            disabled={isLoading}
            style={{ flex: 1 }}
          >
            <SampleIcon /> {isLoading ? 'Generating...' : 'Sample'}
          </Button>
          <Button variant="secondary" onClick={onSelect} style={{ flex: 1 }}>
            Edit
          </Button>
          <Button
            variant="secondary"
            onClick={onDelete}
            style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.2)' }}
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
