import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutGrid,
  Image,
  Video,
  Mic,
  Settings,
  FolderOpen,
  Sparkles,
  Zap,
  ChevronRight,
  FileText,
  Timer,
  LogOut,
  Bot,
  Lightbulb,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/', icon: LayoutGrid, label: 'Dashboard', description: 'Overview & quick actions' },
  { to: '/agent', icon: Bot, label: 'AI Agent', description: 'Claude-powered assistant', featured: true },
  { to: '/inspiration', icon: Lightbulb, label: 'Inspiration', description: 'Reference examples' },
  { to: '/projects', icon: FolderOpen, label: 'Projects', description: 'All your creations' },
  { to: '/script-generator', icon: FileText, label: 'Script Generator', description: 'AI-powered scripts' },
  { to: '/static-slideshow', icon: Image, label: 'Static Slideshow', description: 'Image slideshows' },
  { to: '/narrative-slideshow', icon: Mic, label: 'Narrative', description: 'With voiceover' },
  { to: '/video-generator', icon: Video, label: 'Video Gen', description: 'AI transitions' },
  { to: '/automations', icon: Timer, label: 'Automations', description: 'Scheduled recipes' },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', position: 'relative' }}>
      {/* Decorative gradient blobs */}
      <div className="decorative-blob blob-1" />
      <div className="decorative-blob blob-2" />
      <div className="decorative-blob blob-3" />

      {/* Sidebar */}
      <aside style={{
        width: '280px',
        background: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(148, 163, 184, 0.2)',
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        height: '100vh',
        zIndex: 50,
      }}>
        {/* Logo */}
        <div style={{ padding: '24px', borderBottom: '1px solid rgba(148, 163, 184, 0.15)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <motion.div 
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 24px rgba(102, 126, 234, 0.35)',
              }}
              whileHover={{ scale: 1.05, rotate: 5 }}
              transition={{ type: 'spring', stiffness: 400, damping: 10 }}
            >
              <Sparkles size={24} style={{ color: 'white' }} />
            </motion.div>
            <div>
              <h1 style={{ 
                fontWeight: 800, 
                fontSize: '20px', 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>
                Philosophy
              </h1>
              <p style={{ fontSize: '13px', color: '#64748b', fontWeight: 500 }}>Video Generator</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
          <p style={{ 
            fontSize: '11px', 
            fontWeight: 700, 
            color: '#94a3b8', 
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '12px',
            paddingLeft: '12px'
          }}>
            Create
          </p>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {navItems.map((item) => {
              // Check if current path matches this nav item (including sub-routes like /static-slideshow/:id)
              const isActive = item.to === '/' 
                ? location.pathname === '/' 
                : location.pathname.startsWith(item.to);
              return (
                <li key={item.to}>
                  <NavLink to={item.to}>
                    <motion.div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '14px 16px',
                        borderRadius: '14px',
                        textDecoration: 'none',
                        position: 'relative',
                        overflow: 'hidden',
                        background: isActive 
                          ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.1) 100%)'
                          : 'transparent',
                        border: isActive ? '1px solid rgba(102, 126, 234, 0.2)' : '1px solid transparent',
                      }}
                      whileHover={{ 
                        background: isActive 
                          ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.1) 100%)'
                          : 'rgba(102, 126, 234, 0.08)',
                        x: 4
                      }}
                      transition={{ duration: 0.2 }}
                    >
                      <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: isActive 
                          ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                          : 'rgba(148, 163, 184, 0.15)',
                        transition: 'all 0.2s ease',
                      }}>
                        <item.icon size={18} style={{ 
                          color: isActive ? 'white' : '#64748b',
                        }} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <span style={{ 
                          fontWeight: 600, 
                          fontSize: '14px',
                          color: isActive ? '#4f46e5' : '#334155',
                          display: 'block',
                        }}>
                          {item.label}
                        </span>
                        <span style={{
                          fontSize: '11px',
                          color: '#94a3b8',
                          marginTop: '2px',
                          display: 'block',
                        }}>
                          {item.description}
                        </span>
                      </div>
                      {isActive && (
                        <motion.div
                          layoutId="activeIndicator"
                          style={{
                            width: '4px',
                            height: '24px',
                            borderRadius: '2px',
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            position: 'absolute',
                            right: '8px',
                          }}
                        />
                      )}
                    </motion.div>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom section */}
        <div style={{ padding: '16px', borderTop: '1px solid rgba(148, 163, 184, 0.15)' }}>
          <NavLink to="/settings">
            <motion.div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 16px',
                borderRadius: '12px',
                color: '#64748b',
              }}
              whileHover={{ background: 'rgba(102, 126, 234, 0.08)', x: 4 }}
            >
              <Settings size={20} />
              <span style={{ fontWeight: 500, fontSize: '14px' }}>Settings</span>
              <ChevronRight size={16} style={{ marginLeft: 'auto', opacity: 0.5 }} />
            </motion.div>
          </NavLink>
          
          {/* Status indicator */}
          <motion.div 
            style={{
              marginTop: '12px',
              padding: '14px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
              border: '1px solid rgba(34, 197, 94, 0.2)',
            }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <motion.div 
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #22c55e, #10b981)',
                  boxShadow: '0 0 10px rgba(34, 197, 94, 0.5)',
                }}
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <div>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#166534' }}>All Systems Online</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                  <Zap size={10} style={{ color: '#22c55e' }} />
                  <span style={{ fontSize: '11px', color: '#15803d' }}>4 APIs connected</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Logout button */}
          <motion.button
            onClick={handleLogout}
            style={{
              width: '100%',
              marginTop: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: '12px',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              background: 'rgba(239, 68, 68, 0.05)',
              color: '#dc2626',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
            }}
            whileHover={{ 
              background: 'rgba(239, 68, 68, 0.1)',
              borderColor: 'rgba(239, 68, 68, 0.3)',
            }}
            whileTap={{ scale: 0.98 }}
          >
            <LogOut size={18} />
            <span>Sign Out</span>
          </motion.button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ 
        flex: 1, 
        marginLeft: '280px',
        minHeight: '100vh',
      }}>
        <div style={{ padding: '32px 40px', maxWidth: '1400px', margin: '0 auto' }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
