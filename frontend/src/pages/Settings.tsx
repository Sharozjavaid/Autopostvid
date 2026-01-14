import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { 
  Settings as SettingsIcon, 
  Key, 
  Palette,
  Image,
  Check,
  AlertCircle,
  Zap,
  Sparkles,
  Type
} from 'lucide-react';
import { healthCheck, getAvailableModels } from '../api/client';
import GlassCard from '../components/GlassCard';

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
    transition: { duration: 0.4, ease: "easeOut" as const }
  },
};

export default function Settings() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  });

  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: getAvailableModels,
  });

  const apiServices = [
    { 
      id: 'gemini', 
      name: 'Google Gemini', 
      description: 'Script generation and content AI',
      connected: health?.services?.gemini,
      envVar: 'GOOGLE_API_KEY',
      gradient: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
    },
    { 
      id: 'elevenlabs', 
      name: 'ElevenLabs', 
      description: 'Voice synthesis for narration',
      connected: health?.services?.elevenlabs,
      envVar: 'ELEVENLABS_API_KEY',
      gradient: 'linear-gradient(135deg, #a855f7 0%, #7c3aed 100%)',
    },
    { 
      id: 'fal', 
      name: 'fal.ai', 
      description: 'GPT Image 1.5, Flux, and Helix video',
      connected: health?.services?.fal,
      envVar: 'FAL_KEY',
      gradient: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
    },
    { 
      id: 'openai', 
      name: 'OpenAI', 
      description: 'DALL-E 3 image generation',
      connected: health?.services?.openai,
      envVar: 'OPENAI_API_KEY',
      gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    },
  ];

  return (
    <motion.div 
      style={{ display: 'flex', flexDirection: 'column', gap: '32px', maxWidth: '900px' }}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
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
            <SettingsIcon size={26} style={{ color: 'white' }} />
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
              Settings
            </h1>
            <p style={{ color: '#64748b', marginTop: '4px' }}>
              Configure API connections and preferences
            </p>
          </div>
        </div>
      </motion.div>

      {/* API Connections */}
      <motion.div variants={itemVariants}>
        <GlassCard padding="lg">
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px' }}>
            <motion.div 
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              whileHover={{ scale: 1.05 }}
            >
              <Key size={22} style={{ color: '#667eea' }} />
            </motion.div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>API Connections</h2>
              <p style={{ fontSize: '14px', color: '#64748b', marginTop: '2px' }}>
                Status of connected services
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {apiServices.map((service, index) => (
              <motion.div
                key={service.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '18px 20px',
                  background: 'rgba(248, 250, 252, 0.8)',
                  borderRadius: '16px',
                  border: '1px solid rgba(148, 163, 184, 0.15)',
                }}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ borderColor: service.connected ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <motion.div 
                    style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: service.connected 
                        ? 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)'
                        : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                      boxShadow: service.connected 
                        ? '0 0 12px rgba(34, 197, 94, 0.5)'
                        : '0 0 12px rgba(239, 68, 68, 0.5)',
                    }}
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                  <div>
                    <h3 style={{ fontWeight: 600, color: '#0f172a', fontSize: '15px' }}>{service.name}</h3>
                    <p style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>{service.description}</p>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <code style={{
                    fontSize: '12px',
                    background: 'white',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    color: '#64748b',
                    fontFamily: 'monospace',
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                  }}>
                    {service.envVar}
                  </code>
                  {service.connected ? (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 14px',
                      fontSize: '12px',
                      fontWeight: 600,
                      borderRadius: '20px',
                      background: 'rgba(34, 197, 94, 0.1)',
                      color: '#16a34a',
                    }}>
                      <Check size={14} /> Connected
                    </span>
                  ) : (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 14px',
                      fontSize: '12px',
                      fontWeight: 600,
                      borderRadius: '20px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      color: '#dc2626',
                    }}>
                      <AlertCircle size={14} /> Not configured
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>

          <div style={{
            marginTop: '20px',
            padding: '16px 20px',
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)',
            borderRadius: '12px',
            border: '1px solid rgba(102, 126, 234, 0.15)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <Zap size={16} style={{ color: '#667eea' }} />
              <strong style={{ color: '#667eea', fontSize: '14px' }}>Configuration Tip</strong>
            </div>
            <p style={{ fontSize: '13px', color: '#475569', lineHeight: 1.6 }}>
              API keys are configured via environment variables in the backend.
              Create a <code style={{ background: 'white', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>.env</code> file in the project root with your API keys.
            </p>
          </div>
        </GlassCard>
      </motion.div>

      {/* Available Models */}
      <motion.div variants={itemVariants}>
        <GlassCard padding="lg">
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px' }}>
            <motion.div 
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              whileHover={{ scale: 1.05 }}
            >
              <Image size={22} style={{ color: '#3b82f6' }} />
            </motion.div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>Image Models</h2>
              <p style={{ fontSize: '14px', color: '#64748b', marginTop: '2px' }}>
                Available image generation models
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
            {models?.image_models?.map((model: any, index: number) => (
              <motion.div
                key={model.id}
                style={{
                  padding: '18px',
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)',
                  borderRadius: '14px',
                  border: '1px solid rgba(59, 130, 246, 0.15)',
                }}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ borderColor: 'rgba(59, 130, 246, 0.4)', y: -2 }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <Sparkles size={16} style={{ color: '#3b82f6' }} />
                  <h3 style={{ fontWeight: 600, color: '#0f172a', fontSize: '14px' }}>{model.name}</h3>
                </div>
                <p style={{ fontSize: '12px', color: '#64748b' }}>Provider: {model.provider}</p>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      </motion.div>

      {/* Fonts */}
      <motion.div variants={itemVariants}>
        <GlassCard padding="lg">
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px' }}>
            <motion.div 
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              whileHover={{ scale: 1.05 }}
            >
              <Type size={22} style={{ color: '#a855f7' }} />
            </motion.div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>Font Styles</h2>
              <p style={{ fontSize: '14px', color: '#64748b', marginTop: '2px' }}>
                Available fonts for text overlays
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px' }}>
            {models?.fonts?.map((font: any, index: number) => (
              <motion.div
                key={font.id}
                style={{
                  padding: '16px',
                  background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)',
                  borderRadius: '12px',
                  border: '1px solid rgba(168, 85, 247, 0.15)',
                  textAlign: 'center',
                }}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                whileHover={{ borderColor: 'rgba(168, 85, 247, 0.4)', y: -2 }}
              >
                <p style={{ fontWeight: 600, color: '#0f172a', fontSize: '14px' }}>{font.name}</p>
                <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>{font.style}</p>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      </motion.div>

      {/* Themes */}
      <motion.div variants={itemVariants}>
        <GlassCard padding="lg">
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px' }}>
            <motion.div 
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(249, 115, 22, 0.15) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              whileHover={{ scale: 1.05 }}
            >
              <Palette size={22} style={{ color: '#ec4899' }} />
            </motion.div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>Visual Themes</h2>
              <p style={{ fontSize: '14px', color: '#64748b', marginTop: '2px' }}>
                Pre-configured visual styles
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
            {models?.themes?.map((theme: any, index: number) => (
              <motion.div
                key={theme.id}
                style={{
                  padding: '18px',
                  background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.05) 0%, rgba(249, 115, 22, 0.05) 100%)',
                  borderRadius: '14px',
                  border: '1px solid rgba(236, 72, 153, 0.15)',
                }}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ borderColor: 'rgba(236, 72, 153, 0.4)', y: -2 }}
              >
                <h3 style={{ fontWeight: 600, color: '#0f172a', fontSize: '14px' }}>{theme.name}</h3>
                <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px', fontFamily: 'monospace' }}>{theme.id}</p>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      </motion.div>

      {/* About */}
      <motion.div variants={itemVariants}>
        <GlassCard gradient="purple" padding="lg">
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', marginBottom: '16px' }}>About</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
            <div style={{ padding: '14px', background: 'white', borderRadius: '12px' }}>
              <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Version</p>
              <p style={{ fontWeight: 600, color: '#0f172a' }}>2.0.0</p>
            </div>
            <div style={{ padding: '14px', background: 'white', borderRadius: '12px' }}>
              <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Frontend</p>
              <p style={{ fontWeight: 600, color: '#0f172a' }}>React + Vite + TypeScript</p>
            </div>
            <div style={{ padding: '14px', background: 'white', borderRadius: '12px' }}>
              <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Backend</p>
              <p style={{ fontWeight: 600, color: '#0f172a' }}>FastAPI + SQLite</p>
            </div>
            <div style={{ padding: '14px', background: 'white', borderRadius: '12px' }}>
              <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>AI Services</p>
              <p style={{ fontWeight: 600, color: '#0f172a' }}>Gemini, ElevenLabs, fal.ai</p>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </motion.div>
  );
}
