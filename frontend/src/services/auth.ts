import api from './api';
import { LoginCredentials, AuthResponse, UserRegisterData, UserProfile } from '../types/index';

const TOKEN_KEY = 'open_advocacy_auth_token';
const USER_KEY = 'open_advocacy_user';

const authService = {
  async login(credentials: LoginCredentials): Promise<{ success: boolean; error?: string }> {
    try {
      // Convert to form data as required by FastAPI's OAuth2PasswordRequestForm
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await api.post<AuthResponse>('/auth/token', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data?.access_token) {
        localStorage.setItem(TOKEN_KEY, response.data.access_token);
        await this.fetchUserProfile();
        return { success: true };
      }
      return { success: false, error: 'Invalid login response' };
    } catch (error: unknown) {
      console.error('Login error:', error);
      // Return the error message from the server if available
      const errorMessage =
        (error instanceof Error && 'response' in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined) || 'Invalid email or password';

      return {
        success: false,
        error: errorMessage,
      };
    }
  },

  // Register function (requires admin privileges)
  async register(userData: UserRegisterData): Promise<UserProfile | null> {
    try {
      const response = await api.post<UserProfile>('/auth/register', userData);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      return null;
    }
  },

  async fetchUserProfile(): Promise<UserProfile | null> {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) return null;

      const response = await api.get<UserProfile>('/auth/me');
      localStorage.setItem(USER_KEY, JSON.stringify(response.data));
      return response.data;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      return null;
    }
  },

  // Check if user is logged in
  isAuthenticated(): boolean {
    return !!localStorage.getItem(TOKEN_KEY);
  },

  // Get the current user from localStorage
  getCurrentUser(): UserProfile | null {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  hasRole(role: string): boolean {
    const user = this.getCurrentUser();
    return user?.role === role;
  },

  setupTokenInterceptor(): void {
    api.interceptors.request.use(
      config => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      error => Promise.reject(error)
    );
  },
};

export default authService;
