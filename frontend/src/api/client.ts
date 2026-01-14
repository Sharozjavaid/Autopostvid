import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Also export as apiClient for convenience
export const apiClient = api;

// Helper to get static image URLs
export const getSlideImageUrl = (imagePath: string | null, cacheBuster?: number): string | null => {
  if (!imagePath) return null;
  const filename = imagePath.split('/').pop();
  const url = `${API_BASE_URL}/static/slides/${filename}`;
  return cacheBuster ? `${url}?t=${cacheBuster}` : url;
};

export const getBackgroundImageUrl = (imagePath: string | null): string | null => {
  if (!imagePath) return null;
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

export default api;
