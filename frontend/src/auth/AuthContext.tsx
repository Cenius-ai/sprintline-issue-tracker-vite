import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { api, getToken, setToken, UNAUTHORIZED_EVENT } from '../api/client';
import type { LoginResponse, User } from '../api/types';

export type AuthStatus = 'restoring' | 'authenticated' | 'anonymous';

interface AuthValue {
  user: User | null;
  status: AuthStatus;
  sessionExpired: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>('restoring');
  const [sessionExpired, setSessionExpired] = useState(false);

  // Restore the session from the token before any route guard decides.
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setStatus('anonymous');
      return;
    }
    let cancelled = false;
    api
      .get<User>('/api/auth/me', { suppressAuthEvent: true })
      .then((profile) => {
        if (cancelled) return;
        setUser(profile);
        setStatus('authenticated');
      })
      .catch(() => {
        if (cancelled) return;
        setToken(null);
        setUser(null);
        setStatus('anonymous');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Any 401 from the API drops the session and returns to the login screen.
  useEffect(() => {
    const onUnauthorized = () => {
      setUser(null);
      setStatus('anonymous');
      setSessionExpired(true);
    };
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await api.post<LoginResponse>(
      '/api/auth/login',
      { email, password },
      { auth: false },
    );
    setToken(response.token);
    setUser(response.user);
    setStatus('authenticated');
    setSessionExpired(false);
    return response.user;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setStatus('anonymous');
    setSessionExpired(false);
  }, []);

  const value = useMemo<AuthValue>(
    () => ({ user, status, sessionExpired, login, logout }),
    [user, status, sessionExpired, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return context;
}
