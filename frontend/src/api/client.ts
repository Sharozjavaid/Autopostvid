import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

// API Key for authentication - loaded from environment variable
const API_KEY = import.meta.env.VITE_API_KEY || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY && { 'X-API-Key': API_KEY }),
  },
});

// Also export as apiClient for convenience
export const apiClient = api;

// Log warning in development if no API key is configured
if (!API_KEY && import.meta.env.DEV) {
  console.warn('[API Client] No VITE_API_KEY configured - API calls may fail if backend requires authentication');
}

// Helper to get static image URLs
// Handles both GCS URLs (https://storage.googleapis.com/...) and local paths
export const getSlideImageUrl = (imagePath: string | null, cacheBuster?: number): string | null => {
  if (!imagePath) return null;
  
  // If it's already a full URL (GCS or any https), use it directly
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return cacheBuster ? `${imagePath}?t=${cacheBuster}` : imagePath;
  }
  
  // Otherwise, it's a local path - build the static URL
  const filename = imagePath.split('/').pop();
  const url = `${API_BASE_URL}/static/slides/${filename}`;
  return cacheBuster ? `${url}?t=${cacheBuster}` : url;
};

export const getBackgroundImageUrl = (imagePath: string | null): string | null => {
  if (!imagePath) return null;
  
  // If it's already a full URL (GCS or any https), use it directly
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath;
  }
  
  // Otherwise, it's a local path - build the static URL
  const filename = imagePath.split('/').pop();
  return `${API_BASE_URL}/static/images/${filename}`;
};

// Types
export interface Slide {
  id: string;
  project_id: string;
  order_index: number;
  title: string | null;
  subtitle: string | null;
  visual_description: string | null;
  narration: string | null;
  background_image_path: string | null;
  final_image_path: string | null;
  video_clip_path: string | null;
  current_font: string | null;
  current_theme: string | null;
  current_version: number;
  image_status: 'pending' | 'generating' | 'complete' | 'error';
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  topic: string;
  content_type: string;
  script_style?: string;
  status: string;
  script_approved?: string;
  settings: Record<string, unknown>;
  slides: Slide[];
  slide_count: number;
  created_at: string;
  updated_at: string;
}

export interface Theme {
  id: string;
  name: string;
  description: string;
}

export interface Font {
  id: string;
  name: string;
  style: string;
}

export interface ImageModel {
  id: string;
  name: string;
  provider: string;
}

// API Functions

// Projects
export const getProjects = async (params?: { status?: string; content_type?: string }) => {
  const response = await api.get('/api/projects', { params });
  return response.data;
};

export const getProject = async (projectId: string): Promise<Project> => {
  const response = await api.get(`/api/projects/${projectId}`);
  return response.data;
};

export const createProject = async (data: { name: string; topic: string; content_type: string }) => {
  const response = await api.post('/api/projects', data);
  return response.data;
};

export const updateProject = async (projectId: string, data: Partial<Project>) => {
  const response = await api.put(`/api/projects/${projectId}`, data);
  return response.data;
};

export const deleteProject = async (projectId: string) => {
  await api.delete(`/api/projects/${projectId}`);
};

export const getProjectStats = async (projectId: string) => {
  const response = await api.get(`/api/projects/${projectId}/stats`);
  return response.data;
};

// Scripts
export const generateScript = async (data: {
  topic: string;
  content_type?: string;
  image_style?: string;
  num_slides?: number;
}) => {
  const response = await api.post('/api/scripts/generate', data);
  return response.data;
};

export const getScriptStyles = async () => {
  const response = await api.get('/api/scripts/styles');
  return response.data;
};

export const approveScript = async (projectId: string) => {
  const response = await api.post(`/api/scripts/${projectId}/approve`);
  return response.data;
};

export const regenerateEntireScript = async (projectId: string, newStyle?: string) => {
  const response = await api.post(`/api/scripts/${projectId}/regenerate-all`, null, {
    params: { new_style: newStyle }
  });
  return response.data;
};

export const regenerateSlideScript = async (
  projectId: string,
  slideIndex: number,
  instruction?: string
) => {
  const response = await api.post(
    `/api/scripts/${projectId}/regenerate-slide/${slideIndex}`,
    null,
    { params: { instruction } }
  );
  return response.data;
};

export const updateSlideScript = async (
  projectId: string,
  slideId: string,
  data: {
    title?: string | null;
    subtitle?: string | null;
    visual_description?: string | null;
    narration?: string | null;
  }
) => {
  const response = await api.put(`/api/scripts/${projectId}/slides/${slideId}`, null, {
    params: data,
  });
  return response.data;
};

// Slides
export const getProjectSlides = async (projectId: string): Promise<Slide[]> => {
  const response = await api.get(`/api/slides/project/${projectId}`);
  return response.data;
};

export const createSlide = async (projectId: string, data: Partial<Slide>) => {
  const response = await api.post(`/api/slides/project/${projectId}`, data);
  return response.data;
};

export const updateSlide = async (slideId: string, data: Partial<Slide>) => {
  const response = await api.put(`/api/slides/${slideId}`, data);
  return response.data;
};

export const deleteSlide = async (slideId: string) => {
  await api.delete(`/api/slides/${slideId}`);
};

export const duplicateSlide = async (slideId: string) => {
  const response = await api.post(`/api/slides/${slideId}/duplicate`);
  return response.data;
};

export const reorderSlides = async (projectId: string, slideIds: string[]) => {
  const response = await api.post(`/api/slides/project/${projectId}/reorder`, {
    slide_ids: slideIds,
  });
  return response.data;
};

// Images
export const generateSlideImage = async (
  slideId: string,
  data: { model: string; font?: string; theme?: string }
) => {
  const response = await api.post(`/api/images/generate/${slideId}`, data);
  return response.data;
};

export const generateSlideImageWithOptions = async (
  slideId: string,
  data: { model?: string; font?: string; theme?: string }
) => {
  const response = await api.post(`/api/images/generate/${slideId}`, {
    model: data.model || 'gpt15',
    font: data.font || 'social',
    theme: data.theme || 'golden_dust',
  });
  return response.data;
};

export const generateBatchImages = async (
  projectId: string,
  data: { model: string; font?: string; theme?: string; slide_ids?: string[] }
) => {
  const response = await api.post(`/api/images/generate-batch/${projectId}`, data);
  return response.data;
};

export const deleteSlideImage = async (slideId: string) => {
  const response = await api.delete(`/api/images/${slideId}/image`);
  return response.data;
};

export const reapplyTextOverlay = async (
  slideId: string,
  font: string
): Promise<{ success: boolean; slide_id: string; font: string; final_image_url: string; version?: number }> => {
  const response = await api.post(`/api/images/${slideId}/reapply-text`, null, {
    params: { font }
  });
  return response.data;
};

// Slide Version History
export interface SlideVersion {
  id: string;
  slide_id: string;
  version_number: number;
  title: string | null;
  subtitle: string | null;
  visual_description: string | null;
  narration: string | null;
  font: string | null;
  theme: string | null;
  background_image_path: string | null;
  final_image_path: string | null;
  change_type: string;
  change_description: string | null;
  created_at: string | null;
}

export interface SlideVersionsResponse {
  slide_id: string;
  current_version: number;
  total_versions: number;
  versions: SlideVersion[];
}

export const getSlideVersions = async (slideId: string): Promise<SlideVersionsResponse> => {
  const response = await api.get(`/api/images/${slideId}/versions`);
  return response.data;
};

export const revertToVersion = async (
  slideId: string,
  versionNumber: number
): Promise<{ success: boolean; message: string; slide_id: string; new_version: number }> => {
  const response = await api.post(`/api/images/${slideId}/revert/${versionNumber}`);
  return response.data;
};

// Settings/Models
export const getAvailableModels = async () => {
  const response = await api.get('/api/settings/models');
  return response.data;
};

// Health
export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

// WebSocket connection for progress updates
export const createWebSocket = (projectId: string) => {
  const wsUrl = API_BASE_URL.replace('http', 'ws');
  return new WebSocket(`${wsUrl}/ws/${projectId}`);
};

// Automations
export interface Automation {
  id: string;
  name: string;
  content_type: string;
  image_style: string;
  topics: string[];
  current_topic_index: number;
  schedule_times: string[];
  schedule_days: string[];
  email_enabled: boolean;
  email_address: string | null;
  email_on_complete?: boolean;
  email_on_error?: boolean;
  settings: {
    auto_approve_script?: boolean;
    auto_generate_images?: boolean;
    image_model?: string;
    font?: string;
  };
  status: 'running' | 'stopped' | 'paused';
  is_active: boolean;
  last_run: string | null;
  next_run: string | null;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  created_at: string;
  updated_at?: string;
}

export interface AutomationCreate {
  name: string;
  content_type?: string;
  image_style?: string;
  topics?: string[];
  schedule_times?: string[];
  schedule_days?: string[];
  email_enabled?: boolean;
  email_address?: string;
  settings?: Automation['settings'];
}

export interface AutomationUpdate {
  name?: string;
  content_type?: string;
  image_style?: string;
  topics?: string[];
  schedule_times?: string[];
  schedule_days?: string[];
  email_enabled?: boolean;
  email_address?: string;
  settings?: Automation['settings'];
}

export interface ContentType {
  id: string;
  name: string;
  description: string;
  example: string;
  default_image_style: string;
}

export interface ImageStyle {
  id: string;
  name: string;
  description: string;
}

export const getContentTypes = async (): Promise<ContentType[]> => {
  const response = await api.get('/api/scripts/content-types');
  return response.data.content_types || response.data;
};

export const getImageStyles = async (): Promise<ImageStyle[]> => {
  const response = await api.get('/api/scripts/image-styles');
  return response.data.image_styles || response.data;
};

export const getAutomations = async (): Promise<{ automations: Automation[]; total: number }> => {
  const response = await api.get('/api/automations');
  return response.data;
};

export const getAutomation = async (automationId: string): Promise<Automation> => {
  const response = await api.get(`/api/automations/${automationId}`);
  return response.data;
};

export const createAutomation = async (data: AutomationCreate): Promise<{ success: boolean; automation: Automation }> => {
  const response = await api.post('/api/automations', data);
  return response.data;
};

export const updateAutomation = async (
  automationId: string,
  data: AutomationUpdate
): Promise<{ success: boolean; automation: Automation }> => {
  const response = await api.put(`/api/automations/${automationId}`, data);
  return response.data;
};

export const deleteAutomation = async (automationId: string) => {
  await api.delete(`/api/automations/${automationId}`);
};

export const startAutomation = async (automationId: string) => {
  const response = await api.post(`/api/automations/${automationId}/start`);
  return response.data;
};

export const stopAutomation = async (automationId: string) => {
  const response = await api.post(`/api/automations/${automationId}/stop`);
  return response.data;
};

export const pauseAutomation = async (automationId: string) => {
  const response = await api.post(`/api/automations/${automationId}/pause`);
  return response.data;
};

export const generateAutomationSample = async (automationId: string): Promise<{
  success: boolean;
  preview: boolean;
  topic: string;
  content_type: string;
  image_style: string;
  script: Record<string, unknown>;
  message: string;
}> => {
  const response = await api.post(`/api/automations/${automationId}/sample`);
  return response.data;
};

export const addAutomationTopic = async (automationId: string, topic: string) => {
  const response = await api.post(`/api/automations/${automationId}/topics`, { topic });
  return response.data;
};

export const addAutomationTopicsBulk = async (automationId: string, topics: string[]) => {
  const response = await api.post(`/api/automations/${automationId}/topics/bulk`, { topics });
  return response.data;
};

export const removeAutomationTopic = async (automationId: string, topicIndex: number) => {
  const response = await api.delete(`/api/automations/${automationId}/topics/${topicIndex}`);
  return response.data;
};

export const reorderAutomationTopics = async (automationId: string, topics: string[]) => {
  const response = await api.put(`/api/automations/${automationId}/topics/reorder`, { topics });
  return response.data;
};

// Automation Run History
export interface AutomationRun {
  id: string;
  automation_id: string;
  topic: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'posted';
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  project_id: string | null;
  slides_count: number;
  image_paths: string[];
  script_path: string | null;
  tiktok_posted: boolean;
  tiktok_publish_id: string | null;
  tiktok_post_status: 'pending' | 'processing' | 'success' | 'failed' | null;
  tiktok_error: string | null;
  error_message: string | null;
  settings_used: Record<string, unknown>;
  created_at: string | null;
}

export const getAutomationRuns = async (
  automationId: string,
  limit: number = 20
): Promise<{ automation_id: string; runs: AutomationRun[]; total: number }> => {
  const response = await api.get(`/api/automations/${automationId}/runs`, { params: { limit } });
  return response.data;
};

export const getAutomationRun = async (
  automationId: string,
  runId: string
): Promise<AutomationRun> => {
  const response = await api.get(`/api/automations/${automationId}/runs/${runId}`);
  return response.data;
};

export const retryTikTokPost = async (
  automationId: string,
  runId: string
): Promise<{ success: boolean; message?: string; error?: string; hint?: string; publish_id?: string }> => {
  const response = await api.post(`/api/automations/${automationId}/runs/${runId}/retry-tiktok`);
  return response.data;
};

// =============================================================================
// AGENT API
// =============================================================================

export interface ToolCall {
  tool_name: string;
  tool_input: Record<string, unknown>;
  result: Record<string, unknown>;
  success: boolean;
}

export interface AgentChatResponse {
  session_id: string;
  response: string;
  tool_calls: ToolCall[];
  iterations: number;
  timestamp: string;
  error?: string;
}

export interface AgentHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  tool_calls?: ToolCall[];
}

export interface AgentHistoryResponse {
  session_id: string;
  messages: AgentHistoryMessage[];
  message_count: number;
}

export interface AgentToolInfo {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  category: string;
}

export interface AgentToolsResponse {
  tools: AgentToolInfo[];
  total: number;
  categories: string[];
}

export interface AgentStatusResponse {
  model: string;
  max_tokens: number;
  max_iterations: number;
  active_sessions: number;
  available_tools: number;
}

// Slide preview data from agent tool results
export interface SlidePreviewData {
  slide_id: string;
  slide_index: number;
  project_id: string;
  content: {
    title: string | null;
    subtitle: string | null;
  };
  image: {
    url: string;
    background_url: string | null;
    width: number;
    height: number;
  };
  settings: {
    font: string;
    theme: string;
    model: string;
  };
}

// Agent streaming event types
export type AgentStreamEvent =
  | { type: 'session'; session_id: string }
  | { type: 'text'; text: string }
  | { type: 'thinking'; text: string }
  | { type: 'tool_start'; tool_name: string; tool_input: Record<string, unknown> }
  | { type: 'tool_result'; tool_name: string; result: Record<string, unknown>; success: boolean }
  | { type: 'slide_preview'; slide: SlidePreviewData }
  | { type: 'done'; iterations: number; tool_count: number }
  | { type: 'error'; message: string };

// Agent API Functions

export const sendAgentMessage = async (
  message: string,
  sessionId?: string
): Promise<AgentChatResponse> => {
  const response = await api.post('/api/agent/chat', {
    message,
    session_id: sessionId,
  });
  return response.data;
};

export const streamAgentMessage = (
  message: string,
  sessionId: string | undefined,
  onEvent: (event: AgentStreamEvent) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): (() => void) => {
  const params = new URLSearchParams({ message });
  if (sessionId) params.append('session_id', sessionId);
  // Include API key in query params for SSE (EventSource doesn't support custom headers)
  if (API_KEY) params.append('api_key', API_KEY);
  
  const eventSource = new EventSource(
    `${API_BASE_URL}/api/agent/chat/stream?${params.toString()}`
  );
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent({ type: event.type as AgentStreamEvent['type'], ...data });
    } catch {
      // Handle non-JSON events
    }
  };
  
  // Handle specific event types
  const eventTypes = ['session', 'text', 'thinking', 'tool_start', 'tool_result', 'slide_preview', 'done', 'error'];
  eventTypes.forEach((eventType) => {
    eventSource.addEventListener(eventType, (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        onEvent({ type: eventType as AgentStreamEvent['type'], ...data });
        
        if (eventType === 'done' || eventType === 'error') {
          eventSource.close();
          onComplete?.();
        }
      } catch (e) {
        console.error('Failed to parse event:', e);
      }
    });
  });
  
  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    onError?.(new Error('Connection error'));
    eventSource.close();
  };
  
  // Return cleanup function
  return () => {
    eventSource.close();
  };
};

export const getAgentHistory = async (sessionId: string): Promise<AgentHistoryResponse> => {
  const response = await api.get(`/api/agent/history/${sessionId}`);
  return response.data;
};

export const clearAgentSession = async (sessionId: string) => {
  const response = await api.delete(`/api/agent/session/${sessionId}`);
  return response.data;
};

export const getAgentTools = async (): Promise<AgentToolsResponse> => {
  const response = await api.get('/api/agent/tools');
  return response.data;
};

export const getAgentStatus = async (): Promise<AgentStatusResponse> => {
  const response = await api.get('/api/agent/status');
  return response.data;
};

// =============================================================================
// GALLERY API
// =============================================================================

export interface GalleryItem {
  id: string;
  item_type: 'slide' | 'script' | 'prompt' | 'image' | 'project';
  project_id: string | null;
  slide_id: string | null;
  title: string | null;
  subtitle: string | null;
  description: string | null;
  image_url: string | null;
  thumbnail_url: string | null;
  text_content: string | null;
  font: string | null;
  theme: string | null;
  content_style: string | null;
  metadata: Record<string, unknown> | null;
  status: 'complete' | 'draft' | 'failed';
  session_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface GalleryItemCreate {
  item_type?: string;
  project_id?: string;
  slide_id?: string;
  title?: string;
  subtitle?: string;
  description?: string;
  image_url?: string;
  thumbnail_url?: string;
  text_content?: string;
  font?: string;
  theme?: string;
  content_style?: string;
  metadata?: Record<string, unknown>;
  status?: string;
  session_id?: string;
}

export interface GalleryListResponse {
  items: GalleryItem[];
  total: number;
  has_more: boolean;
}

export interface GalleryStats {
  total: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  unique_projects: number;
}

export const getGalleryItems = async (params?: {
  item_type?: string;
  status?: string;
  project_id?: string;
  limit?: number;
  offset?: number;
}): Promise<GalleryListResponse> => {
  const response = await api.get('/api/gallery', { params });
  return response.data;
};

export const createGalleryItem = async (data: GalleryItemCreate): Promise<GalleryItem> => {
  const response = await api.post('/api/gallery', data);
  return response.data;
};

export const getGalleryItem = async (itemId: string): Promise<GalleryItem> => {
  const response = await api.get(`/api/gallery/${itemId}`);
  return response.data;
};

export const updateGalleryItem = async (
  itemId: string,
  data: Partial<GalleryItem>
): Promise<GalleryItem> => {
  const response = await api.put(`/api/gallery/${itemId}`, data);
  return response.data;
};

export const deleteGalleryItem = async (itemId: string): Promise<void> => {
  await api.delete(`/api/gallery/${itemId}`);
};

export const clearGallery = async (): Promise<{ success: boolean; deleted: number }> => {
  const response = await api.delete('/api/gallery');
  return response.data;
};

export const getGalleryStats = async (): Promise<GalleryStats> => {
  const response = await api.get('/api/gallery/stats/summary');
  return response.data;
};

// ============================================================================
// Cloud Storage API (Media Library)
// ============================================================================

export interface StorageItem {
  name: string;
  url: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  folder: string;
  created_at: string | null;
}

export interface StorageListResponse {
  items: StorageItem[];
  total: number;
  folder: string;
}

export interface StorageStats {
  available: boolean;
  bucket?: string;
  total_files: number;
  total_size_mb: number;
  folders: Record<string, { count: number; size: number }>;
  public_url?: string;
  error?: string;
}

export const browseStorage = async (params?: {
  folder?: string;
  file_type?: 'video' | 'image' | 'audio';
  limit?: number;
}): Promise<StorageListResponse> => {
  const response = await api.get('/api/storage/browse', { params });
  return response.data;
};

export const getStorageVideos = async (limit?: number): Promise<StorageListResponse> => {
  const response = await api.get('/api/storage/videos', { params: { limit } });
  return response.data;
};

export const getStorageImages = async (limit?: number): Promise<StorageListResponse> => {
  const response = await api.get('/api/storage/images', { params: { limit } });
  return response.data;
};

export const getStorageSlides = async (limit?: number): Promise<StorageListResponse> => {
  const response = await api.get('/api/storage/slides', { params: { limit } });
  return response.data;
};

export const getStorageStats = async (): Promise<StorageStats> => {
  const response = await api.get('/api/storage/stats');
  return response.data;
};

export const getStorageFolders = async (): Promise<{ folders: string[]; bucket?: string; public_url?: string }> => {
  const response = await api.get('/api/storage/folders');
  return response.data;
};

export default api;
