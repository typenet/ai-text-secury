"use client";

import { use, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { RiskBadge, SeverityBadge } from "@/components/risk";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getScan, type Scan } from "@/lib/api";

const POLL_MS = 1500;

export default function ScanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [scan, setScan] = useState<Scan | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let cancelled = false;
    async function load() {
      try {
        const s = await getScan(id);
        if (cancelled) return;
        setScan(s);
        if (s.status === "queued" || s.status === "running") timer = setTimeout(load, POLL_MS);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Erro ao carregar");
      }
    }
    load();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [id]);

  if (error) return <p className="text-destructive">{error}</p>;
  if (!scan || scan.status === "queued" || scan.status === "running") {
    return (
      <p className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="size-4 animate-spin" /> Analisando documento...
      </p>
    );
  }
  if (scan.status === "failed") return <p className="text-destructive">Falha na análise: {scan.error}</p>;

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight break-all">{scan.document.filename}</h1>
          <p className="text-muted-foreground">
            {scan.document.doc_type.toUpperCase()} · {scan.document.page_count ?? "?"} página(s) · engine{" "}
            {scan.engine_version}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-4xl font-bold tabular-nums">{scan.score}</span>
          {scan.band && <RiskBadge band={scan.band} />}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Achados ({scan.findings.length})</CardTitle>
          <CardDescription>Ordenados por severidade. Cada achado indica a regra, a página e o trecho.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {scan.findings.length === 0 && <p className="text-muted-foreground">Nenhum risco encontrado.</p>}
          {scan.findings.map((f, i) => (
            <div key={i} className="grid gap-1 rounded-lg border p-3">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <SeverityBadge severity={f.severity} />
                <code className="font-mono">{f.rule}</code>
                {f.page != null && <span className="text-muted-foreground">página {f.page}</span>}
                <span className="ml-auto text-muted-foreground">confiança {f.confidence}%</span>
              </div>
              {f.text && <p className="text-sm break-words whitespace-pre-wrap">{f.text}</p>}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
