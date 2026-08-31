"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

type CategoryState = {
  category: string | null;
  setCategory: (value: string) => void;
  clear: () => void;
};

const CategoryContext = createContext<CategoryState | null>(null);

const CATEGORY_COOKIE = "portfolio_category";
const ONE_YEAR_SECONDS = 365 * 24 * 60 * 60;
const FOR_PARAM = "for";

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp(`(?:^|;\\s*)${name}=([^;]*)`),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

function writeCookie(name: string, value: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${ONE_YEAR_SECONDS}; path=/; SameSite=Lax`;
}

function clearCookie(name: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; max-age=0; path=/; SameSite=Lax`;
}

// `category === null` means the `default` audience (conventions.md #1 crawler SSR).
// It is never offered as a user choice after D2; IntroOverlay/HUD only expose the
// 5 concrete audiences. `clear()` resets to `default` for programmatic /
// crawler cases but is no longer wired to any button.
export function CategoryProvider({ children }: { children: ReactNode }) {
  const [category, setCategoryState] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const forParam = params.get(FOR_PARAM);

    if (forParam) {
      writeCookie(CATEGORY_COOKIE, forParam);
      setCategoryState(forParam);

      const url = new URL(window.location.href);
      url.searchParams.delete(FOR_PARAM);
      window.history.replaceState({}, "", url.toString());
    } else {
      setCategoryState(readCookie(CATEGORY_COOKIE));
    }
  }, []);

  const setCategory = useCallback((value: string) => {
    writeCookie(CATEGORY_COOKIE, value);
    setCategoryState(value);
  }, []);

  const clear = useCallback(() => {
    clearCookie(CATEGORY_COOKIE);
    setCategoryState(null);
  }, []);

  return (
    <CategoryContext.Provider value={{ category, setCategory, clear }}>
      {children}
    </CategoryContext.Provider>
  );
}

export function useCategory(): CategoryState {
  const ctx = useContext(CategoryContext);
  if (!ctx) {
    throw new Error("useCategory must be used within a CategoryProvider");
  }
  return ctx;
}
