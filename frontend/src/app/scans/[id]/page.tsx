"use client";

import { use, useEffect, useState } from "react";
import { Loader2, OctagonAlert } from "lucide-react";

import { BackLink, ScanResult } from "@/components/scan-result";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
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

  if (error) return <ScanError title="Não foi possível carregar o scan" message={error} />;
  if (!scan || scan.status === "queued" || scan.status === "running") return <ScanLoading scan={scan} />;
  if (scan.status === "failed") return <ScanError title="Falha na análise" message={scan.error ?? "Erro desconhecido"} />;
  return <ScanResult scan={scan} />;
}

function ScanLoading({ scan }: { scan: Scan | null }) {
  const running = scan?.status === "running";
  return (
    <div className="grid gap-6" aria-busy="true">
      <BackLink />
      <div className="grid gap-2">
        <Skeleton className="h-7 w-2/3 max-w-md" />
        <Skeleton className="h-4 w-1/2 max-w-xs" />
      </div>
      <Card className="py-0">
        <div className="grid sm:grid-cols-[auto_1fr]">
          <div className="grid place-items-center border-b p-6 sm:border-r sm:border-b-0 sm:px-10">
            <div className="grid size-[168px] place-items-center rounded-full border-8 border-muted">
              <Loader2 className="size-6 animate-spin text-brand" aria-hidden />
            </div>
          </div>
          <div className="grid content-center gap-3 p-6">
            <Badge variant="brand" className="w-fit">
              {running ? "Analisando" : "Na fila"}
            </Badge>
            <p className="text-xl font-semibold tracking-tight">
              {scan?.document.filename ? `Analisando ${scan.document.filename}` : "Analisando documento..."}
            </p>
            <p className="text-muted-foreground">
              Verificando texto oculto, caracteres invisíveis, instruções para IA e dados sensíveis.
            </p>
          </div>
        </div>
      </Card>
      <div className="grid gap-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    </div>
  );
}

function ScanError({ title, message }: { title: string; message: string }) {
  return (
    <div className="grid max-w-xl gap-6">
      <BackLink />
      <Alert variant="destructive">
        <OctagonAlert />
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>{message}</AlertDescription>
      </Alert>
    </div>
  );
}
