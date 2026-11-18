import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, post, token } from "./api";
import type { User } from "./types";

interface Session {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}
const Context = createContext<Session>(null!);
export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  async function refresh() {
    if (token()) setUser(await api<User>("/auth/me"));
  }
  useEffect(() => {
    refresh()
      .catch(() => sessionStorage.removeItem("tfpmds-token"))
      .finally(() => setLoading(false));
  }, []);
  async function login(email: string, password: string) {
    const data = await post<{ access_token: string; user: User }>(
      "/auth/login",
      { email, password },
    );
    sessionStorage.setItem("tfpmds-token", data.access_token);
    setUser(data.user);
  }
  async function logout() {
    try {
      await post("/auth/logout");
    } finally {
      sessionStorage.removeItem("tfpmds-token");
      setUser(null);
    }
  }
  return (
    <Context.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </Context.Provider>
  );
}
export const useSession = () => useContext(Context);
