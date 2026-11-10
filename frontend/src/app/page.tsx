"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createScan, getApiKey, setApiKey } from "@/lib/api";

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
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Analisar documento</h1>
        <p className="text-muted-foreground">
          Detecta texto oculto, prompt injection e dados sensíveis antes de o documento chegar à IA.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Novo scan</CardTitle>
          <CardDescription>PDF, DOCX ou TXT, até 50 MB.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="grid gap-4">
            <label className="grid gap-1.5 text-sm">
              API key
              <Input
                type="password"
                value={apiKey}
                onChange={(e) => setKey(e.target.value)}
                placeholder="ats_..."
                autoComplete="off"
                required
              />
            </label>
            <label className="grid gap-1.5 text-sm">
              Arquivo
              <Input
                type="file"
                accept=".pdf,.docx,.txt,application/pdf,text/plain"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                required
              />
            </label>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={busy || !file} className="w-fit">
              {busy ? <Loader2 className="animate-spin" /> : <Upload />}
              Enviar para análise
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
