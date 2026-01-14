import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  Image, 
  Video, 
  Mic, 
  FolderOpen,
  CheckCircle,
  ArrowRight,
  Sparkles,
  Zap,
  TrendingUp,
  Clock,
  Star
} from 'lucide-react';
import { getProjects, healthCheck } from '../api/client';
import Button from '../components/Button';
import GlassCard from '../components/GlassCard';

const workflowCards = [
  {
    id: 'static-slideshow',
    title: 'Static Slideshow',
    description: 'Create perfect slideshows with AI-generated images and text overlays.',
    icon: Image,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    shadowColor: 'rgba(102, 126, 234, 0.4)',
    bgGradient: 'rgba(102, 126, 234, 0.08)',
    path: '/static-slideshow',
    features: ['Script generation', 'Image iteration', 'Text overlay', 'Export as images'],
    popular: true,
  },
  {
    id: 'narrative-slideshow',
    title: 'Narrative Slideshow',
    description: 'Add ElevenLabs voiceover to your slideshows for storytelling.',
    icon: Mic,
    gradient: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
    shadowColor: 'rgba(168, 85, 247, 0.4)',
    bgGradient: 'rgba(168, 85, 247, 0.08)',
    path: '/narrative-slideshow',
    features: ['AI narration script', 'ElevenLabs voice', 'Timed transitions', 'Video export'],
    popular: false,
  },
  {
    id: 'video-generator',
    title: 'Image-to-Video',
    description: 'Transform static images into dynamic videos with AI transitions.',
    icon: Video,
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
    shadowColor: 'rgba(59, 130, 246, 0.4)',
    bgGradient: 'rgba(59, 130, 246, 0.08)',
    path: '/video-generator',
    features: ['AI video transitions', 'Motion effects', 'Narration sync', 'HD export'],
    popular: false,
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const }
  },
};

export default function Dashboard() {
  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects({}),
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  });

  const recentProjects = (projectsData?.projects || []).slice(0, 5);
  const totalProjects = projectsData?.total || 0;

  return (
    <motion.div 
      style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Hero Header */}
      <motion.div variants={itemVariants}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'flex-start', 
          justifyContent: 'space-between',
          marginBottom: '8px',
        }}>
          <div>
            <motion.div
              style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <motion.div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '18px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.4)',
                }}
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
              >
                <Sparkles size={28} style={{ color: 'white' }} />
              </motion.div>
              <div>
                <h1 style={{ 
                  fontSize: '36px', 
                  fontWeight: 800, 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  marginBottom: '4px',
                }}>
                  Philosophy Video Generator
                </h1>
                <p style={{ color: '#64748b', fontSize: '16px' }}>
                  Create stunning philosophy content with AI
                </p>
              </div>
            </motion.div>
          </div>
          <Link to="/projects">
            <Button variant="secondary" icon={<FolderOpen size={18} />}>
              View All Projects
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Stats Row */}
      <motion.div variants={itemVariants}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
          {/* Projects stat */}
          <GlassCard gradient="purple" padding="lg">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <FolderOpen size={22} style={{ color: 'white' }} />
              </div>
              <div>
                <p style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a' }}>{totalProjects}</p>
                <p style={{ fontSize: '13px', color: '#64748b', fontWeight: 500 }}>Total Projects</p>
              </div>
            </div>
          </GlassCard>

          {/* API Status */}
          <GlassCard gradient="teal" padding="lg">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <Zap size={22} style={{ color: 'white' }} />
              </div>
              <div>
                <p style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a' }}>
                  {Object.values(health?.services || {}).filter(Boolean).length || 0}
                </p>
                <p style={{ fontSize: '13px', color: '#64748b', fontWeight: 500 }}>APIs Connected</p>
              </div>
            </div>
          </GlassCard>

          {/* Completed */}
          <GlassCard gradient="blue" padding="lg">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <CheckCircle size={22} style={{ color: 'white' }} />
              </div>
              <div>
                <p style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a' }}>
                  {(projectsData?.projects || []).filter((p: any) => p.status === 'complete').length}
                </p>
                <p style={{ fontSize: '13px', color: '#64748b', fontWeight: 500 }}>Completed</p>
              </div>
            </div>
          </GlassCard>

          {/* Trending */}
          <GlassCard gradient="pink" padding="lg">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <TrendingUp size={22} style={{ color: 'white' }} />
              </div>
              <div>
                <p style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a' }}>100%</p>
                <p style={{ fontSize: '13px', color: '#64748b', fontWeight: 500 }}>Success Rate</p>
              </div>
            </div>
          </GlassCard>
        </div>
      </motion.div>

      {/* Workflow Cards */}
      <motion.div variants={itemVariants}>
        <div style={{ marginBottom: '20px' }}>
          <h2 style={{ 
            fontSize: '22px', 
            fontWeight: 700, 
            color: '#0f172a',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}>
            <span style={{
              width: '4px',
              height: '24px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '2px',
            }} />
            Choose Your Workflow
          </h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
          {workflowCards.map((card, index) => (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.1 }}
            >
              <Link to={card.path} style={{ textDecoration: 'none' }}>
                <motion.div
                  style={{
                    background: 'rgba(255, 255, 255, 0.8)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255, 255, 255, 0.8)',
                    borderRadius: '24px',
                    padding: '28px',
                    height: '100%',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                  whileHover={{ 
                    y: -8,
                    boxShadow: `0 20px 50px ${card.shadowColor}`,
                    borderColor: card.shadowColor,
                  }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Popular badge */}
                  {card.popular && (
                    <div style={{
                      position: 'absolute',
                      top: '16px',
                      right: '16px',
                      background: card.gradient,
                      padding: '6px 12px',
                      borderRadius: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}>
                      <Star size={12} style={{ color: 'white' }} fill="white" />
                      <span style={{ fontSize: '11px', fontWeight: 600, color: 'white' }}>Popular</span>
                    </div>
                  )}

                  {/* Icon */}
                  <motion.div
                    style={{
                      width: '60px',
                      height: '60px',
                      borderRadius: '18px',
                      background: card.gradient,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: '20px',
                      boxShadow: `0 8px 24px ${card.shadowColor}`,
                    }}
                    whileHover={{ scale: 1.1, rotate: 5 }}
                  >
                    <card.icon size={28} style={{ color: 'white' }} />
                  </motion.div>

                  {/* Content */}
                  <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '10px', color: '#0f172a' }}>
                    {card.title}
                  </h3>
                  <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px', lineHeight: 1.6 }}>
                    {card.description}
                  </p>

                  {/* Features */}
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
                    {card.features.map((feature) => (
                      <li key={feature} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#64748b' }}>
                        <CheckCircle size={14} style={{ color: card.shadowColor.replace('0.4', '1') }} />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {/* CTA */}
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px', 
                    fontSize: '15px', 
                    fontWeight: 600,
                    background: card.gradient,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}>
                    Get Started
                    <ArrowRight size={18} style={{ color: card.shadowColor.replace('0.4', '1') }} />
                  </div>
                </motion.div>
              </Link>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Recent Projects */}
      <motion.div variants={itemVariants}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ 
            fontSize: '22px', 
            fontWeight: 700, 
            color: '#0f172a',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}>
            <span style={{
              width: '4px',
              height: '24px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '2px',
            }} />
            Recent Projects
          </h2>
          <Link to="/projects" style={{ 
            fontSize: '14px', 
            fontWeight: 600,
            color: '#667eea',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}>
            View all
            <ArrowRight size={16} />
          </Link>
        </div>
        
        {recentProjects.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {recentProjects.map((project: any, index: number) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * index }}
              >
                <Link to={`/static-slideshow/${project.id}`} style={{ textDecoration: 'none' }}>
                  <GlassCard hover padding="lg">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '14px',
                          background: project.content_type === 'video' 
                            ? 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)'
                            : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}>
                          {project.content_type === 'video' ? (
                            <Video size={22} style={{ color: 'white' }} />
                          ) : (
                            <Image size={22} style={{ color: 'white' }} />
                          )}
                        </div>
                        <div>
                          <h4 style={{ fontWeight: 600, color: '#0f172a', fontSize: '16px' }}>{project.name}</h4>
                          <p style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
                            {project.slide_count} slides • {project.content_type}
                          </p>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <span style={{
                          padding: '6px 14px',
                          fontSize: '12px',
                          fontWeight: 600,
                          borderRadius: '20px',
                          background: project.status === 'complete' 
                            ? 'rgba(34, 197, 94, 0.1)' 
                            : 'rgba(102, 126, 234, 0.1)',
                          color: project.status === 'complete' ? '#16a34a' : '#667eea',
                        }}>
                          {project.status}
                        </span>
                        <span style={{ fontSize: '13px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={14} />
                          {new Date(project.updated_at).toLocaleDateString()}
                        </span>
                        <ArrowRight size={18} style={{ color: '#94a3b8' }} />
                      </div>
                    </div>
                  </GlassCard>
                </Link>
              </motion.div>
            ))}
          </div>
        ) : (
          <GlassCard padding="xl">
            <div style={{ textAlign: 'center', padding: '32px' }}>
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
              <p style={{ color: '#64748b', fontSize: '16px', marginBottom: '8px' }}>No projects yet</p>
              <p style={{ fontSize: '14px', color: '#94a3b8' }}>
                Choose a workflow above to create your first project
              </p>
            </div>
          </GlassCard>
        )}
      </motion.div>
    </motion.div>
  );
}
