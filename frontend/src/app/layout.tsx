import type { Metadata } from "next";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Text Secury",
  description: "Segurança de documentos antes da IA: texto oculto, prompt injection e dados sensíveis.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-dvh">
        <header className="border-b">
          <div className="mx-auto flex h-14 max-w-5xl items-center gap-2 px-4">
            <ShieldCheck className="size-5 text-primary" />
            <Link href="/" className="font-semibold">
              AI Text Secury
            </Link>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
