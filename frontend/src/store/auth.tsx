// Auth context: holds the currently logged-in user, the active
// establishment, and exposes login/logout/switchEstablishment helpers.
//
// Tokens themselves live in the API client (localStorage). This context
// hydrates on mount: if there's a saved token, it fetches /users/me and
// the user's memberships to decide which establishment is active.

import * as React from "react";
import * as authApi from "@/api/auth";
import * as usersApi from "@/api/users";
import * as estApi from "@/api/establishments";
import { getAuth, subscribeAuth } from "@/api/client";
import type { EstablishmentRead, MembershipRead, UserRead } from "@/api/types";

const ACTIVE_EST_KEY = "agenda.active_establishment";

interface AuthState {
  status: "loading" | "anonymous" | "authenticated";
  user: UserRead | null;
  memberships: MembershipRead[];
  establishments: EstablishmentRead[];
  activeEstablishment: EstablishmentRead | null;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  switchEstablishment: (id: string) => void;
  refreshEstablishment: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = React.useState<AuthState>({
    status: "loading",
    user: null,
    memberships: [],
    establishments: [],
    activeEstablishment: null,
  });

  const hydrate = React.useCallback(async () => {
    if (!getAuth()) {
      setState({ status: "anonymous", user: null, memberships: [], establishments: [], activeEstablishment: null });
      return;
    }
    try {
      const user = await usersApi.me();
      let memberships: MembershipRead[] = [];
      let establishments: EstablishmentRead[] = [];
      try {
        memberships = await usersApi.listUserMemberships(user.id);
      } catch { memberships = []; }

      if (memberships.length > 0) {
        const results = await Promise.allSettled(
          memberships.map((m) => estApi.getEstablishment(m.establishment_id)),
        );
        establishments = results
          .filter((r): r is PromiseFulfilledResult<EstablishmentRead> => r.status === "fulfilled")
          .map((r) => r.value);
      } else if (user.is_global_admin) {
        try {
          const page = await estApi.listEstablishments({ size: 50 });
          establishments = page.data;
        } catch { /* ignore */ }
      }

      const savedId = localStorage.getItem(ACTIVE_EST_KEY);
      const active =
        establishments.find((e) => e.id === savedId) ?? establishments[0] ?? null;
      if (active) localStorage.setItem(ACTIVE_EST_KEY, active.id);

      setState({ status: "authenticated", user, memberships, establishments, activeEstablishment: active });
    } catch {
      setState({ status: "anonymous", user: null, memberships: [], establishments: [], activeEstablishment: null });
    }
  }, []);

  React.useEffect(() => {
    hydrate();
    const unsub = subscribeAuth((a) => { if (!a) hydrate(); });
    return () => { unsub(); };
  }, [hydrate]);

  const value: AuthContextValue = {
    ...state,
    login: async (username, password) => {
      await authApi.login({ username, password });
      await hydrate();
    },
    logout: () => {
      authApi.logout();
      localStorage.removeItem(ACTIVE_EST_KEY);
      setState({ status: "anonymous", user: null, memberships: [], establishments: [], activeEstablishment: null });
    },
    switchEstablishment: (id) => {
      setState((s) => {
        const active = s.establishments.find((e) => e.id === id) ?? s.activeEstablishment;
        if (active) localStorage.setItem(ACTIVE_EST_KEY, active.id);
        return { ...s, activeEstablishment: active };
      });
    },
    refreshEstablishment: hydrate,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

/** Convenience: throws if no establishment is active. Use inside screens
 *  that are only rendered after the auth gate. */
export function useEstablishmentId(): string {
  const { activeEstablishment } = useAuth();
  if (!activeEstablishment) throw new Error("No active establishment");
  return activeEstablishment.id;
}
