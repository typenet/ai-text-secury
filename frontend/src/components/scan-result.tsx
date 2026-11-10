"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowLeft, FileText, ScanSearch } from "lucide-react";

import { BAND_BG, BANDS, SEVERITY_BAND, SEVERITY_LABEL, SEVERITY_ORDER, RiskBadge, SeverityBadge } from "@/components/risk";
import { formatBytes } from "@/components/dropzone";
import { ScoreGauge } from "@/components/score-gauge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Finding, Scan, Severity } from "@/lib/api";
import { ruleInfo } from "@/lib/rules";
import { cn } from "@/lib/utils";

export function ScanResult({ scan }: { scan: Scan }) {
  const [filter, setFilter] = useState<Severity | null>(null);
  const score = scan.score ?? 0;
  const band = scan.band ?? "safe";
  const info = BANDS[band];

  const counts = useMemo(() => {
    const c: Record<Severity, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    for (const f of scan.findings) c[f.severity]++;
    return c;
  }, [scan.findings]);

  const findings = useMemo(
    () =>
      scan.findings
        .filter((f) => !filter || f.severity === filter)
        .sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity) || b.confidence - a.confidence),
    [scan.findings, filter],
  );

  return (
    <div className="grid gap-6">
      <BackLink />

      <div className="flex flex-wrap items-start gap-4">
        <span className="grid size-11 shrink-0 place-items-center rounded-lg border bg-card text-muted-foreground shadow-card">
          <FileText className="size-5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-semibold tracking-tight break-all">{scan.document.filename}</h1>
          <p className="mt-1 flex flex-wrap gap-x-2 text-sm text-muted-foreground">
            <span>{scan.document.doc_type.toUpperCase()}</span>
            <span aria-hidden>·</span>
            <span>{scan.document.page_count ?? "?"} página(s)</span>
            <span aria-hidden>·</span>
            <span>{formatBytes(scan.document.size_bytes)}</span>
            {scan.finished_at && (
              <>
                <span aria-hidden>·</span>
                <span>analisado em {new Date(scan.finished_at).toLocaleString("pt-BR")}</span>
              </>
            )}
          </p>
        </div>
      </div>

      <Card className="overflow-hidden py-0">
        <div className="grid sm:grid-cols-[auto_1fr]">
          <div className="grid place-items-center border-b p-6 sm:border-r sm:border-b-0 sm:px-10">
            <ScoreGauge score={score} />
          </div>
          <div className="grid content-center gap-4 p-5 sm:p-6">
            <div className="grid gap-2">
              <RiskBadge band={band} className="w-fit" />
              <p className="text-xl font-semibold tracking-tight">{info.verdict}</p>
              <p className="text-muted-foreground">{info.action}</p>
            </div>
            <BandScale score={score} />
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4" role="group" aria-label="Filtrar por severidade">
        {SEVERITY_ORDER.map((sev) => {
          const active = filter === sev;
          return (
            <button
              key={sev}
              type="button"
              aria-pressed={active}
              disabled={counts[sev] === 0}
              onClick={() => setFilter(active ? null : sev)}
              className={cn(
                "grid gap-1 rounded-lg border bg-card p-4 text-left shadow-card transition-colors outline-none",
                "hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-default disabled:opacity-60 disabled:hover:bg-card",
                active && "border-ring ring-1 ring-ring",
              )}
            >
              <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <span aria-hidden className={cn("size-2 rounded-full", BAND_BG[SEVERITY_BAND[sev]])} />
                {SEVERITY_LABEL[sev]}
              </span>
              <span className="text-2xl font-semibold tabular-nums">{counts[sev]}</span>
            </button>
          );
        })}
      </div>

      <Card>
        <CardHeader className="flex flex-wrap items-center justify-between gap-2">
          <div className="grid gap-1">
            <CardTitle>Achados</CardTitle>
            <CardDescription>Do mais grave ao mais leve, com a regra, a página e o trecho encontrado.</CardDescription>
          </div>
          {filter && (
            <Button variant="ghost" size="sm" onClick={() => setFilter(null)}>
              Mostrar todos ({scan.findings.length})
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {scan.findings.length === 0 ? (
            <Alert variant="safe">
              <ScanSearch />
              <AlertTitle>Nenhum risco encontrado</AlertTitle>
              <AlertDescription>O motor {scan.engine_version} não identificou técnicas de ocultação nem injeção.</AlertDescription>
            </Alert>
          ) : (
            <ul className="divide-y rounded-lg border">
              {findings.map((f, i) => (
                <FindingRow key={i} finding={f} />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        Motor {scan.engine_version} · scan <code className="font-mono">{scan.id}</code>
      </p>
    </div>
  );
}

function FindingRow({ finding: f }: { finding: Finding }) {
  const rule = ruleInfo(f.rule);
  const band = SEVERITY_BAND[f.severity];
  return (
    <li className="relative grid gap-2 p-4 pl-5">
      <span aria-hidden className={cn("absolute inset-y-3 left-0 w-1 rounded-r-full", BAND_BG[band])} />
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <SeverityBadge severity={f.severity} />
        <span className="font-medium">{rule.label}</span>
        <code className="font-mono text-xs text-muted-foreground">{f.rule}</code>
        <span className="flex w-full items-center gap-3 text-xs text-muted-foreground sm:ml-auto sm:w-auto">
          {f.page != null && <span>página {f.page}</span>}
          <span className="flex items-center gap-1.5" title={`Confiança ${f.confidence}%`}>
            confiança
            <span className="h-1.5 w-12 overflow-hidden rounded-full bg-muted">
              <span className={cn("block h-full", BAND_BG[band])} style={{ width: `${f.confidence}%` }} />
            </span>
            <span className="tabular-nums">{f.confidence}%</span>
          </span>
        </span>
      </div>
      {rule.description && <p className="text-sm text-muted-foreground">{rule.description}</p>}
      {f.text && (
        <blockquote className="max-h-40 overflow-auto rounded-md border bg-muted/60 px-3 py-2 font-mono text-[13px] leading-relaxed break-words whitespace-pre-wrap">
          {f.text}
        </blockquote>
      )}
    </li>
  );
}

/** Régua com as 4 faixas e um marcador na posição do score. */
function BandScale({ score }: { score: number }) {
  const segs = [
    { band: "safe", w: 21 },
    { band: "attention", w: 30 },
    { band: "high", w: 30 },
    { band: "critical", w: 19 },
  ] as const;
  return (
    <div className="grid gap-1.5" aria-hidden>
      <div className="relative flex h-2 gap-0.5">
        {segs.map((s) => (
          <span key={s.band} className={cn("h-full rounded-full opacity-80", BAND_BG[s.band])} style={{ width: `${s.w}%` }} />
        ))}
        <span
          className="absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-card bg-foreground shadow"
          style={{ left: `${Math.max(0, Math.min(100, score))}%` }}
        />
      </div>
      <div className="flex text-[11px] text-muted-foreground">
        {segs.map((s) => (
          <span key={s.band} style={{ width: `${s.w}%` }}>
            {BANDS[s.band].label}
          </span>
        ))}
      </div>
    </div>
  );
}

export function BackLink() {
  return (
    <Link href="/" className="inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
      <ArrowLeft className="size-4" aria-hidden /> Novo scan
    </Link>
  );
}
