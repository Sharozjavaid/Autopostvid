import type { ReactNode, CSSProperties, MouseEvent } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface ButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'gradient-purple' | 'gradient-blue' | 'gradient-pink';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  disabled?: boolean;
  className?: string;
  onClick?: (e?: MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  style?: CSSProperties;
  fullWidth?: boolean;
}

const variantStyles: Record<string, CSSProperties> = {
  primary: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    boxShadow: '0 4px 20px rgba(102, 126, 234, 0.4)',
  },
  'gradient-purple': {
    background: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
    color: 'white',
    border: 'none',
    boxShadow: '0 4px 20px rgba(168, 85, 247, 0.4)',
  },
  'gradient-blue': {
    background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
    color: 'white',
    border: 'none',
    boxShadow: '0 4px 20px rgba(59, 130, 246, 0.4)',
  },
  'gradient-pink': {
    background: 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)',
    color: 'white',
    border: 'none',
    boxShadow: '0 4px 20px rgba(236, 72, 153, 0.4)',
  },
  secondary: {
    background: 'rgba(255, 255, 255, 0.8)',
    color: '#334155',
    border: '1px solid rgba(148, 163, 184, 0.3)',
    backdropFilter: 'blur(10px)',
  },
  ghost: {
    background: 'transparent',
    color: '#64748b',
    border: 'none',
  },
  danger: {
    background: 'rgba(239, 68, 68, 0.1)',
    color: '#dc2626',
    border: '1px solid rgba(239, 68, 68, 0.2)',
  },
  success: {
    background: 'rgba(34, 197, 94, 0.1)',
    color: '#16a34a',
    border: '1px solid rgba(34, 197, 94, 0.2)',
  },
};

const sizeStyles: Record<string, CSSProperties> = {
  sm: {
    padding: '8px 14px',
    fontSize: '13px',
    borderRadius: '10px',
    gap: '6px',
  },
  md: {
    padding: '12px 20px',
    fontSize: '14px',
    borderRadius: '12px',
    gap: '8px',
  },
  lg: {
    padding: '16px 28px',
    fontSize: '16px',
    borderRadius: '14px',
    gap: '10px',
  },
};

const getHoverVariant = (variant: string) => {
  switch (variant) {
    case 'primary':
      return { y: -2, boxShadow: '0 8px 30px rgba(102, 126, 234, 0.5)', scale: 1.02 };
    case 'gradient-purple':
      return { y: -2, boxShadow: '0 8px 30px rgba(168, 85, 247, 0.5)', scale: 1.02 };
    case 'gradient-blue':
      return { y: -2, boxShadow: '0 8px 30px rgba(59, 130, 246, 0.5)', scale: 1.02 };
    case 'gradient-pink':
      return { y: -2, boxShadow: '0 8px 30px rgba(236, 72, 153, 0.5)', scale: 1.02 };
    case 'secondary':
      return { y: -1, boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)' };
    case 'ghost':
      return { scale: 1.02 };
    case 'danger':
      return { scale: 1.01 };
    case 'success':
      return { scale: 1.01 };
    default:
      return { scale: 1.02 };
  }
};

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  disabled,
  className = '',
  onClick,
  type = 'button',
  style,
  fullWidth = false,
}: ButtonProps) {
  const isDisabled = disabled || loading;

  const baseStyle: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 600,
    cursor: isDisabled ? 'not-allowed' : 'pointer',
    outline: 'none',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    opacity: isDisabled ? 0.6 : 1,
    width: fullWidth ? '100%' : 'auto',
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...style,
  };

  return (
    <motion.button
      type={type}
      className={className}
      style={baseStyle}
      disabled={isDisabled}
      whileHover={!isDisabled ? getHoverVariant(variant) : undefined}
      whileTap={!isDisabled ? { scale: 0.98 } : undefined}
      onClick={onClick}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} className="animate-spin" />
      ) : (
        icon && iconPosition === 'left' && icon
      )}
      {children}
      {!loading && icon && iconPosition === 'right' && icon}
    </motion.button>
  );
}
