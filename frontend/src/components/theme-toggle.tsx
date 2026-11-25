"use client";

import { useEffect, useState } from "react";
import { Monitor, Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";

type Theme = "system" | "light" | "dark";
const KEY = "ats_theme";
const NEXT: Record<Theme, Theme> = { system: "light", light: "dark", dark: "system" };
const LABEL: Record<Theme, string> = { system: "Tema do sistema", light: "Tema claro", dark: "Tema escuro" };

/** Script inline no <head>: aplica o tema salvo antes da pintura (evita "piscar"). */
export const themeScript = `try{var t=localStorage.getItem("${KEY}");if(t==="light"||t==="dark")document.documentElement.classList.add(t)}catch(e){}`;

function apply(theme: Theme) {
  const el = document.documentElement;
  el.classList.remove("light", "dark");
  if (theme !== "system") el.classList.add(theme);
  try {
    if (theme === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, theme);
  } catch {
    /* modo privado */
  }
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    const el = document.documentElement;
    setTheme(el.classList.contains("dark") ? "dark" : el.classList.contains("light") ? "light" : "system");
  }, []);

  const Icon = theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;
  return (
    <Button
      variant="ghost"
      size="icon"
      title={`${LABEL[theme]} (clique para trocar)`}
      aria-label={`${LABEL[theme]}. Trocar tema`}
      onClick={() => {
        const next = NEXT[theme];
        apply(next);
        setTheme(next);
      }}
    >
      <Icon />
    </Button>
  );
}
