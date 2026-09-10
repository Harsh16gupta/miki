import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { AuthContext, type AuthStatus } from "./AuthContext";
import { apiFetch, apiPostJson, ApiError, getStoredToken } from "../lib/api";
import type { AuthUser, RegisterResponse, TokenResponse } from "../types/api";

const TOKEN_KEY = "miki_token";

function storeToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // private-mode storage failures keep the session guest-only
  }
}

/** T39: user state, token persistence, auto-login via GET /auth/me. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  // No persisted token → guest immediately (no effect round-trip).
  const [status, setStatus] = useState<AuthStatus>(() =>
    getStoredToken() ? "loading" : "guest",
  );
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    // Auto-login on refresh when a token was persisted.
    // (No-token case is already "guest" via the state initializer.)
    if (!getStoredToken()) return;
    apiFetch<AuthUser>("/auth/me")
      .then((u) => {
        if (mounted.current) {
          setUser(u);
          setStatus("authed");
        }
      })
      .catch(() => {
        storeToken(null);
        if (mounted.current) setStatus("guest");
      });
    return () => {
      mounted.current = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const body = await apiPostJson<TokenResponse>("/auth/login", {
      email,
      password,
    });
    storeToken(body.access_token);
    try {
      const u = await apiFetch<AuthUser>("/auth/me");
      setUser(u);
      setStatus("authed");
    } catch (e) {
      storeToken(null);
      setStatus("guest");
      throw e instanceof ApiError ? new Error(e.detail) : e;
    }
  }, []);

  const register = useCallback(
    async (fullName: string, email: string, password: string) => {
      const body = await apiPostJson<RegisterResponse>("/auth/register", {
        email,
        password,
        full_name: fullName,
      });
      storeToken(body.access_token);
      const { access_token: _discard, token_type: _tt, ...profile } = body;
      setUser(profile);
      setStatus("authed");
    },
    [],
  );

  const logout = useCallback(() => {
    storeToken(null);
    setUser(null);
    setStatus("guest");
  }, []);

  return (
    <AuthContext.Provider value={{ user, status, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
