import type { ReactNode, CSSProperties } from 'react';
import { motion } from 'framer-motion';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'solid' | 'gradient' | 'outlined';
  gradient?: 'purple' | 'blue' | 'pink' | 'teal' | 'warm' | 'green' | 'orange';
  style?: CSSProperties;
}

const paddingValues = {
  none: '0',
  sm: '12px',
  md: '16px',
  lg: '24px',
  xl: '32px',
};

const gradientColors = {
  purple: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)',
  blue: 'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(79, 172, 254, 0.08) 100%)',
  pink: 'linear-gradient(135deg, rgba(168, 85, 247, 0.08) 0%, rgba(236, 72, 153, 0.08) 100%)',
  teal: 'linear-gradient(135deg, rgba(20, 184, 166, 0.08) 0%, rgba(56, 239, 125, 0.08) 100%)',
  warm: 'linear-gradient(135deg, rgba(250, 112, 154, 0.08) 0%, rgba(254, 225, 64, 0.08) 100%)',
  green: 'linear-gradient(135deg, rgba(34, 197, 94, 0.08) 0%, rgba(16, 185, 129, 0.08) 100%)',
  orange: 'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(249, 115, 22, 0.08) 100%)',
};

const gradientBorders = {
  purple: 'rgba(102, 126, 234, 0.2)',
  blue: 'rgba(59, 130, 246, 0.2)',
  pink: 'rgba(168, 85, 247, 0.2)',
  teal: 'rgba(20, 184, 166, 0.2)',
  warm: 'rgba(250, 112, 154, 0.2)',
  green: 'rgba(34, 197, 94, 0.2)',
  orange: 'rgba(245, 158, 11, 0.2)',
};

export default function GlassCard({
  children,
  className = '',
  hover = false,
  onClick,
  padding = 'md',
  variant = 'default',
  gradient,
  style,
}: GlassCardProps) {
  const getBackground = () => {
    if (gradient) {
      return gradientColors[gradient];
    }
    switch (variant) {
      case 'solid':
        return 'rgba(255, 255, 255, 0.95)';
      case 'gradient':
        return 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)';
      case 'outlined':
        return 'transparent';
      default:
        return 'rgba(255, 255, 255, 0.7)';
    }
  };

  const getBorder = () => {
    if (gradient) {
      return `1px solid ${gradientBorders[gradient]}`;
    }
    switch (variant) {
      case 'outlined':
        return '2px solid rgba(148, 163, 184, 0.2)';
      default:
        return '1px solid rgba(255, 255, 255, 0.8)';
    }
  };

  const baseStyles: CSSProperties = {
    background: getBackground(),
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    border: getBorder(),
    borderRadius: '20px',
    boxShadow: '0 4px 24px rgba(0, 0, 0, 0.06)',
    padding: paddingValues[padding],
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    ...style,
  };

  if (onClick || hover) {
    return (
      <motion.div
        className={className}
        style={{
          ...baseStyles,
          cursor: onClick ? 'pointer' : 'default',
        }}
        onClick={onClick}
        whileHover={hover || onClick ? { 
          y: -4, 
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.1)',
          borderColor: gradient ? gradientBorders[gradient] : 'rgba(102, 126, 234, 0.3)',
        } : {}}
        whileTap={onClick ? { scale: 0.98 } : {}}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <div className={className} style={baseStyles}>
      {children}
    </div>
  );
}
