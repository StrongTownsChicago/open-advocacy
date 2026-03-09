import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import authService from '../services/auth';
import { UserProfile, LoginCredentials, UserRegisterData } from '@/types/index';
import { useNavigate } from 'react-router-dom';

interface AuthContextType {
  isAuthenticated: boolean;
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  register: (userData: UserRegisterData) => Promise<UserProfile | null>;
  logout: () => void;
  clearError: () => void;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  checkPermission: (requiredRoles: string[] | null, mustBeAuthenticated?: boolean) => boolean;
  redirectToLogin: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  loading: true,
  error: null,
  login: async () => false,
  register: async () => null,
  logout: () => {},
  clearError: () => {},
  hasRole: () => false,
  hasAnyRole: () => false,
  checkPermission: () => false,
  redirectToLogin: () => {},
});

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      // Setup API interceptor to include token in requests
      authService.setupTokenInterceptor();

      // Check if user is already logged in
      if (authService.isAuthenticated()) {
        try {
          const userProfile = await authService.fetchUserProfile();
          if (userProfile) {
            setUser(userProfile);
            setIsAuthenticated(true);
          } else {
            // Token is invalid or expired
            authService.logout();
            setIsAuthenticated(false);
          }
        } catch (err) {
          console.error('Error initializing auth:', err);
          authService.logout();
          setIsAuthenticated(false);
        }
      }

      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const result = await authService.login(credentials);

      if (result.success) {
        const userProfile = authService.getCurrentUser();
        setUser(userProfile);
        setIsAuthenticated(true);
        return true;
      } else {
        console.error('Error in context, esle', result.error);
        // Set the error message from the service
        setError(result.error || 'Invalid credentials. Please try again.');
        return false;
      }
    } catch (err) {
      console.error('Error in context', err);
      setError('Login failed. Please try again later.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: UserRegisterData): Promise<UserProfile | null> => {
    setLoading(true);
    setError(null);

    try {
      const user = await authService.register(userData);
      return user;
    } catch (err: unknown) {
      const errorMessage =
        (err instanceof Error && 'response' in err && (err as { response?: { data?: { detail?: string } } }).response?.data?.detail) || 'Registration failed. Please try again later.';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setIsAuthenticated(false);
    navigate('/');
  };

  // Clear any auth errors
  const clearError = () => {
    setError(null);
  };

  const hasRole = (role: string): boolean => {
    return !!user && user.role === role;
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return !!user && roles.includes(user.role);
  };

  // Comprehensive permission check with customizable rules
  const checkPermission = (
    requiredRoles: string[] | null,
    mustBeAuthenticated: boolean = true
  ): boolean => {
    // If no special permissions required and authentication not required
    if (!requiredRoles && !mustBeAuthenticated) {
      return true;
    }

    // If authentication is required but user isn't logged in
    if (mustBeAuthenticated && !isAuthenticated) {
      return false;
    }

    // If no specific roles required but user is authenticated
    if (!requiredRoles && isAuthenticated) {
      return true;
    }

    // Check if user has any of the required roles
    return requiredRoles ? hasAnyRole(requiredRoles) : false;
  };

  // Helper to redirect to login with return path
  const redirectToLogin = () => {
    navigate('/login', { state: { from: window.location.pathname } });
  };

  const value = {
    isAuthenticated,
    user,
    loading,
    error,
    login,
    register,
    logout,
    clearError,
    hasRole,
    hasAnyRole,
    checkPermission,
    redirectToLogin,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
