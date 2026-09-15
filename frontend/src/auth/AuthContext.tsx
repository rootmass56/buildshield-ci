import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getSession,
  login as loginRequest,
  logout as logoutRequest,
} from "../api/client";

interface AuthState {
  ready: boolean;
  authenticated: boolean;
  username: string | null;
  csrfToken: string | null;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const initialState: AuthState = {
  ready: false,
  authenticated: false,
  username: null,
  csrfToken: null,
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(initialState);

  const refresh = useCallback(async () => {
    const session = await getSession();

    setState({
      ready: true,
      authenticated: session.authenticated,
      username: session.authenticated ? session.username ?? null : null,
      csrfToken: session.authenticated ? session.csrf_token ?? null : null,
    });
  }, []);

  useEffect(() => {
    void refresh().catch(() => {
      setState({
        ready: true,
        authenticated: false,
        username: null,
        csrfToken: null,
      });
    });
  }, [refresh]);

  const login = useCallback(
    async (username: string, password: string) => {
      const session = await loginRequest(username, password);

      setState({
        ready: true,
        authenticated: true,
        username: session.username,
        csrfToken: session.csrf_token,
      });
    },
    [],
  );

  const logout = useCallback(async () => {
    if (state.csrfToken) {
      await logoutRequest(state.csrfToken);
    }

    setState({
      ready: true,
      authenticated: false,
      username: null,
      csrfToken: null,
    });
  }, [state.csrfToken]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      logout,
      refresh,
    }),
    [state, login, logout, refresh],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === null) {
    throw new Error("useAuth must be used within AuthProvider.");
  }

  return context;
}
