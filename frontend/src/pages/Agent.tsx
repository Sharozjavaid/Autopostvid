import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  streamAgentMessage,
  getAgentTools,
  getAgentStatus,
  clearAgentSession,
  API_BASE_URL,
  type AgentStreamEvent,
  type ToolCall,
  type SlidePreviewData,
} from '../api/client';
import { useGallery, type GalleryItem } from '../context/GalleryContext';

// ============================================================================
// Types
// ============================================================================

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
  slidePreviews?: SlidePreviewData[];
  isStreaming?: boolean;
}

interface ActiveTool {
  name: string;
  input: Record<string, unknown>;
  status: 'running' | 'complete' | 'error';
  result?: Record<string, unknown>;
}

type TabType = 'chat' | 'gallery';
type GalleryFilterType = 'all' | 'slides' | 'scripts' | 'drafts';

// ============================================================================
// Styles
// ============================================================================

const styles = {
  pageContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    height: 'calc(100vh - 64px)',
    marginTop: '-32px',
    marginLeft: '-40px',
    marginRight: '-40px',
    marginBottom: '-32px',
    background: 'linear-gradient(180deg, rgba(102, 126, 234, 0.03) 0%, transparent 50%)',
  },
  
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 24px',
    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
    background: 'rgba(255, 255, 255, 0.5)',
    backdropFilter: 'blur(12px)',
  },
  
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  
  logoIcon: {
    width: '40px',
    height: '40px',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.25rem',
    boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
  },
  
  logoText: {
    fontSize: '1.125rem',
    fontWeight: 700,
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  
  statusBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    borderRadius: '20px',
    background: 'rgba(34, 197, 94, 0.1)',
    border: '1px solid rgba(34, 197, 94, 0.2)',
  },
  
  statusDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#22c55e',
    boxShadow: '0 0 6px #22c55e',
  },
  
  statusText: {
    fontSize: '0.75rem',
    color: '#16a34a',
    fontWeight: 500,
  },
  
  tabs: {
    display: 'flex',
    gap: '4px',
    padding: '4px',
    borderRadius: '12px',
    background: 'rgba(148, 163, 184, 0.1)',
  },
  
  tab: {
    padding: '8px 20px',
    borderRadius: '8px',
    border: 'none',
    background: 'transparent',
    color: '#64748b',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  
  tabActive: {
    background: '#fff',
    color: '#334155',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  },
  
  tabBadge: {
    fontSize: '0.6875rem',
    padding: '2px 6px',
    borderRadius: '10px',
    background: 'rgba(102, 126, 234, 0.15)',
    color: '#667eea',
    fontWeight: 600,
  },
  
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  
  actionButton: {
    padding: '8px 16px',
    borderRadius: '8px',
    border: '1px solid rgba(148, 163, 184, 0.2)',
    background: 'rgba(255, 255, 255, 0.8)',
    color: '#64748b',
    fontSize: '0.8125rem',
    fontWeight: 500,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.2s ease',
  },
  
  clearButton: {
    background: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.2)',
    color: '#dc2626',
  },
  
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
  },
  
  // Chat Panel Styles
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    maxWidth: '900px',
    width: '100%',
    margin: '0 auto',
    padding: '0 24px',
    height: '100%',
  },
  
  messagesArea: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '24px 0',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  
  messagesInner: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px',
    flex: 1,
  },
  
  messageWrapper: {
    display: 'flex',
    gap: '12px',
  },
  
  avatar: {
    width: '32px',
    height: '32px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.875rem',
    flexShrink: 0,
  },
  
  userAvatar: {
    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
  },
  
  assistantAvatar: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  
  messageContent: {
    flex: 1,
    minWidth: 0,
  },
  
  messageRole: {
    fontSize: '0.6875rem',
    fontWeight: 600,
    color: '#94a3b8',
    marginBottom: '4px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  
  messageBubble: {
    padding: '12px 16px',
    borderRadius: '16px',
    lineHeight: 1.6,
    fontSize: '0.9375rem',
  },
  
  userBubble: {
    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%)',
    border: '1px solid rgba(59, 130, 246, 0.15)',
    color: '#1e40af',
  },
  
  assistantBubble: {
    background: '#fff',
    border: '1px solid rgba(148, 163, 184, 0.15)',
    color: '#334155',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
  },
  
  inputContainer: {
    padding: '16px 0 24px',
    borderTop: '1px solid rgba(148, 163, 184, 0.1)',
    background: 'linear-gradient(180deg, transparent 0%, rgba(255, 255, 255, 0.5) 100%)',
  },
  
  inputWrapper: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '12px',
    background: '#fff',
    borderRadius: '16px',
    border: '1px solid rgba(148, 163, 184, 0.2)',
    padding: '8px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
    transition: 'all 0.2s ease',
  },
  
  inputWrapperFocused: {
    borderColor: 'rgba(102, 126, 234, 0.4)',
    boxShadow: '0 4px 20px rgba(102, 126, 234, 0.15)',
  },
  
  input: {
    flex: 1,
    padding: '10px 12px',
    background: 'transparent',
    border: 'none',
    outline: 'none',
    color: '#334155',
    fontSize: '0.9375rem',
    resize: 'none' as const,
    minHeight: '44px',
    maxHeight: '150px',
    fontFamily: 'inherit',
  },
  
  sendButton: {
    width: '44px',
    height: '44px',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    flexShrink: 0,
    boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
  },
  
  sendButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
    boxShadow: 'none',
  },
  
  // Empty State
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    padding: '48px 24px',
  },
  
  emptyIcon: {
    width: '80px',
    height: '80px',
    borderRadius: '24px',
    background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '2.5rem',
    marginBottom: '24px',
  },
  
  emptyTitle: {
    fontSize: '1.5rem',
    fontWeight: 700,
    color: '#1e293b',
    marginBottom: '8px',
  },
  
  emptyText: {
    fontSize: '0.9375rem',
    color: '#64748b',
    textAlign: 'center' as const,
    maxWidth: '400px',
    lineHeight: 1.6,
    marginBottom: '32px',
  },
  
  suggestionChips: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '10px',
    justifyContent: 'center',
    maxWidth: '600px',
  },
  
  suggestionChip: {
    padding: '10px 18px',
    borderRadius: '20px',
    background: '#fff',
    border: '1px solid rgba(148, 163, 184, 0.2)',
    color: '#475569',
    fontSize: '0.875rem',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
  },
  
  // Tool Cards
  toolsPanel: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '8px',
    marginTop: '12px',
  },
  
  toolCard: {
    padding: '8px 12px',
    borderRadius: '10px',
    background: 'rgba(102, 126, 234, 0.08)',
    border: '1px solid rgba(102, 126, 234, 0.15)',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  
  toolIcon: {
    width: '24px',
    height: '24px',
    borderRadius: '6px',
    background: 'rgba(102, 126, 234, 0.2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.75rem',
  },
  
  toolName: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#667eea',
  },
  
  // Slide Previews
  slidePreviewsContainer: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '12px',
    marginTop: '16px',
  },
  
  slidePreview: {
    width: '100px',
    borderRadius: '10px',
    overflow: 'hidden',
    border: '1px solid rgba(148, 163, 184, 0.2)',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    background: '#fff',
  },
  
  slidePreviewImage: {
    width: '100%',
    aspectRatio: '9 / 16',
    objectFit: 'cover' as const,
  },
  
  // Gallery Styles
  galleryContainer: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '24px',
  },
  
  galleryHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '20px',
  },
  
  galleryFilters: {
    display: 'flex',
    gap: '8px',
  },
  
  filterChip: {
    padding: '6px 14px',
    borderRadius: '16px',
    border: '1px solid rgba(148, 163, 184, 0.2)',
    background: '#fff',
    color: '#64748b',
    fontSize: '0.8125rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  
  filterChipActive: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: '1px solid transparent',
    color: '#fff',
  },
  
  galleryStats: {
    display: 'flex',
    gap: '16px',
  },
  
  statItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '0.8125rem',
    color: '#64748b',
  },
  
  galleryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: '16px',
  },
  
  galleryCard: {
    borderRadius: '12px',
    overflow: 'hidden',
    background: '#fff',
    border: '1px solid rgba(148, 163, 184, 0.15)',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  
  galleryCardImage: {
    width: '100%',
    aspectRatio: '9 / 16',
    objectFit: 'cover' as const,
    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
  },
  
  galleryCardContent: {
    padding: '12px',
  },
  
  galleryCardTitle: {
    fontSize: '0.8125rem',
    fontWeight: 600,
    color: '#334155',
    marginBottom: '4px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  
  galleryCardMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '0.6875rem',
    color: '#94a3b8',
  },
  
  galleryCardType: {
    padding: '2px 6px',
    borderRadius: '4px',
    background: 'rgba(102, 126, 234, 0.1)',
    color: '#667eea',
    fontWeight: 500,
    textTransform: 'capitalize' as const,
  },
  
  galleryEmptyState: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    padding: '80px 24px',
    textAlign: 'center' as const,
  },
  
  typingIndicator: {
    display: 'flex',
    gap: '4px',
    padding: '8px 0',
  },
  
  typingDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#667eea',
  },
};

// ============================================================================
// Components
// ============================================================================

const TypingIndicator = () => (
  <div style={styles.typingIndicator}>
    {[0, 1, 2].map((i) => (
      <motion.div
        key={i}
        style={styles.typingDot}
        animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1, 0.8] }}
        transition={{
          duration: 1,
          repeat: Infinity,
          delay: i * 0.2,
        }}
      />
    ))}
  </div>
);

const ToolCallCard = ({ tool }: { tool: ActiveTool | ToolCall }) => {
  const name = 'tool_name' in tool ? tool.tool_name : tool.name;
  const status = 'status' in tool ? tool.status : (tool.success ? 'complete' : 'error');
  
  return (
    <motion.div
      style={styles.toolCard}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <div style={styles.toolIcon}>
        {status === 'running' ? '⚡' : status === 'complete' ? '✓' : '✗'}
      </div>
      <span style={styles.toolName}>{name}</span>
      {status === 'running' && (
        <motion.div
          style={{ width: 12, height: 12, border: '2px solid #667eea', borderTopColor: 'transparent', borderRadius: '50%' }}
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
      )}
    </motion.div>
  );
};

const SlidePreviewCard = ({ slide, onClick }: { slide: SlidePreviewData; onClick?: () => void }) => {
  const imageUrl = slide.image.url.startsWith('http')
    ? slide.image.url
    : `${API_BASE_URL}${slide.image.url}`;
  
  return (
    <motion.div
      style={styles.slidePreview}
      whileHover={{ scale: 1.05, boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)' }}
      onClick={onClick}
    >
      <img src={imageUrl} alt={slide.content.title || 'Slide'} style={styles.slidePreviewImage} />
    </motion.div>
  );
};

const GalleryCard = ({ item, onClick }: { item: GalleryItem; onClick?: () => void }) => {
  const imageUrl = item.image_url
    ? item.image_url.startsWith('http')
      ? item.image_url
      : `${API_BASE_URL}${item.image_url}`
    : null;
  
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  
  return (
    <motion.div
      style={styles.galleryCard}
      whileHover={{ y: -4, boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)' }}
      onClick={onClick}
    >
      {imageUrl ? (
        <img src={imageUrl} alt={item.title || 'Item'} style={styles.galleryCardImage} />
      ) : (
        <div style={{ ...styles.galleryCardImage, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '2rem' }}>
          {item.item_type === 'script' ? '📝' : item.item_type === 'prompt' ? '💭' : '📄'}
        </div>
      )}
      <div style={styles.galleryCardContent}>
        <div style={styles.galleryCardTitle}>{item.title || 'Untitled'}</div>
        <div style={styles.galleryCardMeta}>
          <span style={styles.galleryCardType}>{item.item_type}</span>
          <span>{formatDate(item.created_at)}</span>
        </div>
      </div>
    </motion.div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export default function Agent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [inputFocused, setInputFocused] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTools, setActiveTools] = useState<ActiveTool[]>([]);
  const [activeSlidePreviews, setActiveSlidePreviews] = useState<SlidePreviewData[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const [galleryFilter, setGalleryFilter] = useState<GalleryFilterType>('all');
  
  const { items: galleryItems, stats: galleryStats, addSlide } = useGallery();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  
  // Queries
  const { data: _toolsData } = useQuery({
    queryKey: ['agent-tools'],
    queryFn: getAgentTools,
  });
  
  const { data: statusData } = useQuery({
    queryKey: ['agent-status'],
    queryFn: getAgentStatus,
    refetchInterval: 30000,
  });
  
  // Mutations
  const clearMutation = useMutation({
    mutationFn: () => clearAgentSession(sessionId!),
    onSuccess: () => {
      setMessages([]);
      setSessionId(null);
    },
  });
  
  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTools]);
  
  // Filter gallery items
  const filteredGalleryItems = galleryItems.filter((item) => {
    if (galleryFilter === 'all') return true;
    if (galleryFilter === 'slides') return item.item_type === 'slide';
    if (galleryFilter === 'scripts') return item.item_type === 'script' || item.item_type === 'prompt';
    if (galleryFilter === 'drafts') return item.status === 'draft';
    return true;
  });
  
  // Handle streaming response
  const handleStreamEvent = useCallback((event: AgentStreamEvent) => {
    switch (event.type) {
      case 'session':
        setSessionId(event.session_id);
        break;
        
      case 'text':
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant' && last.isStreaming) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + event.text },
            ];
          }
          return prev;
        });
        break;
        
      case 'tool_start':
        setActiveTools((prev) => [
          ...prev,
          { name: event.tool_name, input: event.tool_input, status: 'running' },
        ]);
        break;
        
      case 'tool_result':
        setActiveTools((prev) =>
          prev.map((t) =>
            t.name === event.tool_name && t.status === 'running'
              ? { ...t, status: event.success ? 'complete' : 'error', result: event.result }
              : t
          )
        );
        break;
      
      case 'slide_preview':
        setActiveSlidePreviews((prev) => {
          if (prev.some((s) => s.slide_id === event.slide.slide_id)) {
            return prev;
          }
          // Also add to gallery
          addSlide(event.slide);
          return [...prev, event.slide];
        });
        break;
        
      case 'done':
        setIsStreaming(false);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant') {
            const toolCalls: ToolCall[] = activeTools
              .filter((t) => t.status !== 'running')
              .map((t) => ({
                tool_name: t.name,
                tool_input: t.input,
                result: t.result || {},
                success: t.status === 'complete',
              }));
            return [
              ...prev.slice(0, -1),
              { 
                ...last, 
                isStreaming: false, 
                toolCalls,
                slidePreviews: activeSlidePreviews.length > 0 ? [...activeSlidePreviews] : undefined,
              },
            ];
          }
          return prev;
        });
        setActiveTools([]);
        setActiveSlidePreviews([]);
        break;
        
      case 'error':
        setIsStreaming(false);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant') {
            return [
              ...prev.slice(0, -1),
              { ...last, content: `Error: ${event.message}`, isStreaming: false },
            ];
          }
          return [
            ...prev,
            {
              id: Date.now().toString(),
              role: 'assistant',
              content: `Error: ${event.message}`,
              timestamp: new Date(),
            },
          ];
        });
        setActiveTools([]);
        setActiveSlidePreviews([]);
        break;
    }
  }, [activeTools, activeSlidePreviews, addSlide]);
  
  // Send message
  const sendMessage = useCallback(() => {
    if (!inputValue.trim() || isStreaming) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };
    
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInputValue('');
    setIsStreaming(true);
    setActiveTools([]);
    setActiveSlidePreviews([]);
    
    cleanupRef.current = streamAgentMessage(
      inputValue.trim(),
      sessionId || undefined,
      handleStreamEvent,
      (error) => {
        console.error('Stream error:', error);
        setIsStreaming(false);
      },
      () => {
        setIsStreaming(false);
      }
    );
  }, [inputValue, isStreaming, sessionId, handleStreamEvent]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupRef.current?.();
    };
  }, []);
  
  // Handle keyboard
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  // Suggestion click
  const handleSuggestion = (text: string) => {
    setInputValue(text);
    inputRef.current?.focus();
  };
  
  const suggestions = [
    "Create a slideshow about Stoicism",
    "List my recent projects",
    "Generate a Marcus Aurelius quote slideshow",
    "What content styles are available?",
  ];
  
  return (
    <div style={styles.pageContainer}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}>
            <div style={styles.logoIcon}>🤖</div>
            <span style={styles.logoText}>AI Agent</span>
          </div>
          
          {statusData && (
            <div style={styles.statusBadge}>
              <div style={styles.statusDot} />
              <span style={styles.statusText}>
                {statusData.available_tools} tools ready
              </span>
            </div>
          )}
        </div>
        
        {/* Tabs */}
        <div style={styles.tabs}>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'chat' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('chat')}
          >
            💬 Chat
          </button>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'gallery' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('gallery')}
          >
            📁 Gallery
            {galleryItems.length > 0 && (
              <span style={styles.tabBadge}>{galleryItems.length}</span>
            )}
          </button>
        </div>
        
        <div style={styles.headerActions}>
          {activeTab === 'chat' && sessionId && (
            <motion.button
              style={{ ...styles.actionButton, ...styles.clearButton }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => clearMutation.mutate()}
              disabled={clearMutation.isPending}
            >
              🗑 Clear Chat
            </motion.button>
          )}
        </div>
      </header>
      
      {/* Main Content */}
      <div style={styles.mainContent}>
        <AnimatePresence mode="wait">
          {activeTab === 'chat' ? (
            <motion.div
              key="chat"
              style={styles.chatContainer}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
            >
              {messages.length === 0 ? (
                <div style={styles.emptyState}>
                  <div style={styles.emptyIcon}>🏛️</div>
                  <h2 style={styles.emptyTitle}>Philosophy Content Agent</h2>
                  <p style={styles.emptyText}>
                    I can help you create philosophy-themed TikTok slideshows, manage projects,
                    and set up automations. Powered by Claude.
                  </p>
                  <div style={styles.suggestionChips}>
                    {suggestions.map((s, i) => (
                      <motion.button
                        key={i}
                        style={styles.suggestionChip}
                        whileHover={{ scale: 1.02, background: 'rgba(102, 126, 234, 0.08)' }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleSuggestion(s)}
                      >
                        {s}
                      </motion.button>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={styles.messagesArea}>
                  <div style={styles.messagesInner}>
                    {messages.map((msg) => (
                      <motion.div
                        key={msg.id}
                        style={styles.messageWrapper}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                      >
                        <div style={{ ...styles.avatar, ...(msg.role === 'user' ? styles.userAvatar : styles.assistantAvatar) }}>
                          {msg.role === 'user' ? '👤' : '🤖'}
                        </div>
                        
                        <div style={styles.messageContent}>
                          <div style={styles.messageRole}>
                            {msg.role === 'user' ? 'You' : 'Agent'}
                          </div>
                          
                          <div style={{ ...styles.messageBubble, ...(msg.role === 'user' ? styles.userBubble : styles.assistantBubble) }}>
                            {msg.isStreaming && !msg.content ? (
                              <TypingIndicator />
                            ) : (
                              <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                            )}
                          </div>
                          
                          {/* Slide Previews */}
                          {msg.slidePreviews && msg.slidePreviews.length > 0 && (
                            <div style={styles.slidePreviewsContainer}>
                              {msg.slidePreviews.map((slide) => (
                                <SlidePreviewCard key={slide.slide_id} slide={slide} />
                              ))}
                            </div>
                          )}
                          
                          {/* Tool Calls */}
                          {msg.toolCalls && msg.toolCalls.length > 0 && (
                            <div style={styles.toolsPanel}>
                              {msg.toolCalls.map((tc, i) => (
                                <ToolCallCard key={i} tool={tc} />
                              ))}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                    
                    {/* Active tools while streaming */}
                    {isStreaming && activeTools.length > 0 && (
                      <div style={{ marginLeft: '44px' }}>
                        <div style={styles.toolsPanel}>
                          {activeTools.map((tool, i) => (
                            <ToolCallCard key={i} tool={tool} />
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Active slide previews while streaming */}
                    {isStreaming && activeSlidePreviews.length > 0 && (
                      <div style={{ marginLeft: '44px' }}>
                        <div style={styles.slidePreviewsContainer}>
                          {activeSlidePreviews.map((slide) => (
                            <SlidePreviewCard key={slide.slide_id} slide={slide} />
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div ref={messagesEndRef} />
                  </div>
                </div>
              )}
              
              {/* Input */}
              <div style={styles.inputContainer}>
                <div style={{ ...styles.inputWrapper, ...(inputFocused ? styles.inputWrapperFocused : {}) }}>
                  <textarea
                    ref={inputRef}
                    style={styles.input}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onFocus={() => setInputFocused(true)}
                    onBlur={() => setInputFocused(false)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask me anything about creating philosophy content..."
                    rows={1}
                    disabled={isStreaming}
                  />
                  
                  <motion.button
                    style={{ ...styles.sendButton, ...(isStreaming || !inputValue.trim() ? styles.sendButtonDisabled : {}) }}
                    whileHover={isStreaming || !inputValue.trim() ? {} : { scale: 1.05 }}
                    whileTap={isStreaming || !inputValue.trim() ? {} : { scale: 0.95 }}
                    onClick={sendMessage}
                    disabled={isStreaming || !inputValue.trim()}
                  >
                    {isStreaming ? (
                      <motion.div
                        style={{ width: 16, height: 16, border: '2px solid #fff', borderTopColor: 'transparent', borderRadius: '50%' }}
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      />
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
                        <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                      </svg>
                    )}
                  </motion.button>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="gallery"
              style={styles.galleryContainer}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Gallery Header */}
              <div style={styles.galleryHeader}>
                <div style={styles.galleryFilters}>
                  {(['all', 'slides', 'scripts', 'drafts'] as const).map((filter) => (
                    <button
                      key={filter}
                      style={{
                        ...styles.filterChip,
                        ...(galleryFilter === filter ? styles.filterChipActive : {}),
                      }}
                      onClick={() => setGalleryFilter(filter)}
                    >
                      {filter === 'all' ? '🎨 All' : filter === 'slides' ? '🖼 Slides' : filter === 'scripts' ? '📝 Scripts' : '📋 Drafts'}
                    </button>
                  ))}
                </div>
                
                {galleryStats && (
                  <div style={styles.galleryStats}>
                    <span style={styles.statItem}>
                      <strong>{galleryStats.total}</strong> items
                    </span>
                    <span style={styles.statItem}>
                      <strong>{galleryStats.unique_projects}</strong> projects
                    </span>
                  </div>
                )}
              </div>
              
              {/* Gallery Grid */}
              {filteredGalleryItems.length === 0 ? (
                <div style={styles.galleryEmptyState}>
                  <div style={{ ...styles.emptyIcon, marginBottom: '16px' }}>📭</div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#334155', marginBottom: '8px' }}>
                    No items yet
                  </h3>
                  <p style={{ fontSize: '0.875rem', color: '#64748b', maxWidth: '300px' }}>
                    {galleryFilter === 'all'
                      ? 'Start a conversation to create slides, scripts, and more. Everything you create will appear here.'
                      : `No ${galleryFilter} found. Try a different filter.`}
                  </p>
                </div>
              ) : (
                <div style={styles.galleryGrid}>
                  {filteredGalleryItems.map((item) => (
                    <GalleryCard key={item.id} item={item} />
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
