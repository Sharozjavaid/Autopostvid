import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getGalleryItems,
  createGalleryItem,
  deleteGalleryItem,
  clearGallery as clearGalleryApi,
  getGalleryStats,
  type GalleryItem,
  type GalleryItemCreate,
  type GalleryStats,
  type SlidePreviewData,
} from '../api/client';

interface GalleryContextType {
  items: GalleryItem[];
  stats: GalleryStats | null;
  isLoading: boolean;
  error: Error | null;
  addItem: (item: GalleryItemCreate) => Promise<GalleryItem>;
  addSlide: (slide: SlidePreviewData) => Promise<GalleryItem>;
  removeItem: (itemId: string) => Promise<void>;
  hasItem: (itemId: string) => boolean;
  clearGallery: () => Promise<void>;
  getItemsByProject: (projectId: string) => GalleryItem[];
  getItemsByType: (type: GalleryItem['item_type']) => GalleryItem[];
  refetch: () => void;
}

const GalleryContext = createContext<GalleryContextType | null>(null);

export function GalleryProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  
  // Fetch gallery items from API
  const { data: galleryData, isLoading, error, refetch } = useQuery({
    queryKey: ['gallery-items'],
    queryFn: () => getGalleryItems({ limit: 200 }),
    staleTime: 30000, // 30 seconds
  });
  
  // Fetch gallery stats
  const { data: statsData } = useQuery({
    queryKey: ['gallery-stats'],
    queryFn: getGalleryStats,
    staleTime: 60000, // 1 minute
  });
  
  const items = galleryData?.items || [];
  const stats = statsData || null;
  
  // Create item mutation
  const createMutation = useMutation({
    mutationFn: createGalleryItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-items'] });
      queryClient.invalidateQueries({ queryKey: ['gallery-stats'] });
    },
  });
  
  // Delete item mutation
  const deleteMutation = useMutation({
    mutationFn: deleteGalleryItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-items'] });
      queryClient.invalidateQueries({ queryKey: ['gallery-stats'] });
    },
  });
  
  // Clear gallery mutation
  const clearMutation = useMutation({
    mutationFn: clearGalleryApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-items'] });
      queryClient.invalidateQueries({ queryKey: ['gallery-stats'] });
    },
  });
  
  const addItem = useCallback(async (item: GalleryItemCreate): Promise<GalleryItem> => {
    return createMutation.mutateAsync(item);
  }, [createMutation]);
  
  // Helper to add a slide preview from agent
  const addSlide = useCallback(async (slide: SlidePreviewData): Promise<GalleryItem> => {
    // Check if already exists
    const existing = items.find((i) => i.slide_id === slide.slide_id);
    if (existing) {
      return existing;
    }
    
    return createMutation.mutateAsync({
      item_type: 'slide',
      project_id: slide.project_id,
      slide_id: slide.slide_id,
      title: slide.content.title || `Slide ${slide.slide_index + 1}`,
      subtitle: slide.content.subtitle,
      image_url: slide.image.url,
      font: slide.settings.font,
      theme: slide.settings.theme,
      content_style: slide.settings.model,
      metadata: {
        slide_index: slide.slide_index,
        image_width: slide.image.width,
        image_height: slide.image.height,
        background_url: slide.image.background_url,
      },
      status: 'complete',
    });
  }, [createMutation, items]);
  
  const removeItem = useCallback(async (itemId: string): Promise<void> => {
    await deleteMutation.mutateAsync(itemId);
  }, [deleteMutation]);
  
  const hasItem = useCallback((itemId: string): boolean => {
    return items.some((i) => i.id === itemId || i.slide_id === itemId);
  }, [items]);
  
  const clearGallery = useCallback(async (): Promise<void> => {
    await clearMutation.mutateAsync();
  }, [clearMutation]);
  
  const getItemsByProject = useCallback((projectId: string): GalleryItem[] => {
    return items.filter((i) => i.project_id === projectId);
  }, [items]);
  
  const getItemsByType = useCallback((type: GalleryItem['item_type']): GalleryItem[] => {
    return items.filter((i) => i.item_type === type);
  }, [items]);
  
  return (
    <GalleryContext.Provider value={{
      items,
      stats,
      isLoading,
      error: error as Error | null,
      addItem,
      addSlide,
      removeItem,
      hasItem,
      clearGallery,
      getItemsByProject,
      getItemsByType,
      refetch,
    }}>
      {children}
    </GalleryContext.Provider>
  );
}

export function useGallery() {
  const context = useContext(GalleryContext);
  if (!context) {
    throw new Error('useGallery must be used within a GalleryProvider');
  }
  return context;
}

// Re-export types
export type { GalleryItem, GalleryItemCreate, GalleryStats };
