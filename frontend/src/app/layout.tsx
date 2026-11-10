import type { Metadata, Viewport } from "next";

import "@fontsource-variable/ibm-plex-sans";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "./globals.css";

import { SiteHeader } from "@/components/site-header";
import { themeScript } from "@/components/theme-toggle";

export const metadata: Metadata = {
  title: { default: "AI Text Secury", template: "%s · AI Text Secury" },
  description: "Segurança de documentos antes da IA: texto oculto, prompt injection e dados sensíveis.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f9fafb" },
    { media: "(prefers-color-scheme: dark)", color: "#12161d" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="flex min-h-dvh flex-col">
        <SiteHeader />
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:py-12">{children}</main>
        <footer className="border-t">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-5 text-xs text-muted-foreground">
            <span>AI Text Secury · segurança documental para IA</span>
            <span>Score 0–100 · Seguro, Atenção, Alto risco, Crítico</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
