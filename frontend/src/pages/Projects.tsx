import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  FolderOpen, 
  Plus, 
  Search,
  Image,
  Video,
  Mic,
  Trash2,
  Clock,
  Layers,
  Filter,
  ArrowRight
} from 'lucide-react';
import { getProjects, deleteProject, getSlideImageUrl } from '../api/client';
import type { Project } from '../api/client';
import GlassCard from '../components/GlassCard';
import Button from '../components/Button';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.4, ease: "easeOut" as const }
  },
};

export default function Projects() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const { data, isLoading } = useQuery({
    queryKey: ['projects', statusFilter, typeFilter],
    queryFn: () => getProjects({ 
      status: statusFilter || undefined, 
      content_type: typeFilter || undefined 
    }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const projects = data?.projects || [];
  const filteredProjects = projects.filter((p: Project) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.topic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getProjectIcon = (contentType: string) => {
    switch (contentType) {
      case 'video':
        return { icon: Video, gradient: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)', shadow: 'rgba(59, 130, 246, 0.3)' };
      case 'narrative':
        return { icon: Mic, gradient: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)', shadow: 'rgba(168, 85, 247, 0.3)' };
      default:
        return { icon: Image, gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', shadow: 'rgba(102, 126, 234, 0.3)' };
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'complete':
        return { bg: 'rgba(34, 197, 94, 0.1)', color: '#16a34a' };
      case 'generating':
        return { bg: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)', color: '#667eea' };
      case 'error':
        return { bg: 'rgba(239, 68, 68, 0.1)', color: '#dc2626' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.1)', color: '#64748b' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
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
            <FolderOpen size={26} style={{ color: 'white' }} />
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
              Projects
            </h1>
            <p style={{ color: '#64748b', marginTop: '4px' }}>
              {data?.total || 0} projects total
            </p>
          </div>
        </div>
        <Link to="/static-slideshow">
          <Button variant="primary" icon={<Plus size={18} />}>
            New Project
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <GlassCard padding="md">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Search */}
          <div style={{ flex: 1, position: 'relative' }}>
            <Search size={18} style={{ 
              position: 'absolute', 
              left: '14px', 
              top: '50%', 
              transform: 'translateY(-50%)', 
              color: '#94a3b8' 
            }} />
            <input
              type="text"
              className="input"
              style={{ paddingLeft: '44px' }}
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Filter size={18} style={{ color: '#64748b' }} />
            
            {/* Status filter */}
            <select
              className="select"
              style={{ width: '160px' }}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Status</option>
              <option value="draft">Draft</option>
              <option value="generating">Generating</option>
              <option value="complete">Complete</option>
            </select>

            {/* Type filter */}
            <select
              className="select"
              style={{ width: '160px' }}
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="">All Types</option>
              <option value="slideshow">Slideshow</option>
              <option value="video">Video</option>
            </select>
          </div>
        </div>
      </GlassCard>

      {/* Projects grid */}
      {isLoading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <GlassCard key={i} padding="lg">
              <div style={{ animation: 'pulse 2s infinite' }}>
                <div style={{ height: '20px', background: 'rgba(148, 163, 184, 0.2)', borderRadius: '8px', width: '75%', marginBottom: '12px' }} />
                <div style={{ height: '16px', background: 'rgba(148, 163, 184, 0.15)', borderRadius: '6px', width: '50%' }} />
              </div>
            </GlassCard>
          ))}
        </div>
      ) : filteredProjects.length > 0 ? (
        <motion.div 
          style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {filteredProjects.map((project: Project) => {
            const iconData = getProjectIcon(project.content_type);
            const IconComponent = iconData.icon;
            const statusStyle = getStatusBadge(project.status);
            
            // Determine if project is complete (all images done)
            const allImagesComplete = project.slides && project.slides.length > 0 && 
              project.slides.every((s: any) => s.image_status === 'complete');
            
            // Route to completed view if complete, otherwise to editor
            const projectLink = allImagesComplete 
              ? `/projects/${project.id}` 
              : `/static-slideshow/${project.id}`;
            
            return (
              <motion.div key={project.id} variants={itemVariants}>
                <GlassCard hover padding="none">
                  <Link to={projectLink} style={{ textDecoration: 'none' }}>
                    <div style={{ padding: '20px' }}>
                      {/* Header */}
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                          <motion.div 
                            style={{
                              width: '48px',
                              height: '48px',
                              borderRadius: '14px',
                              background: iconData.gradient,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              boxShadow: `0 4px 16px ${iconData.shadow}`,
                            }}
                            whileHover={{ scale: 1.05 }}
                          >
                            <IconComponent size={22} style={{ color: 'white' }} />
                          </motion.div>
                          <div>
                            <h3 style={{ fontWeight: 600, color: '#0f172a', fontSize: '16px' }} className="line-clamp-1">
                              {project.name}
                            </h3>
                            <p style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
                              {project.content_type}
                            </p>
                          </div>
                        </div>
                        <span style={{
                          padding: '6px 12px',
                          fontSize: '12px',
                          fontWeight: 600,
                          borderRadius: '16px',
                          background: statusStyle.bg,
                          color: statusStyle.color,
                        }}>
                          {project.status}
                        </span>
                      </div>

                      {/* Preview thumbnails */}
                      {project.slides && project.slides.length > 0 && (
                        <div style={{ display: 'flex', gap: '6px', marginBottom: '16px' }}>
                          {project.slides.slice(0, 4).map((slide: any) => (
                            <div
                              key={slide.id}
                              style={{
                                flex: 1,
                                aspectRatio: '9/16',
                                background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                                borderRadius: '8px',
                                overflow: 'hidden',
                              }}
                            >
                              {slide.final_image_path && (
                                <img
                                  src={getSlideImageUrl(slide.final_image_path) || ''}
                                  alt=""
                                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                />
                              )}
                            </div>
                          ))}
                          {project.slides.length > 4 && (
                            <div style={{
                              flex: 1,
                              aspectRatio: '9/16',
                              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                              borderRadius: '8px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}>
                              <span style={{ fontSize: '12px', fontWeight: 600, color: '#667eea' }}>
                                +{project.slides.length - 4}
                              </span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Stats */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px', color: '#64748b' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Layers size={14} />
                          {project.slide_count} slides
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={14} />
                          {new Date(project.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </Link>

                  {/* Actions */}
                  <div style={{
                    borderTop: '1px solid rgba(148, 163, 184, 0.15)',
                    padding: '12px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'rgba(248, 250, 252, 0.5)',
                  }}>
                    <Link to={projectLink} style={{ 
                      fontSize: '13px', 
                      fontWeight: 600, 
                      color: '#667eea',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}>
                      {allImagesComplete ? 'View Project' : 'Continue Editing'}
                      <ArrowRight size={14} />
                    </Link>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => {
                        if (confirm('Delete this project?')) {
                          deleteMutation.mutate(project.id);
                        }
                      }}
                      icon={<Trash2 size={14} />}
                    >
                      Delete
                    </Button>
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </motion.div>
      ) : (
        <GlassCard padding="xl">
          <div style={{ textAlign: 'center', padding: '48px' }}>
            <motion.div
              style={{
                width: '80px',
                height: '80px',
                borderRadius: '24px',
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 20px',
              }}
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <FolderOpen size={36} style={{ color: '#667eea' }} />
            </motion.div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>No projects found</h3>
            <p style={{ color: '#64748b', marginBottom: '24px' }}>
              {searchQuery || statusFilter || typeFilter
                ? 'Try adjusting your filters'
                : 'Create your first project to get started'}
            </p>
            <Link to="/static-slideshow">
              <Button variant="primary" icon={<Plus size={18} />}>
                Create Project
              </Button>
            </Link>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
