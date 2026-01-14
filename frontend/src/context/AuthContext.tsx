import { createContext, useContext, useState, type ReactNode } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (username: string, password: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Credentials - in production, these would be environment variables or backend-validated
const VALID_USERNAME = 'shabrowski';
const VALID_PASSWORD = 'PhilosophizeMe2922';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    // Check localStorage for existing session
    const stored = localStorage.getItem('philobot_auth');
    if (stored) {
      try {
        const { expiry } = JSON.parse(stored);
        // Session expires after 7 days
        if (expiry && new Date(expiry) > new Date()) {
          return true;
        }
        localStorage.removeItem('philobot_auth');
      } catch {
        localStorage.removeItem('philobot_auth');
      }
    }
    return false;
  });

  const login = (username: string, password: string): boolean => {
    if (username === VALID_USERNAME && password === VALID_PASSWORD) {
      const expiry = new Date();
      expiry.setDate(expiry.getDate() + 7); // 7 days from now
      localStorage.setItem('philobot_auth', JSON.stringify({ 
        authenticated: true, 
        expiry: expiry.toISOString() 
      }));
      setIsAuthenticated(true);
      return true;
    }
    return false;
  };

  const logout = () => {
    localStorage.removeItem('philobot_auth');
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
