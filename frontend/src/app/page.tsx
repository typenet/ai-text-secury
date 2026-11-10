"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { EyeOff, KeyRound, Loader2, ScanSearch, ShieldAlert, UserLock } from "lucide-react";

import { Dropzone } from "@/components/dropzone";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createScan, getApiKey, setApiKey } from "@/lib/api";

const CHECKS = [
  { icon: EyeOff, title: "Texto oculto", text: "Texto branco, minúsculo, fora da página, sob imagens ou em camadas escondidas." },
  { icon: ShieldAlert, title: "Prompt injection", text: "Instruções escondidas para manipular assistentes e pipelines RAG." },
  { icon: UserLock, title: "Dados sensíveis", text: "CPF, CNPJ, cartões e outros dados pessoais cobertos pela LGPD." },
];

export default function HomePage() {
  const router = useRouter();
  const [apiKey, setKey] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setKey(getApiKey()), []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setApiKey(apiKey);
      const scan = await createScan(file);
      router.push(`/scans/${scan.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no envio");
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-10 lg:grid-cols-[1fr_22rem] lg:gap-12">
      <section className="grid content-start gap-6">
        <div className="grid gap-3">
          <p className="text-sm font-medium text-brand">Análise antes da IA</p>
          <h1 className="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
            Descubra o que o documento esconde antes que a IA leia.
          </h1>
          <p className="max-w-prose text-muted-foreground text-pretty">
            Envie um PDF, DOCX ou TXT. Você recebe um score de risco de 0 a 100 e a lista de achados com página e trecho.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Novo scan</CardTitle>
            <CardDescription>O resultado fica pronto em poucos segundos.</CardDescription>
          </CardHeader>
          <form onSubmit={onSubmit} className="contents">
            <CardContent className="grid gap-5">
              <Dropzone file={file} onFile={setFile} disabled={busy} />
              <div className="grid gap-2">
                <Label htmlFor="api-key">
                  <KeyRound className="size-3.5 text-muted-foreground" aria-hidden />
                  API key
                </Label>
                <Input
                  id="api-key"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setKey(e.target.value)}
                  placeholder="ats_..."
                  autoComplete="off"
                  required
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground">Fica salva só neste navegador.</p>
              </div>
              {error && (
                <Alert variant="destructive">
                  <ShieldAlert />
                  <AlertTitle>Não foi possível enviar</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
            <CardFooter>
              <Button type="submit" size="lg" disabled={busy || !file} className="w-full sm:w-auto">
                {busy ? <Loader2 className="animate-spin" /> : <ScanSearch />}
                {busy ? "Enviando..." : "Analisar documento"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </section>

      <aside className="grid content-start gap-4 lg:pt-28">
        <h2 className="text-sm font-medium text-muted-foreground">O que verificamos</h2>
        <ul className="grid gap-3">
          {CHECKS.map(({ icon: Icon, title, text }) => (
            <li key={title} className="flex gap-3 rounded-lg border bg-card p-4 shadow-card">
              <span className="grid size-9 shrink-0 place-items-center rounded-md bg-brand-soft text-brand">
                <Icon className="size-4" aria-hidden />
              </span>
              <div className="grid gap-0.5">
                <p className="text-sm font-medium">{title}</p>
                <p className="text-sm text-muted-foreground">{text}</p>
              </div>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
