"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

interface User {
  id: string;
  email: string;
  name?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (userData: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Check for stored user session
    const storedUser = localStorage.getItem("dum_social_user");
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
      } catch (error) {
        console.error("Failed to parse stored user data:", error);
        localStorage.removeItem("dum_social_user");
      }
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    // Redirect logic
    const isAuthPage = pathname?.startsWith("/auth");
    
    if (!isLoading) {
      if (!user && !isAuthPage) {
        // User not authenticated and not on auth page, redirect to login
        router.push("/auth/login");
      } else if (user && isAuthPage) {
        // User authenticated but on auth page, redirect to dashboard
        router.push("/");
      }
    }
  }, [user, isLoading, pathname, router]);

  const login = (userData: User) => {
    setUser(userData);
    localStorage.setItem("dum_social_user", JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("dum_social_user");
    router.push("/auth/login");
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
