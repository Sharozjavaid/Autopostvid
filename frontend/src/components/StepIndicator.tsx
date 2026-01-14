import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

interface Step {
  id: string;
  label: string;
  description?: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  onStepClick?: (stepIndex: number) => void;
  variant?: 'default' | 'purple' | 'blue';
}

const gradientColors = {
  default: {
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    shadow: 'rgba(102, 126, 234, 0.4)',
    bg: 'rgba(102, 126, 234, 0.1)',
    text: '#667eea',
  },
  purple: {
    gradient: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
    shadow: 'rgba(168, 85, 247, 0.4)',
    bg: 'rgba(168, 85, 247, 0.1)',
    text: '#a855f7',
  },
  blue: {
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
    shadow: 'rgba(59, 130, 246, 0.4)',
    bg: 'rgba(59, 130, 246, 0.1)',
    text: '#3b82f6',
  },
};

export default function StepIndicator({ 
  steps, 
  currentStep, 
  onStepClick,
  variant = 'default',
}: StepIndicatorProps) {
  const colors = gradientColors[variant];

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      gap: '8px',
      padding: '8px 0',
    }}>
      {steps.map((step, index) => {
        const isComplete = index < currentStep;
        const isCurrent = index === currentStep;
        const isClickable = onStepClick && index <= currentStep;

        return (
          <div key={step.id} style={{ display: 'flex', alignItems: 'center' }}>
            {/* Step circle */}
            <motion.button
              onClick={() => isClickable && onStepClick(index)}
              disabled={!isClickable}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '44px',
                height: '44px',
                borderRadius: '14px',
                border: 'none',
                cursor: isClickable ? 'pointer' : 'default',
                background: isComplete 
                  ? colors.gradient
                  : isCurrent 
                    ? colors.bg
                    : 'rgba(148, 163, 184, 0.1)',
                boxShadow: isComplete 
                  ? `0 4px 16px ${colors.shadow}`
                  : 'none',
                outline: isCurrent ? `2px solid ${colors.text}` : 'none',
                outlineOffset: '2px',
              }}
              whileHover={isClickable ? { scale: 1.08, y: -2 } : {}}
              whileTap={isClickable ? { scale: 0.95 } : {}}
              transition={{ type: 'spring', stiffness: 400, damping: 17 }}
            >
              {isComplete ? (
                <motion.div
                  initial={{ scale: 0, rotate: -45 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 20 }}
                >
                  <Check size={20} strokeWidth={3} style={{ color: 'white' }} />
                </motion.div>
              ) : (
                <span style={{ 
                  fontWeight: 700, 
                  fontSize: '15px',
                  color: isCurrent ? colors.text : '#94a3b8',
                }}>
                  {index + 1}
                </span>
              )}
              
              {/* Pulse animation for current step */}
              {isCurrent && (
                <motion.div
                  style={{
                    position: 'absolute',
                    inset: '-4px',
                    borderRadius: '18px',
                    border: `2px solid ${colors.text}`,
                    opacity: 0.5,
                  }}
                  animate={{ 
                    scale: [1, 1.2, 1],
                    opacity: [0.5, 0, 0.5],
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}
            </motion.button>

            {/* Step label */}
            <div style={{ marginLeft: '12px', marginRight: '24px' }}>
              <p style={{ 
                fontSize: '14px', 
                fontWeight: 600,
                color: isCurrent ? colors.text : isComplete ? '#334155' : '#94a3b8',
              }}>
                {step.label}
              </p>
              {step.description && (
                <p style={{ 
                  fontSize: '12px', 
                  color: isCurrent ? '#64748b' : '#94a3b8',
                  marginTop: '2px',
                }}>
                  {step.description}
                </p>
              )}
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div style={{ 
                width: '48px', 
                height: '4px', 
                marginRight: '8px',
                borderRadius: '2px',
                background: 'rgba(148, 163, 184, 0.2)',
                overflow: 'hidden',
              }}>
                <motion.div
                  style={{
                    height: '100%',
                    background: colors.gradient,
                    borderRadius: '2px',
                  }}
                  initial={{ width: '0%' }}
                  animate={{ width: isComplete ? '100%' : '0%' }}
                  transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
